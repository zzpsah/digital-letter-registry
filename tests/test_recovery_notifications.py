from pathlib import Path
from types import SimpleNamespace

from letter_registry.recovery_notifications import reconcile_recovery_notifications


class FakeTransport:
    def __init__(self, rows):
        self.rows = rows

    def select(self, table, *, columns="*", filters=None):
        assert table == "processing_jobs"
        return self.rows


class FakeLoader:
    def load(self, letter_id):
        return SimpleNamespace(original_filename=f"document-{letter_id}.pdf")


def test_sends_one_summary_only_after_entire_recovery_batch_is_terminal(tmp_path: Path):
    rows = [
        {"id": "1", "letter_id": "a", "status": "completed", "reason": "manual-recovery:test"},
        {"id": "2", "letter_id": "b", "status": "pending", "reason": "manual-recovery:test"},
    ]
    calls = []
    send = lambda args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace(returncode=0, stderr="")
    assert reconcile_recovery_notifications(FakeTransport(rows), state_dir=tmp_path, source_loader=FakeLoader(), send=send) == []
    assert calls == []

    rows[1]["status"] = "failed"
    assert reconcile_recovery_notifications(FakeTransport(rows), state_dir=tmp_path, source_loader=FakeLoader(), send=send) == ["manual-recovery:test"]
    assert len(calls) == 1
    assert (tmp_path / "manual-recovery_test.json").exists()

    # Repeated worker ticks must not send duplicate receipts.
    assert reconcile_recovery_notifications(FakeTransport(rows), state_dir=tmp_path, source_loader=FakeLoader(), send=send) == []
    assert len(calls) == 1


def test_failed_whatsapp_send_is_retried_on_next_worker_tick(tmp_path: Path):
    rows = [{"id": "1", "letter_id": "a", "status": "completed", "reason": "manual-reprocess:test"}]
    failed = lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="gateway offline")
    assert reconcile_recovery_notifications(FakeTransport(rows), state_dir=tmp_path, source_loader=FakeLoader(), send=failed) == []
    assert not list(tmp_path.glob("*.json"))

    successful = lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr="")
    assert reconcile_recovery_notifications(FakeTransport(rows), state_dir=tmp_path, source_loader=FakeLoader(), send=successful) == ["manual-reprocess:test"]
