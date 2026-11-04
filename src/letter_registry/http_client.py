"""Small urllib transport helpers for the public Tailscale Funnel endpoint."""

from __future__ import annotations

import http.client
import socket
from urllib import parse, request


class _IPv4HTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection that prefers IPv4 for Funnel hostnames.

    Vercel's serverless runtime can stall for a full connect timeout while
    attempting the Funnel AAAA route before falling back to IPv4. Resolve only
    A records for *.ts.net while retaining the original hostname for TLS SNI
    and certificate verification.
    """

    def connect(self) -> None:
        addresses = socket.getaddrinfo(
            self.host,
            self.port,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        last_error: OSError | None = None
        for family, socktype, proto, _canonname, sockaddr in addresses:
            sock = socket.socket(family, socktype, proto)
            try:
                sock.settimeout(self.timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sockaddr)
                if self._tunnel_host:
                    self.sock = sock
                    self._tunnel()
                    sock = self.sock
                server_hostname = self._tunnel_host or self.host
                self.sock = self._context.wrap_socket(
                    sock,
                    server_hostname=server_hostname,
                )
                return
            except OSError as exc:
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
        opener = request.build_opener(_IPv4HTTPSHandler())
        return opener.open(req, timeout=timeout)
    return request.urlopen(req, timeout=timeout)
