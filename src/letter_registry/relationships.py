"""Reviewable relationship intelligence.

Automated inference creates suggestions only. Status changes happen separately
and only from confirmed relationships.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from .models import DocumentRelationship


class RelationshipReviewStatus(StrEnum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class RelationshipSuggestion:
    source_letter_id: str
    target_letter_id: str
    relationship_type: DocumentRelationship
    confidence: float
    rationale: str
    version: str

    def __post_init__(self) -> None:
        UUID(self.source_letter_id)
        UUID(self.target_letter_id)
        if self.source_letter_id == self.target_letter_id:
            raise ValueError("relationship source and target must differ")
        if not 0 <= self.confidence <= 1:
            raise ValueError("relationship confidence must be between 0 and 1")
        if not self.rationale.strip():
            raise ValueError("relationship rationale is required")
        if not self.version.strip():
            raise ValueError("relationship version is required")


class RelationshipTransport(Protocol):
    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        ...

    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseRelationshipRepository:
    transport: RelationshipTransport

    def save_suggestion(
        self,
        suggestion: RelationshipSuggestion,
        *,
        owner_id: str,
    ) -> None:
        UUID(owner_id)
        self.transport.upsert(
            "letter_relationships",
            {
                "owner_id": owner_id,
                "source_letter_id": suggestion.source_letter_id,
                "target_letter_id": suggestion.target_letter_id,
                "relationship_type": suggestion.relationship_type.value,
                "confidence": suggestion.confidence,
                "review_status": RelationshipReviewStatus.SUGGESTED.value,
                "relationship_version": suggestion.version,
                "rationale": suggestion.rationale,
            },
            on_conflict=(
                "source_letter_id,target_letter_id,relationship_type"
            ),
        )

    def recalculate_statuses(
        self,
        *,
        version: str = "relationships-v1",
    ) -> tuple[int, int]:
        rows = self.transport.rpc(
            "recalculate_letter_statuses",
            {"status_rule_version": version},
        )
        if not rows:
            return (0, 0)
        row = rows[0]
        return (
            int(row.get("updated_superseded") or 0),
            int(row.get("updated_current") or 0),
        )
