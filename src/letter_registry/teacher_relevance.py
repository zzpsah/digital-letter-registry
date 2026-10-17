"""Deterministic relevance rules for Computer Science teacher letters.

Only source text and source-grounded metadata can trigger automatic importance.
The generated note is deliberately labelled and does not claim a legal outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


AUTO_COMMENT_PREFIX = "[Auto-CS relevance]"

# Direct role/subject phrases are strong evidence. Keep Hindi spelling variants.
_DIRECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Computer Science Teacher", re.compile(r"\bcomputer\s+science\s+teachers?\b", re.I)),
    ("Computer Teacher", re.compile(r"\bcomputer\s+teachers?\b", re.I)),
    ("CS Teacher", re.compile(r"\bcs\s+teachers?\b", re.I)),
    ("कंप्यूटर विज्ञान शिक्षक", re.compile(r"(?:कंप्यूटर|कम्प्यूटर)\s*(?:विज्ञान|साइंस)\s*(?:के\s*)?शिक्षक", re.I)),
    ("कंप्यूटर शिक्षक", re.compile(r"(?:कंप्यूटर|कम्प्यूटर)\s*शिक्षक", re.I)),
    ("संगणक शिक्षक", re.compile(r"संगणक\s*शिक्षक", re.I)),
)

_SUBJECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Computer Science", re.compile(r"\bcomputer\s+science\b", re.I)),
    ("कंप्यूटर विज्ञान", re.compile(r"(?:कंप्यूटर|कम्प्यूटर)\s*(?:विज्ञान|साइंस)", re.I)),
    ("Computer subject", re.compile(r"\bcomputer\s+(?:subject|teacher|education)\b", re.I)),
)

_TEACHER_SERVICE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("teacher/service context", re.compile(
        r"\b(?:teacher|teachers|teaching|appointment|recruitment|seniority|service|"
        r"pay\s*scale|salary|transfer|posting|promotion|qualification|eligibility|"
        r"training|b\.ed\.?|tre[- ]?\d|vacancy|cadre|subject\s+teacher)\b", re.I
    )),
    ("शिक्षक/सेवा संदर्भ", re.compile(
        r"शिक्षक|शिक्षिका|नियुक्ति|बहाली|वरीयता|सेवा\s*शर्त|वेतन|स्थानांतरण|"
        r"पदस्थापन|प्रोन्नति|योग्यता|प्रशिक्षण|प्रशिक्षित|अप्रशिक्षित|विषय\s*शिक्षक"
    )),
)


@dataclass(frozen=True, slots=True)
class TeacherRelevance:
    is_relevant: bool
    evidence: tuple[str, ...] = ()
    comment: str | None = None


def classify_computer_science_teacher_letter(
    *,
    extracted_text: str = "",
    title: str | None = None,
    summary: str | None = None,
    action_required: str | None = None,
    category: str | None = None,
) -> TeacherRelevance:
    """Classify only clear role-specific or subject-plus-service matches."""
    source = "\n".join(str(value or "") for value in (
        title, summary, action_required, category, extracted_text
    ))
    if not source.strip():
        return TeacherRelevance(False)

    direct_evidence = tuple(
        label for label, pattern in _DIRECT_PATTERNS if pattern.search(source)
    )
    subject_evidence = tuple(
        label for label, pattern in _SUBJECT_PATTERNS if pattern.search(source)
    )
    service_evidence = tuple(
        label for label, pattern in _TEACHER_SERVICE_PATTERNS if pattern.search(source)
    )

    # An explicit Computer Science/computer-teacher role is enough. A generic
    # mention of computers is not; subject mentions need teacher/service context.
    relevant = bool(direct_evidence or (subject_evidence and service_evidence))
    if not relevant:
        return TeacherRelevance(False)

    evidence = tuple(dict.fromkeys((*direct_evidence, *subject_evidence, *service_evidence)))
    evidence_text = ", ".join(evidence[:4])
    source_summary = " ".join(str(summary or "").split()).strip()
    source_title = " ".join(str(title or "").split()).strip()
    context = source_summary or source_title
    note = (
        f"{AUTO_COMMENT_PREFIX} This letter appears relevant to Computer Science teachers. "
        f"Evidence detected: {evidence_text}."
    )
    if context:
        note += f" Document context: {context[:420]}"
    note += " Confirm the exact applicability, issuing order and any deadline before acting."
    return TeacherRelevance(True, evidence=evidence, comment=note)


def merge_auto_comment(existing_comment: str | None, generated_comment: str) -> str:
    """Replace this rule's previous note while preserving any human-written note."""
    existing = str(existing_comment or "").strip()
    blocks = re.split(r"(?=\[Auto-CS relevance\])", existing)
    preserved = [block.strip() for block in blocks if block.strip() and not block.lstrip().startswith(AUTO_COMMENT_PREFIX)]
    preserved.append(generated_comment.strip())
    return "\n\n".join(preserved)
