"""Archive account administration over guarded Supabase RPCs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from .access import ArchiveRole


class AccountAdminTransport(Protocol):
    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...


@dataclass(frozen=True, slots=True)
class ArchiveAccessEntry:
    kind: str
    record_id: str
    user_id: str | None
    email: str
    role: ArchiveRole
    status: str
    invite_code: str | None
    created_at: str | None


@dataclass(frozen=True, slots=True)
class ArchiveInviteResult:
    invite_id: str
    email: str
    role: ArchiveRole
    status: str
    invite_code: str
    user_id: str | None


@dataclass(frozen=True, slots=True)
class ArchiveMemberResult:
    user_id: str
    email: str
    role: ArchiveRole
    status: str


@dataclass(slots=True)
class SupabaseArchiveAccountAdmin:
    transport: AccountAdminTransport
    archive_id: str

    def __post_init__(self) -> None:
        self.archive_id = str(UUID(self.archive_id))

    @staticmethod
    def _email(value: object) -> str:
        email = str(value or "").strip().lower()
        if not email or "@" not in email or len(email) > 320:
            raise ValueError("invalid account email")
        return email

    @staticmethod
    def _role(value: object) -> ArchiveRole:
        return ArchiveRole(str(value))

    def list_access(self) -> list[ArchiveAccessEntry]:
        rows = self.transport.rpc(
            "dlr_list_archive_access",
            {"target_archive_id": self.archive_id},
        )
        entries: list[ArchiveAccessEntry] = []
        for row in rows:
            kind = str(row.get("kind") or "")
            if kind not in {"member", "invite"}:
                raise ValueError("invalid archive access entry kind")
            record_id = str(UUID(str(row["record_id"])))
            user_value = row.get("user_id")
            user_id = (
                str(UUID(str(user_value)))
                if user_value is not None
                else None
            )
            invite_value = row.get("invite_code")
            invite_code = (
                str(UUID(str(invite_value)))
                if invite_value is not None
                else None
            )
            status = str(row.get("status") or "")
            if kind == "member" and status not in {"active", "disabled"}:
                raise ValueError("invalid member status")
            if kind == "invite" and status not in {
                "pending",
                "accepted",
                "revoked",
            }:
                raise ValueError("invalid invite status")
            entries.append(
                ArchiveAccessEntry(
                    kind=kind,
                    record_id=record_id,
                    user_id=user_id,
                    email=self._email(row.get("email")),
                    role=self._role(row.get("role")),
                    status=status,
                    invite_code=invite_code,
                    created_at=(
                        str(row["created_at"])
                        if row.get("created_at") is not None
                        else None
                    ),
                )
            )
        return entries

    def invite(
        self,
        *,
        email: str,
        role: ArchiveRole,
    ) -> ArchiveInviteResult:
        rows = self.transport.rpc(
            "dlr_invite_archive_member",
            {
                "target_archive_id": self.archive_id,
                "target_email": self._email(email),
                "target_role": role.value,
            },
        )
        if len(rows) != 1:
            raise ValueError("unexpected invite response")
        row = rows[0]
        user_value = row.get("user_id")
        return ArchiveInviteResult(
            invite_id=str(UUID(str(row["invite_id"]))),
            email=self._email(row.get("email")),
            role=self._role(row.get("role")),
            status=str(row.get("status") or ""),
            invite_code=str(UUID(str(row["invite_code"]))),
            user_id=(
                str(UUID(str(user_value)))
                if user_value is not None
                else None
            ),
        )

    def update_member(
        self,
        *,
        user_id: str,
        role: ArchiveRole,
        status: str,
    ) -> ArchiveMemberResult:
        normalized_user_id = str(UUID(user_id))
        if status not in {"active", "disabled"}:
            raise ValueError("invalid member status")
        rows = self.transport.rpc(
            "dlr_update_archive_member",
            {
                "target_archive_id": self.archive_id,
                "target_user_id": normalized_user_id,
                "target_role": role.value,
                "target_status": status,
            },
        )
        if len(rows) != 1:
            raise ValueError("unexpected member update response")
        row = rows[0]
        return ArchiveMemberResult(
            user_id=str(UUID(str(row["user_id"]))),
            email=self._email(row.get("email")),
            role=self._role(row.get("role")),
            status=str(row.get("status") or ""),
        )

    def revoke_invite(self, invite_id: str) -> bool:
        rows = self.transport.rpc(
            "dlr_revoke_archive_invite",
            {
                "target_archive_id": self.archive_id,
                "target_invite_id": str(UUID(invite_id)),
            },
        )
        if not rows:
            return False
        value = rows[0]
        if "dlr_revoke_archive_invite" in value:
            return bool(value["dlr_revoke_archive_invite"])
        if "result" in value:
            return bool(value["result"])
        return bool(next(iter(value.values()), False))
