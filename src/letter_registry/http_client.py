"""Small urllib transport helpers for the public Tailscale Funnel endpoint."""

from __future__ import annotations

import http.client
import socket
import time
from urllib import parse, request


class _IPv4HTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection that prefers IPv4 for Funnel hostnames.

    Vercel's serverless runtime can stall for a full connect timeout while
    attempting the Funnel AAAA route before falling back to IPv4. Resolve only
    A records for *.ts.net while retaining the original hostname for TLS SNI
    and certificate verification.
    """

    def connect(self) -> None:
        started = time.monotonic()
        print(f"[dlr-net] dns-start host={self.host} port={self.port}", flush=True)
        addresses = socket.getaddrinfo(
            self.host,
            self.port,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        print(
            f"[dlr-net] dns-done host={self.host} addresses={len(addresses)} "
            f"elapsed={time.monotonic() - started:.3f}s",
            flush=True,
        )
        last_error: OSError | None = None
        # A Funnel edge address can accept TCP but stall during TLS from
        # Vercel. Bound each address attempt so the next A record is tried
        # quickly instead of consuming the whole serverless request budget.
        per_address_timeout = min(float(self.timeout or 12), 4.0)
        for family, socktype, proto, _canonname, sockaddr in addresses:
            sock = socket.socket(family, socktype, proto)
            try:
                sock.settimeout(per_address_timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                connect_started = time.monotonic()
                print(f"[dlr-net] connect-start host={self.host} ip={sockaddr[0]}", flush=True)
                sock.connect(sockaddr)
                print(
                    f"[dlr-net] connect-done host={self.host} ip={sockaddr[0]} "
                    f"elapsed={time.monotonic() - connect_started:.3f}s",
                    flush=True,
                )
                if self._tunnel_host:
                    self.sock = sock
                    self._tunnel()
                    sock = self.sock
                server_hostname = self._tunnel_host or self.host
                tls_started = time.monotonic()
                self.sock = self._context.wrap_socket(
                    sock,
                    server_hostname=server_hostname,
                )
                print(
                    f"[dlr-net] tls-done host={self.host} "
                    f"elapsed={time.monotonic() - tls_started:.3f}s",
                    flush=True,
                )
                return
            except OSError as exc:
                print(f"[dlr-net] connect-error host={self.host} error={type(exc).__name__}:{exc}", flush=True)
                last_error = exc
                sock.close()
        if last_error is not None:
            raise last_error
        raise OSError(f"No IPv4 address available for {self.host}")


class _IPv4HTTPSHandler(request.HTTPSHandler):
    def https_open(self, req: request.Request):
        return self.do_open(
            _IPv4HTTPSConnection,
            req,
            context=self._context,
        )


def open_url(req: request.Request, *, timeout: float = 12) -> object:
    """Open a URL, using IPv4-only DNS for Tailscale Funnel HTTPS hosts."""
    hostname = parse.urlsplit(req.full_url).hostname or ""
    if req.full_url.startswith("https://") and hostname.endswith(".ts.net"):
        started = time.monotonic()
        parsed = parse.urlsplit(req.full_url)
        print(
            f"[dlr-net] request-start method={req.get_method()} "
            f"host={hostname} path={parsed.path} timeout={timeout}",
            flush=True,
        )
        opener = request.build_opener(_IPv4HTTPSHandler())
        try:
            response = opener.open(req, timeout=timeout)
            print(
                f"[dlr-net] response-start host={hostname} "
                f"status={response.status} elapsed={time.monotonic() - started:.3f}s",
                flush=True,
            )
            return response
        except Exception as exc:
            print(
                f"[dlr-net] request-error host={hostname} "
                f"error={type(exc).__name__}:{exc} elapsed={time.monotonic() - started:.3f}s",
                flush=True,
            )
            raise
    return request.urlopen(req, timeout=timeout)
