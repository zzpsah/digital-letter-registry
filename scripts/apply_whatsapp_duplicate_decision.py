#!/usr/bin/env python3
"""Apply an explicit WhatsApp duplicate-document decision."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

from letter_registry.fingerprints import sha256_file
from letter_registry.google_drive_writer import GoogleDrivePrivateWriter
from letter_registry.session import SupabaseUserSession
from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)

STATE_ROOT = Path("/home/prashant/.hermes/state/dlr-whatsapp-intake")
DONE_ROOT = STATE_ROOT / "done"
DECISION_ROOT = STATE_ROOT / "duplicate-decisions"
BRIDGE_SEND = "http://127.0.0.1:3000/send"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    root = DECISION_ROOT.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("decision state path is outside the allowed directory")
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid decision state")
    return data


def _save_state(path: Path, state: dict[str, object]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(path, 0o600)


def _source_path(state: dict[str, object]) -> Path:
    item_name = str(state.get("item_name") or "").strip()
    filename = str(state.get("filename") or "").strip()
    if not item_name or not filename:
        raise ValueError("duplicate state is missing source identity")
    path = (DONE_ROOT / item_name / filename).resolve()
    if not path.is_relative_to(DONE_ROOT.resolve()) or not path.is_file():
        raise FileNotFoundError("staged duplicate source is unavailable")
    return path


def _runtime():
    raw = SupabasePostgrestTransport.from_worker_environment()
    owner_id = SupabaseUserSession.from_environment(
        access_token=raw.access_token
    ).user_id()
    transport = ArchiveScopedSupabaseTransport(
        transport=raw,
        archive_id=os.environ["DLR_ARCHIVE_ID"],
    )
    return owner_id, transport


def _existing_letter(transport, letter_id: str) -> dict[str, object]:
    rows = transport.select(
        "letters",
        filters={"id": letter_id},
        columns=(
            "id,original_filename,original_sha256,smart_filename,title,"
            "reference_number,issue_date,storage_provider,storage_object_id,status"
        ),
    )
    if not rows:
        raise RuntimeError("existing archived document was not found")
    return rows[0]


def _save_whatsapp_source(
    transport,
    *,
    owner_id: str,
    letter_id: str,
    state: dict[str, object],
    decision: str,
) -> None:
    message_id = str(state.get("message_id") or "").strip()
    if not message_id:
        return
    transport.upsert(
        "letter_sources",
        {
            "owner_id": owner_id,
            "letter_id": letter_id,
            "source_channel": "whatsapp",
            "external_message_id": message_id,
            "source_label": str(state.get("source_label") or "EDU- Letters"),
            "received_at": _now(),
            "metadata": {
                "connector": "hermes-whatsapp",
                "reply_chat_id": str(state.get("chat_id") or "") or None,
                "query_text": str(state.get("query_text") or "") or None,
                "duplicate_decision": decision,
                "authoritative_source": decision == "supersede",
                "supersedes_previous_source": decision == "supersede",
            },
        },
        on_conflict="owner_id,source_channel,external_message_id",
    )


def _label(letter: dict[str, object], state: dict[str, object]) -> str:
    return str(
        letter.get("title")
        or state.get("existing_title")
        or letter.get("smart_filename")
        or letter.get("original_filename")
        or "Archived document"
    ).strip()


def _send(chat_id: str, lines: list[str]) -> None:
    if not chat_id:
        return
    payload = json.dumps({"chatId": chat_id, "message": "\n".join(lines)}).encode()
    req = request.Request(
        BRIDGE_SEND,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    if not body.get("success"):
        raise RuntimeError("WhatsApp decision confirmation failed")


def _common_lines(letter: dict[str, object], state: dict[str, object]) -> list[str]:
    lines = [f"📄 {_label(letter, state)}"]
    if letter.get("issue_date") or state.get("existing_date"):
        lines.append(f"📅 {letter.get('issue_date') or state.get('existing_date')}")
    if letter.get("reference_number") or state.get("existing_reference"):
        lines.append(
            f"🔖 Ref: {letter.get('reference_number') or state.get('existing_reference')}"
        )
    if state.get("existing_drive_url"):
        lines.append(f"🔗 {state.get('existing_drive_url')}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument(
        "--decision",
        required=True,
        choices=("overwrite", "cancel", "supersede"),
    )
    args = parser.parse_args()

    state_path = Path(args.state)
    state = _load_state(state_path)
    if str(state.get("status") or "") != "pending":
        print("status=already-resolved")
        print(f"decision_status={state.get('status') or ''}")
        return 0

    chat_id = str(state.get("chat_id") or "")
    letter_id = str(state.get("existing_letter_id") or "").strip()
    if not letter_id:
        raise RuntimeError("existing letter id missing from duplicate decision state")

    # Cancel is a true no-op. It must not require database/Drive access.
    if args.decision == "cancel":
        state["status"] = "cancelled"
        state["decision"] = "cancel"
        state["resolved_at"] = _now()
        _save_state(state_path, state)
        _send(
            chat_id,
            [
                "❌ Cancelled — archive me koi change nahi kiya gaya.",
                *_common_lines({}, state),
            ],
        )
        print("status=cancelled")
        return 0

    owner_id, transport = _runtime()
    letter = _existing_letter(transport, letter_id)
    source = _source_path(state)
    source_hash = sha256_file(source)
    existing_hash = str(letter.get("original_sha256") or "").lower()

    if source_hash != existing_hash:
        state["status"] = "stale-mismatch"
        state["resolved_at"] = _now()
        _save_state(state_path, state)
        _send(
            chat_id,
            [
                "⚠️ Duplicate decision apply nahi hua.",
                "File ki details badal gayi hain, isliye koi change nahi kiya gaya. File dobara bhejkar option choose karein.",
                *_common_lines(letter, state),
            ],
        )
        print("status=stale-mismatch")
        return 0

    if args.decision == "supersede":
        # Exact byte duplicates are the same document, not a newer revision.
        # A true supersede relationship is valid only when the incoming file
        # differs and represents a later/revised document.
        state["status"] = "supersede-rejected-identical"
        state["decision"] = "supersede"
        state["resolved_at"] = _now()
        _save_state(state_path, state)
        _send(
            chat_id,
            [
                "⚠️ Supersede apply nahi hua.",
                "Ye bilkul wahi file hai, isliye ise naya version nahi maana ja sakta.",
                "Agar revised ya badla hua document ho to Supersede choose karein.",
                *_common_lines(letter, state),
            ],
        )
        print("status=supersede-rejected-identical")
        return 0

    provider = str(letter.get("storage_provider") or "").lower()
    object_id = str(letter.get("storage_object_id") or "").strip()
    if "drive" not in provider or not object_id:
        raise RuntimeError("existing archived document is not backed by Google Drive")

    GoogleDrivePrivateWriter.from_environment().replace_file(
        object_reference=object_id,
        path=source,
    )
    transport.update(
        "letters",
        {"updated_at": _now()},
        filters={"id": letter_id},
    )
    _save_whatsapp_source(
        transport,
        owner_id=owner_id,
        letter_id=letter_id,
        state=state,
        decision="overwrite",
    )
    state["status"] = "overwritten"
    state["decision"] = "overwrite"
    state["resolved_at"] = _now()
    _save_state(state_path, state)
    _send(
        chat_id,
        [
            "✅ Existing archive copy overwrite kar di gayi.",
            "Purani archived copy ko isi file se replace kar diya gaya. Koi extra duplicate copy nahi bani.",
            *_common_lines(letter, state),
        ],
    )
    print("status=overwritten")
    print(f"existing_letter_id={letter_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
