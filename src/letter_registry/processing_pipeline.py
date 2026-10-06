"""End-to-end derived processing orchestration for one archived document."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
import re

from .extraction import ExtractionResult, VersionedTextExtractor
from .models import DocumentRecord
from .quality_assessment import assess_document_quality
from .autonomous_learning import AutonomousCorrectionMemory
from .structured_analysis import (
    ContextAnalysisResult,
    DocumentContextProvider,
    ImportantAmount,
    PageReference,
    StructuredDocumentContext,
    analyze_document_context,
)


def _mime_type_for_path(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def _issue_date_from_filename(filename: str) -> str | None:
    """Use only a strongly-labelled filename date (for example: Dated-06-03-2026)."""
    match = re.search(
        r"(?:dated|date|दिनांक)[^0-9]{0,8}(\d{1,2})[./_-](\d{1,2})[./_-](\d{4})",
        filename or "",
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _issue_date_from_text(extracted_text: str) -> str | None:
    """Recover an official issue date from a labelled memo/date line."""
    text = extracted_text or ""
    strong = re.findall(
        r"(?:ज्ञापांक|पत्रांक|memo(?:randum)?\s*(?:no\.?|number)?|ref(?:erence)?\s*(?:no\.?|number)?)"
        r"[^\r\n]{0,220}?(?:दिनांक|dated)\s*[:：-]?\s*"
        r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    candidates = strong
    if not candidates:
        candidates = re.findall(
            r"(?:दिनांक|dated)\s*[:：-]?\s*"
            r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})",
            text,
            flags=re.IGNORECASE,
        )
    for parts in reversed(candidates):
        day, month, year = (int(part) for part in parts)
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            continue
    return None


_PAGE_MARKER_RE = re.compile(r"(?m)^\[\[PAGE\s+(\d+)\]\]\s*$")
_GENERIC_TITLES = {
    "official education document",
    "official document",
    "official notice",
    "udise notice",
    "udise notice / document",
    "school fee order / instructions",
    "विद्यालय शुल्क संबंधी आदेश",
    "विद्यालय शुल्क संबंधी आदेश/निर्देश",
    "education department letter",
    "आधिकारिक शैक्षणिक दस्तावेज़",
    "आधिकारिक शैक्षणिक दस्तावेज",
    "आधिकारिक दस्तावेज़",
    "आधिकारिक दस्तावेज",
    "आधिकारिक सूचना",
    "letter",
    "document",
}


def _page_map(extracted_text: str) -> dict[int, str]:
    text = extracted_text or ""
    matches = list(_PAGE_MARKER_RE.finditer(text))
    if not matches:
        return {1: text} if text.strip() else {}
    pages: dict[int, str] = {}
    for idx, match in enumerate(matches):
        page = int(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        pages[page] = text[start:end].strip()
    return pages


def _is_hindiish(text: str) -> bool:
    devanagari = sum(1 for ch in (text or "") if "\u0900" <= ch <= "\u097f")
    latin = sum(1 for ch in (text or "") if ch.isascii() and ch.isalpha())
    return devanagari >= 10 and devanagari >= latin * 0.2


def _semantic_title(
    current: str | None,
    *,
    extracted_text: str,
    summary: str | None,
    category: str | None,
    filename: str,
) -> str | None:
    title = " ".join(str(current or "").split()).strip(" -:|")
    title_folded = title.casefold()
    generic_title = (
        title_folded in _GENERIC_TITLES
        or (
            len(title.split()) <= 6
            and title_folded.startswith("official ")
            and any(word in title_folded for word in ("document", "notice", "letter"))
        )
        or (
            len(title.split()) <= 6
            and "आधिकारिक" in title
            and any(word in title for word in ("दस्तावेज", "सूचना", "पत्र"))
        )
    )
    if title and not generic_title:
        return title

    folded = " ".join(
        (extracted_text or "", str(summary or ""), str(category or ""), filename or "")
    ).casefold()
    category_folded = str(category or "").casefold()
    hindi = _is_hindiish(extracted_text)

    def choose(hi: str, en: str) -> str:
        return hi if hindi else en

    # Source evidence wins over taxonomy. Category is only a last-resort fallback.
    ict_signals = sum(
        term in folded
        for term in (
            "ict lab", "आई०सी०टी०", "आईसीटी", "smart class", "स्मार्ट क्लास",
            "computer science teacher", "कम्प्यूटर विज्ञान", "कंप्यूटर विज्ञान",
        )
    )
    nodal_signals = sum(
        term in folded
        for term in ("नोडल", "nodal", "प्रतिनियुक्त", "deputation", "mark on duty")
    )
    if ict_signals >= 2 and nodal_signals >= 1:
        return "ICT Lab / Smart Class Nodal & Deputation Order"

    if any(term in folded for term in ("teacher grievance", "शिक्षक शिकायत", "service grievance")):
        return choose("शिक्षक सेवा शिकायत निवारण निर्देश", "Teacher Service Grievance Instructions")
    if any(term in folded for term in ("registration", "पंजीयन", "पंजीकरण")):
        if any(term in folded for term in ("last date", "अंतिम तिथि", "schedule", "कार्यक्रम")):
            return choose("पंजीयन कार्यक्रम एवं अंतिम तिथि", "Registration Schedule and Deadline")
        return choose("पंजीयन संबंधी निर्देश", "Registration Instructions")
    if any(term in folded for term in ("admission", "नामांकन", "प्रवेश")):
        return choose("नामांकन संबंधी निर्देश", "Admission Instructions")
    if any(term in folded for term in ("transfer", "स्थानांतरण")):
        return choose("शिक्षक स्थानांतरण संबंधी आदेश", "Teacher Transfer Order")
    if any(term in folded for term in ("scholarship", "छात्रवृत्ति")):
        return choose("छात्रवृत्ति संबंधी निर्देश", "Scholarship Instructions")
    if any(term in folded for term in ("examination", "exam", "परीक्षा")):
        return choose("परीक्षा संबंधी निर्देश", "Examination Instructions")
    if ("शुल्क" in folded or "fee" in folded) and any(
        term in folded for term in ("पुनरीक्षित", "संशोधित", "revised", "revision")
    ):
        return choose("विद्यालय शुल्क पुनरीक्षण आदेश", "School Fee Revision Order")
    if ("शुल्क" in folded or "fee" in folded):
        return choose("विद्यालय शुल्क संबंधी आदेश", "School Fee Order and Instructions")

    # Taxonomy is consulted only after source-semantic rules fail.
    if any(term in category_folded for term in ("registration", "पंजीयन", "पंजीकरण")):
        return choose("पंजीयन संबंधी निर्देश", "Registration Instructions")
    if any(term in category_folded for term in ("admission", "नामांकन", "प्रवेश")):
        return choose("नामांकन संबंधी निर्देश", "Admission Instructions")
    if any(term in category_folded for term in ("exam", "examination", "परीक्षा")):
        return choose("परीक्षा संबंधी निर्देश", "Examination Instructions")
    if any(term in category_folded for term in ("scholarship", "छात्रवृत्ति")):
        return choose("छात्रवृत्ति संबंधी निर्देश", "Scholarship Instructions")
    if any(term in category_folded for term in ("fee", "शुल्क")):
        return choose("विद्यालय शुल्क संबंधी आदेश", "School Fee Order and Instructions")

    # Last-resort semantic fallback: a meaningful filename is better than a
    # generic system label. Strip common file boilerplate/date fragments.
    stem = Path(filename or "").stem
    stem = re.sub(r"(?i)\b(?:letter|scan|document|doc|final|copy)\b", " ", stem)
    stem = re.sub(r"\b\d{1,2}[-_.]\d{1,2}[-_.]\d{4}\b", " ", stem)
    stem = re.sub(r"[_-]+", " ", stem)
    stem = " ".join(stem.split()).strip()
    if 3 <= len(stem.split()) <= 18:
        return stem
    return title or None


_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](20\d{2})(?!\d)")


def _normalize_date_match(match: re.Match[str]) -> str | None:
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _deadline_from_pages(pages: dict[int, str]) -> str | None:
    keywords = (
        "अंतिम तिथि",
        "अंतिम दिनांक",
        "last date",
        "deadline",
        "extended up to",
        "extended till",
        "तिथि विस्तारित",
        "दिनांक तक",
    )
    candidates: list[tuple[int, str]] = []
    for page, text in pages.items():
        for line in text.splitlines():
            folded = line.casefold()
            if not any(term in folded for term in keywords):
                continue
            match = _DATE_RE.search(line)
            if match:
                normalized = _normalize_date_match(match)
                if normalized:
                    candidates.append((page, normalized))
    return candidates[-1][1] if candidates else None


_AMOUNT_RE = re.compile(
    r"(?:₹\s*[0-9][0-9,]*(?:\.\d{1,2})?|"
    r"(?:rs\.?|inr|रु\.?|रुपये|रूपये)\s*[:=-]?\s*[0-9][0-9,]*(?:\.\d{1,2})?|"
    r"[0-9][0-9,]*(?:\.\d{1,2})?\s*(?:रुपये|रूपये))",
    flags=re.IGNORECASE,
)


def _amounts_from_pages(pages: dict[int, str]) -> tuple[ImportantAmount, ...]:
    found: list[ImportantAmount] = []
    seen: set[tuple[str, int]] = set()
    for page, text in pages.items():
        for line in text.splitlines():
            matches = list(_AMOUNT_RE.finditer(line))
            if not matches:
                continue
            clean_line = " ".join(line.split()).strip(" -|•")
            for match in matches:
                value = match.group(0).strip()
                key = (re.sub(r"\s+", "", value.casefold()), page)
                if key in seen:
                    continue
                seen.add(key)
                label = clean_line
                if len(label) > 150:
                    label = label[:147].rstrip() + "…"
                found.append(
                    ImportantAmount(
                        label=label or "Amount",
                        value=value,
                        currency="INR",
                        page=page,
                    )
                )
                if len(found) >= 10:
                    return tuple(found)
    return tuple(found)


def _applies_to_from_text(context_text: str) -> tuple[str, ...]:
    folded = (context_text or "").casefold()
    values: list[str] = []
    rules = (
        (("शिक्षक", "teacher"), "Teachers"),
        (("प्रधानाध्यापक", "headmaster", "head teacher"), "Headmasters"),
        (("छात्र", "student"), "Students"),
        (("अभिभावक", "parent"), "Parents"),
        (("माध्यमिक विद्यालय", "secondary school"), "Secondary schools"),
        (("उच्च माध्यमिक", "higher secondary"), "Higher secondary schools"),
    )
    for terms, label in rules:
        if any(term in folded for term in terms):
            values.append(label)

    classes: list[str] = []
    roman = {"IX": "9", "X": "10", "XI": "11", "XII": "12"}
    for marker in re.finditer(r"(?:class\b|कक्षा|वर्ग)", folded, flags=re.IGNORECASE):
        # Capture a short class-expression window so forms such as
        # "कक्षा 11 एवं 12" or "Class IX-XII" include every class.
        segment = folded[marker.end(): marker.end() + 45]
        segment = re.split(r"[\n.;]", segment, maxsplit=1)[0]
        for raw in re.findall(r"(?<!\w)(9|10|11|12|ix|x|xi|xii)(?!\w)", segment, flags=re.IGNORECASE):
            normalized = roman.get(raw.upper(), raw)
            if normalized not in classes:
                classes.append(normalized)
    if classes:
        ordered = sorted(set(classes), key=int)
        values.append("Classes " + ", ".join(ordered))

    return tuple(dict.fromkeys(values))[:5]


def _tokens_for_match(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\w\u0900-\u097f]+", (value or "").casefold())
        if len(token) >= 4
    }


def _fallback_page_references(
    *,
    pages: dict[int, str],
    key_points: tuple[str, ...],
    deadline: str | None,
    amounts: tuple[ImportantAmount, ...],
) -> tuple[PageReference, ...]:
    if len(pages) < 4:
        return ()
    refs: list[PageReference] = []
    seen_pages_labels: set[tuple[int, str]] = set()

    for point in key_points[:5]:
        query = _tokens_for_match(point)
        if len(query) < 2:
            continue
        best_page = None
        best_hits = 0
        for page, text in pages.items():
            hits = len(query & _tokens_for_match(text))
            if hits > best_hits:
                best_page, best_hits = page, hits
        if best_page is not None and best_hits >= min(3, max(2, len(query) // 5)):
            label = " ".join(point.split()[:8]).rstrip(".,;:") or "Key point"
            key = (best_page, label.casefold())
            if key not in seen_pages_labels:
                refs.append(PageReference(label=label, page=best_page, detail=point))
                seen_pages_labels.add(key)

    for amount in amounts[:3]:
        if amount.page is not None:
            key = (amount.page, "amount")
            if key not in seen_pages_labels:
                refs.append(
                    PageReference(
                        label="Fee / amount details",
                        page=amount.page,
                        detail=amount.label,
                    )
                )
                seen_pages_labels.add(key)

    if deadline:
        deadline_variants = {deadline}
        iso = re.match(r"^(20\d{2})-(\d{2})-(\d{2})", deadline)
        if iso:
            year, month, day = iso.groups()
            deadline_variants.update(
                {
                    f"{day}-{month}-{year}",
                    f"{day}/{month}/{year}",
                    f"{day}.{month}.{year}",
                }
            )
        for page, text in pages.items():
            if any(value in text for value in deadline_variants):
                refs.append(PageReference(label="Deadline / last date", page=page, detail=deadline))
                break

    return tuple(refs[:6])


def _merge_operational_context(
    context: StructuredDocumentContext,
    *,
    extracted_text: str,
    filename: str,
) -> StructuredDocumentContext:
    pages = _page_map(extracted_text)
    page_count = context.page_count or (max(pages) if len(pages) > 1 else None)

    title = _semantic_title(
        context.title,
        extracted_text=extracted_text,
        summary=context.summary,
        category=context.category,
        filename=filename,
    )
    deadline = context.deadline or _deadline_from_pages(pages)

    detected_amounts = _amounts_from_pages(pages)
    merged_amounts: list[ImportantAmount] = list(context.important_amounts)
    amount_keys = {
        (re.sub(r"\s+", "", item.value.casefold()), item.page)
        for item in merged_amounts
        if item.value
    }
    for item in detected_amounts:
        key = (re.sub(r"\s+", "", item.value.casefold()), item.page)
        if key not in amount_keys:
            merged_amounts.append(item)
            amount_keys.add(key)
        if len(merged_amounts) >= 10:
            break

    applies_to = context.applies_to or _applies_to_from_text(
        " ".join(
            filter(
                None,
                (
                    extracted_text[:12000],
                    context.summary,
                    context.action_required,
                    " ".join(context.key_points),
                ),
            )
        )
    )

    refs = list(context.page_references)
    if page_count:
        refs = [ref for ref in refs if 1 <= ref.page <= page_count]
    if not refs:
        refs = list(
            _fallback_page_references(
                pages=pages,
                key_points=context.key_points,
                deadline=deadline,
                amounts=tuple(merged_amounts),
            )
        )

    return replace(
        context,
        title=title,
        deadline=deadline,
        applies_to=tuple(applies_to),
        important_amounts=tuple(merged_amounts[:10]),
        page_references=tuple(refs[:6]),
        page_count=page_count,
    )


def _refine_context_from_strong_evidence(
    context: StructuredDocumentContext,
    *,
    extracted_text: str,
    filename: str,
) -> StructuredDocumentContext:
    """Apply conservative deterministic fixes after an AI/fallback provider."""
    issue_date = (
        context.issue_date
        or _issue_date_from_filename(filename)
        or _issue_date_from_text(extracted_text)
    )

    folded = " ".join(
        (
            extracted_text or "",
            str(context.title or ""),
            str(context.summary or ""),
            " ".join(context.concepts),
        )
    ).casefold()
    teacher_grievance_sop = (
        ("standard operating procedure" in folded or "s.o.p" in folded)
        and ("grievance" in folded or "शिकायत" in folded)
        and ("teacher" in folded or "शिक्षक" in folded)
    )

    title = context.title
    authority = context.authority
    category = context.category
    summary = context.summary
    action_required = context.action_required
    reference_number = context.reference_number
    key_points = context.key_points

    if teacher_grievance_sop:
        title = "Teacher Service Grievance Redressal SOP"
        # This document type has strong issuer evidence in the header. Models
        # sometimes confuse the recipient list ("सभी जिला शिक्षा पदाधिकारी")
        # with the issuing authority, so deterministic evidence wins here.
        if (
            ("education" in folded or "शिक्षा" in folded)
            and ("bihar" in folded or "बिहार" in folded)
        ):
            authority = "Education Department, Government of Bihar (शिक्षा विभाग, बिहार सरकार)"
        category = "Teacher Service / Grievance SOP"
        if not reference_number:
            header_match = re.search(
                r"(?<!\d)(\d{1,3}/20\d{2})(?!\d)",
                (extracted_text or "")[:5000],
            )
            reference_number = header_match.group(1) if header_match else None

        summary = (
            "This document prescribes the SOP for resolving teachers' service-related grievances. "
            "It covers salary/payment handling through CFMS/Treasury, HRMS personal/family/nominee "
            "updates, structured grievance routing, leave matters, and corruption/legal complaints "
            "through the relevant prescribed channels."
        )
        action_required = (
            "Follow the applicable SOP route for the service issue: use CFMS/Treasury for payment "
            "matters, HRMS Self Service for personal/family/nominee changes, and the structured "
            "Grievance Module or prescribed authority for complaints."
        )
        key_points = (
            "The document sets out a 12-point/section SOP for teacher service-related grievance handling.",
            "Salary and payment matters are routed through CFMS/Treasury, including Bank Advice and Direct Credit processes.",
            "Personal, family and nominee changes are routed through HRMS Self Service with Maker-Approver handling.",
            "Complaints use the structured Grievance Module, with separate prescribed handling for leave, corruption and legal/statutory matters.",
        )

    refined = replace(
        context,
        title=title,
        authority=authority,
        category=category,
        summary=summary,
        action_required=action_required,
        issue_date=issue_date,
        reference_number=reference_number,
        key_points=key_points,
    )
    return _merge_operational_context(
        refined,
        extracted_text=extracted_text,
        filename=filename,
    )


class ProcessingRepository:
    """Narrow repository shape needed by derived processing."""

    def save_extraction_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ExtractionResult,
    ) -> None:
        ...

    def save_context_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ContextAnalysisResult,
    ) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ProcessingOutcome:
    extraction: ExtractionResult
    context: ContextAnalysisResult


def process_archived_document(
    path: str | Path,
    *,
    record: DocumentRecord,
    owner_id: str,
    extractor: VersionedTextExtractor,
    context_provider: DocumentContextProvider,
    repository: ProcessingRepository,
    fallback_context_provider: DocumentContextProvider | None = None,
    intake_context: str = "",
    correction_memory: AutonomousCorrectionMemory | None = None,
    extraction_override: ExtractionResult | None = None,
    progress_callback=None,
) -> ProcessingOutcome:
    """Process one already-archived source without mutating the original."""

    if progress_callback:
        progress_callback("text_reuse" if extraction_override is not None else "text_extraction", 25, "Reusing existing OCR/text" if extraction_override is not None else "Extracting text / OCR")
    extraction = extraction_override or extractor.extract(path)
    if progress_callback:
        progress_callback("text_ready", 40, "Document text ready")
    if extraction_override is None:
        repository.save_extraction_result(
            record,
            owner_id=owner_id,
            result=extraction,
        )

    if not extraction.text.strip():
        raise RuntimeError("cannot analyze document context without extracted text")

    analysis_text = correction_memory.apply(extraction.text) if correction_memory is not None else extraction.text
    intake_context = " ".join(str(intake_context or "").split()).strip()
    if intake_context:
        analysis_text += (
            "\n\n[INTAKE MESSAGE / SENDER INSTRUCTION — not document evidence]\n"
            + intake_context
        )

    used_fallback = False
    if progress_callback:
        progress_callback("ai_analysis", 55, "Analyzing document context")
    try:
        analyze_file = getattr(context_provider, "analyze_file", None)
        if callable(analyze_file):
            from .context_hints import detect_context_hints

            hints = detect_context_hints(analysis_text)
            direct_context = analyze_file(
                file_bytes=Path(path).read_bytes(),
                mime_type=_mime_type_for_path(Path(path)),
                filename=Path(path).name,
                extracted_text=analysis_text,
                hints=hints,
            )
            merged_concepts = tuple(dict.fromkeys((*hints.concepts, *direct_context.concepts)))
            if merged_concepts != direct_context.concepts:
                direct_context = replace(direct_context, concepts=merged_concepts)
            context = ContextAnalysisResult(
                context=direct_context,
                hints=hints,
                version=str(getattr(context_provider, "version")),
            )
        else:
            context = analyze_document_context(
                analysis_text,
                provider=context_provider,
            )
    except Exception:
        if fallback_context_provider is None:
            raise
        context = analyze_document_context(
            analysis_text,
            provider=fallback_context_provider,
        )
        used_fallback = True

    def _refine_and_score(candidate: ContextAnalysisResult):
        refined = ContextAnalysisResult(
            context=_refine_context_from_strong_evidence(
                candidate.context,
                extracted_text=extraction.text,
                filename=record.original_filename,
            ),
            hints=candidate.hints,
            version=candidate.version,
        )
        quality = assess_document_quality(
            extracted_text=extraction.text,
            context_confidence=refined.context.confidence,
            title=refined.context.title,
            authority=refined.context.authority,
            category=refined.context.category,
            reference_number=refined.context.reference_number,
            issue_date=refined.context.issue_date,
            clean_document_text=refined.context.clean_document_text,
        )
        refined = ContextAnalysisResult(
            context=replace(
                refined.context,
                quality_score=quality.score,
                quality_flags=quality.flags,
                needs_reprocessing=quality.needs_reprocessing,
                quality_version=quality.version,
            ),
            hints=refined.hints,
            version=refined.version,
        )
        return refined, quality

    context, quality = _refine_and_score(context)

    # A provider can return syntactically valid JSON that is still semantically weak.
    # Reprocess must not call that a success when a stronger fallback is available.
    if quality.needs_reprocessing and fallback_context_provider is not None and not used_fallback:
        try:
            fallback_context = analyze_document_context(
                analysis_text,
                provider=fallback_context_provider,
            )
            fallback_context, fallback_quality = _refine_and_score(fallback_context)

            def _completeness(value):
                fields = (
                    value.title, value.authority, value.summary, value.action_required,
                    value.reference_number, value.issue_date, value.clean_document_text,
                    value.whatsapp_summary, value.summary_hi, value.action_required_hi,
                )
                return sum(1 for field in fields if str(field or "").strip())

            current_ctx = context.context
            fallback_ctx = fallback_context.context
            stronger = (
                fallback_quality.score >= quality.score + 0.02
                or float(fallback_ctx.confidence or 0.0) >= float(current_ctx.confidence or 0.0) + 0.08
                or _completeness(fallback_ctx) >= _completeness(current_ctx) + 2
            )
            if stronger:
                context, quality = fallback_context, fallback_quality
        except Exception:
            pass

    if progress_callback:
        progress_callback("metadata_save", 75, "Saving title, summary and metadata")
    repository.save_context_result(
        record,
        owner_id=owner_id,
        result=context,
    )

    if correction_memory is not None:
        cleaned_text = str(context.context.clean_document_text or "").strip()
        if cleaned_text:
            correction_memory.observe(
                raw_text=extraction.text,
                cleaned_text=cleaned_text,
                document_id=record.record_id,
                confidence=context.context.confidence,
            )

    if progress_callback:
        progress_callback("metadata_saved", 82, "Document intelligence saved")
    return ProcessingOutcome(
        extraction=extraction,
        context=context,
    )
