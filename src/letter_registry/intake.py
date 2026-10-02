"""Private upload/intake service with synthetic-first safety policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import DocumentRecord
from .orchestration import ingest_original
from .persistence import LetterRepository
from .jobs import ProcessingJob, ProcessingQueue
from .storage import OriginalStorage


_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


@dataclass(frozen=True, slots=True)
class IntakePolicy:
    synthetic_only: bool = True
    max_bytes: int = 20 * 1024 * 1024
    allowed_extensions: frozenset[str] = frozenset(_ALLOWED_EXTENSIONS)

    def validate(self, path: Path) -> None:
        if not path.is_file():
            raise ValueError("upload path must be an existing file")

        extension = path.suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValueError("unsupported upload file type")

        size = path.stat().st_size
        if size < 1:
            raise ValueError("upload file is empty")
        if size > self.max_bytes:
            raise ValueError("upload exceeds configured size limit")

        if self.synthetic_only:
            name = path.name.casefold()
            if "synthetic" not in name and "test" not in name:
                raise ValueError(
                    "real document intake is disabled; filename must clearly indicate synthetic/test data"
                )


@dataclass(frozen=True, slots=True)
class IntakeResult:
    record: DocumentRecord
    job: ProcessingJob


@dataclass(slots=True)
class IntakeService:
    storage: OriginalStorage
    repository: LetterRepository
    queue: ProcessingQueue
    policy: IntakePolicy = IntakePolicy()

    def ingest(
        self,
        path: str | Path,
        *,
        owner_id: str,
    ) -> IntakeResult:
        source = Path(path)
        self.policy.validate(source)

        record = ingest_original(
            source,
            storage=self.storage,
            repository=self.repository,
            owner_id=owner_id,
        )
        job = self.queue.enqueue(
            letter_id=record.record_id,
            owner_id=owner_id,
        )
        return IntakeResult(record=record, job=job)
