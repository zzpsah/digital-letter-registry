"""High-confidence subject/body contradiction checks for official letters.

The original heading and operative body are independent source evidence. This
module flags a narrow, high-signal arrears-vs-leave mismatch seen in real Bihar
education circulars; it deliberately avoids guessing how the conflict should be
resolved.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class SourceContentConflict:
    subject_topic: str
    body_topic: str


def _topic_flags(text: str) -> tuple[bool, bool]:
    value = str(text or "").casefold()
    arrears = any(term in value for term in ("बकाया", "arrear", "arrears", "pending dues"))
    leave = any(
        term in value
        for term in ("अवकाश", "छुट्टी", "leave module", "leave application", "leave approval")
    )
    return arrears, leave


def extract_source_subject(extracted_text: str) -> str | None:
    """Extract the source subject heading without inventing a replacement title."""
    text = str(extracted_text or "")
    subject_match = re.search(
        r"(?:विषय|subject)\s*[:：\-–]?\s*(.*?)(?=\n\s*(?:प्रसंग|संदर्भ|महोदय|reference|ref\.?\s*:|dear\s+sir))",
        text,
        flags=re.IGNORECASE,
    )
    if not subject_match:
        return None
    subject = re.sub(r"\s+", " ", subject_match.group(1)).strip(" \t\r\n:：-–।")
    return subject or None


def detect_subject_body_conflict(extracted_text: str) -> SourceContentConflict | None:
    """Return a conflict only when subject and body strongly point to different topics."""
    text = str(extracted_text or "")
    subject_match = re.search(
        r"(?:विषय|subject)\s*[:：\-–]?\s*(.*?)(?=\n\s*(?:प्रसंग|संदर्भ|महोदय|reference|ref\.?\s*:|dear\s+sir))",
        text,
        flags=re.IGNORECASE,
    )
    if not subject_match:
        return None

    subject_text = subject_match.group(1)
    remainder = text[subject_match.end():]
    body_start = re.search(r"महोदय|dear\s+sir|sir/madam", remainder, flags=re.IGNORECASE)
    body_text = remainder[body_start.start():] if body_start else remainder

    subject_arrears, subject_leave = _topic_flags(subject_text)
    body_arrears, body_leave = _topic_flags(body_text)

    if subject_arrears and not subject_leave and body_leave and not body_arrears:
        return SourceContentConflict(subject_topic="arrears approval", body_topic="leave approval")
    if subject_leave and not subject_arrears and body_arrears and not body_leave:
        return SourceContentConflict(subject_topic="leave approval", body_topic="arrears approval")
    return None
