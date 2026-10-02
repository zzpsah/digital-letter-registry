"""Archive membership and role authorization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class ArchiveRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass(frozen=True, slots=True)
class ArchiveMembership:
    archive_id: str
    user_id: str
    role: ArchiveRole

    @property
    def can_write(self) -> bool:
        return self.role in {ArchiveRole.ADMIN, ArchiveRole.EDITOR}

    @property
    def is_admin(self) -> bool:
        return self.role is ArchiveRole.ADMIN


class ArchiveAccessTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseArchiveAccess:
    transport: ArchiveAccessTransport
    archive_id: str

    def __post_init__(self) -> None:
        self.archive_id = str(UUID(self.archive_id))

    def membership(self, user_id: str) -> ArchiveMembership | None:
        normalized_user_id = str(UUID(user_id))
        rows = self.transport.select(
            "archive_members",
            filters={
                "archive_id": self.archive_id,
                "user_id": normalized_user_id,
                "status": "active",
            },
            columns="archive_id,user_id,role,status",
        )
        if not rows:
            return None
        row = rows[0]
        try:
            role = ArchiveRole(str(row["role"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid archive membership role") from exc
        return ArchiveMembership(
            archive_id=str(UUID(str(row["archive_id"]))),
            user_id=str(UUID(str(row["user_id"]))),
            role=role,
        )

    def require(
        self,
        user_id: str,
        *,
        roles: set[ArchiveRole] | None = None,
    ) -> ArchiveMembership:
        membership = self.membership(user_id)
        if membership is None:
            raise PermissionError("active archive membership required")
        if roles is not None and membership.role not in roles:
            raise PermissionError("archive role does not permit this action")
        return membership
