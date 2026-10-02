"""Approval-locked rename execution.

Preview generation remains separate from mutation. A rename can execute only
when the exact reviewed mapping digest is supplied and explicit confirmation is
true.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RenamePlanItem:
    record_id: str
    original_filename: str
    proposed_filename: str

    def __post_init__(self) -> None:
        UUID(self.record_id)
        if not self.original_filename.strip():
            raise ValueError("original_filename is required")
        if not self.proposed_filename.strip():
            raise ValueError("proposed_filename is required")
        if self.original_filename == self.proposed_filename:
            raise ValueError("rename plan item must actually change the filename")


@dataclass(frozen=True, slots=True)
class StoredRenameIdentity:
    record_id: str
    original_filename: str
    storage_provider: str
    storage_object_reference: str


class RenameIdentityRepository(Protocol):
    def get_rename_identity(self, record_id: str) -> StoredRenameIdentity | None:
        ...


class PrivateRenameTransport(Protocol):
    def rename(
        self,
        *,
        provider: str,
        object_reference: str,
        new_filename: str,
    ) -> None:
        ...


def rename_plan_digest(items: Iterable[RenamePlanItem]) -> str:
    """Return a stable SHA-256 digest for the exact reviewed mapping."""

    normalized = sorted(
        (
            {
                "record_id": item.record_id,
                "original_filename": item.original_filename,
                "proposed_filename": item.proposed_filename,
            }
            for item in items
        ),
        key=lambda row: (
            row["record_id"],
            row["original_filename"],
            row["proposed_filename"],
        ),
    )
    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(slots=True)
class ApprovedRenameExecutor:
    repository: RenameIdentityRepository
    transport: PrivateRenameTransport

    def execute(
        self,
        items: list[RenamePlanItem],
        *,
        approved_digest: str,
        confirmed: bool,
    ) -> int:
        if not confirmed:
            raise ValueError("explicit rename confirmation is required")
        if not items:
            raise ValueError("rename plan cannot be empty")

        actual_digest = rename_plan_digest(items)
        if approved_digest != actual_digest:
            raise ValueError("approved rename digest does not match the plan")

        identities: list[tuple[RenamePlanItem, StoredRenameIdentity]] = []
        for item in items:
            identity = self.repository.get_rename_identity(item.record_id)
            if identity is None:
                raise ValueError(f"rename source record not found: {item.record_id}")
            if identity.original_filename != item.original_filename:
                raise ValueError(
                    "rename preview is stale: current filename no longer matches"
                )
            identities.append((item, identity))

        for item, identity in identities:
            self.transport.rename(
                provider=identity.storage_provider,
                object_reference=identity.storage_object_reference,
                new_filename=item.proposed_filename,
            )

        return len(identities)
