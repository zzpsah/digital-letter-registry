"""Durable WhatsApp receipts for terminal manual-recovery batches."""
from __future__ import annotations

import json
import fcntl
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Callable

TERMINAL = {"completed", "failed", "retired"}
RECOVERY_PREFIXES = ("manual-recovery:", "manual-reprocess:", "manual_reprocess:pdftotext-layout-fallback-")


def reconcile_recovery_notifications(
    transport,
    *,
    state_dir: Path,
    source_loader,
    sender: str = "/home/prashant/.hermes/hermes-agent/hermes",
    send: Callable[..., object] = subprocess.run,
) -> list[str]:
    """Send one WhatsApp summary per fully terminal recovery batch.

    A marker is written only after Hermes confirms delivery. If WhatsApp is
    unavailable, the next worker tick retries; the underlying job is never
    replayed just to resend a receipt.
    """
    rows = transport.select(
        "processing_jobs",
        columns="id,letter_id,status,reason,last_error",
    )
    batches: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        reason = str(row.get("reason") or "")
        if reason.startswith(RECOVERY_PREFIXES):
            batches[reason].append(row)

    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    sent: list[str] = []
    for reason, jobs in sorted(batches.items()):
        if not jobs or any(str(job.get("status") or "") not in TERMINAL for job in jobs):
            continue
        marker = state_dir / (reason.replace("/", "_").replace(":", "_") + ".json")
        if marker.exists():
            continue
        lock_path = marker.with_suffix(".lock")
        with lock_path.open("a", encoding="utf-8") as lock_handle:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if marker.exists():
                continue

            completed = sum(str(job.get("status")) == "completed" for job in jobs)
            failed = sum(str(job.get("status")) == "failed" for job in jobs)
            retired = sum(str(job.get("status")) == "retired" for job in jobs)
            lines = [
                "*eLetters document recovery report*",
                f"Batch: {reason}",
                f"Total: {len(jobs)} | Completed: {completed} | Failed: {failed} | Retired: {retired}",
                "",
            ]
            for job in jobs:
                try:
                    record = source_loader.load(str(job.get("letter_id") or ""))
                    name = record.original_filename if record else str(job.get("letter_id") or "Unknown document")
                except Exception:
                    name = str(job.get("letter_id") or "Unknown document")
                status = str(job.get("status") or "unknown").upper()
                lines.append(f"• {name}: {status}")
                if status == "FAILED" and job.get("last_error"):
                    lines.append(f"  Reason: {str(job['last_error'])[:180]}")
            lines.extend(["", "This report reflects the final database job statuses."])
            message = "\n".join(lines)

            fd, temp_name = tempfile.mkstemp(prefix="dlr-recovery-", suffix=".txt")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(message)
                os.chmod(temp_name, 0o600)
                result = send(
                    [sender, "send", "--to", "whatsapp", "--file", temp_name, "--quiet"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                if getattr(result, "returncode", 1) != 0:
                    error = str(getattr(result, "stderr", "") or "WhatsApp delivery failed")[:300]
                    print(f"recovery_notification_pending reason={reason} error={error}")
                    continue
            except Exception as exc:
                print(f"recovery_notification_pending reason={reason} error={str(exc)[:300]}")
                continue
            finally:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass

            tmp_marker = marker.with_suffix(".json.tmp")
            tmp_marker.write_text(json.dumps({"reason": reason, "jobs": len(jobs), "completed": completed, "failed": failed, "retired": retired}, ensure_ascii=False), encoding="utf-8")
            os.chmod(tmp_marker, 0o600)
            tmp_marker.replace(marker)
            sent.append(reason)
            print(f"recovery_notification_sent reason={reason} jobs={len(jobs)} completed={completed} failed={failed} retired={retired}")
    return sent
