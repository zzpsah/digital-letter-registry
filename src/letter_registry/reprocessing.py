"""Preview-only recursive reprocessing planner.

The planner is deterministic and non-destructive. It compares stored processing
versions with a requested target set and returns the exact reasons each letter
would need reprocessing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


_COMPONENTS = (
    "ocr_version",
    "context_version",
    "dictionary_version",
    "filename_rule_version",
    "category_schema_version",
    "embedding_version",
    "status_rule_version",
)


@dataclass(frozen=True, slots=True)
class ReprocessingTargets:
    ocr_version: str
    context_version: str
    dictionary_version: str
    filename_rule_version: str
    category_schema_version: str
    embedding_version: str
    status_rule_version: str

    def as_dict(self) -> dict[str, str]:
        return {
            name: str(getattr(self, name)).strip()
            for name in _COMPONENTS
        }

    def __post_init__(self) -> None:
        if any(not value for value in self.as_dict().values()):
            raise ValueError("all target processing versions are required")


@dataclass(frozen=True, slots=True)
class ReprocessingPreviewItem:
    letter_id: str
    reasons: tuple[str, ...]
    current_versions: dict[str, str]
    target_versions: dict[str, str]


class ReprocessingTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseReprocessingPlanner:
    transport: ReprocessingTransport

    def preview(
        self,
        targets: ReprocessingTargets,
    ) -> list[ReprocessingPreviewItem]:
        rows = self.transport.select(
            "letter_processing",
            columns="letter_id," + ",".join(_COMPONENTS),
        )
        target = targets.as_dict()
        preview: list[ReprocessingPreviewItem] = []
        for row in rows:
            current = {
                name: str(row.get(name) or "unprocessed")
                for name in _COMPONENTS
            }
            reasons = tuple(
                name
                for name in _COMPONENTS
                if current[name] != target[name]
            )
            if reasons:
                preview.append(
                    ReprocessingPreviewItem(
                        letter_id=str(row["letter_id"]),
                        reasons=reasons,
                        current_versions=current,
                        target_versions=target,
                    )
                )
        return preview
