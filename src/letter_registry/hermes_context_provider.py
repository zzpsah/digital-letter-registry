from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess

from .context_hints import ContextHints
from .quality_assessment import normalize_confidence
from .structured_analysis import (
    ImportantAmount,
    ImportantDate,
    PageReference,
    StructuredDocumentContext,
)
from .deterministic_context import DeterministicDocumentContextProvider


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("~~~"):
        text = text.strip("~")
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Hermes did not return JSON")
    return json.loads(text[start:end + 1])


@dataclass(frozen=True, slots=True)
class HermesDefaultModelContextProvider:
    command: str = "/home/prashant/.local/bin/hermes"
    timeout_seconds: int = 45
    version: str = "hermes:current-default-or-deterministic:text-v3"

    def analyze(self, *, extracted_text: str, hints: ContextHints) -> StructuredDocumentContext:
        prompt = (
            "You are the document-understanding fallback for a school official-letter archive.\n"
            "Analyze the extracted document text as a whole. It may contain reading errors. Do not invent unreadable facts. "
            "If an [INTAKE MESSAGE / SENDER INSTRUCTION] section is present, use it only for routing/priority, "
            "never as evidence for document facts.\n"
            "Return ONLY valid JSON with keys: title, authority, category, subcategory, summary, summary_hi, whatsapp_summary, action_required, action_required_hi, "
            "issue_date, reference_number, concepts, important_dates, deadline, applies_to, important_amounts, "
            "page_references, page_count, related_terms_hi, related_terms_en, confidence, key_points, clean_document_text.\n"
            "INTELLIGENCE PRIORITY: category/subcategory and deterministic hints are secondary taxonomy only. Never derive title, summary, action, audience, or WhatsApp text from taxonomy unless the document itself supports it. If taxonomy conflicts with document evidence, trust the document and keep classification separate.\n"
            "TITLE: create a concise semantic title (4-12 words) from the actual purpose. Never use generic titles like "
            "'Official Education Document', 'Official Notice', 'आधिकारिक दस्तावेज़', or merely 'Letter'.\n"
            "OUTPUT LANGUAGE: title may follow the source language. Write summary, action_required, key_points, applies_to, "
            "amount labels and page-reference labels in simple concise English for email. Also write summary_hi and action_required_hi in clear natural Hindi (Devanagari). Write whatsapp_summary in simple "
            "Roman-English/Hinglish using Latin script. Keep clean_document_text in the source language.\n"
            "SUMMARY: summary must say only what the document is about and its main purpose/decision in 1-2 short sentences. "
            "whatsapp_summary must express the same subject/purpose in clear Roman-English/Hinglish. Do not repeat action steps, "
            "deadline, required documents or amounts in either summary unless they are the actual central subject.\n"
            "ACTION: state exactly what the recipient must do. Extract the actual last date into deadline. "
            "applies_to identifies affected classes, teachers, students, schools or districts.\n"
            "AMOUNTS: important_amounts is an array of {label,value,currency,page}; include only operationally important fees/rates. "
            "PAGE REFERENCES: if [[PAGE N]] markers exist, return up to 6 useful {label,page,detail} references and page_count.\n"
            "STRICT EVIDENCE RULES: never reinterpret percentages, thresholds, counts, dates, money, or who/what a number applies to. "
            "If a numeric sentence is ambiguous, omit that numeric claim. Keep official names/reference/date exactly when supported. "
            "Dates must be ISO YYYY-MM-DD only when confident, otherwise null. important_dates must be objects with label,value,confidence.\n\n"
            "DOCUMENT TEXT:\n" + extracted_text[:32000]
        )
        try:
            proc = subprocess.run(
                [
                    self.command, "chat", "-q", prompt, "--oneshot", "-Q",
                    "--ignore-rules", "--max-turns", "1",
                    "--run-budget", str(self.timeout_seconds),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds + 10,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Hermes context failed rc={proc.returncode}: {proc.stderr[-500:]}"
                )
            data = _parse_json(proc.stdout)
        except Exception:
            return DeterministicDocumentContextProvider().analyze(
                extracted_text=extracted_text,
                hints=hints,
            )
        dates = tuple(
            ImportantDate(
                label=str(item.get("label") or "").strip(),
                value=str(item.get("value") or "").strip(),
                confidence=normalize_confidence(item.get("confidence")),
            )
            for item in (data.get("important_dates") or [])
            if isinstance(item, dict) and (item.get("label") or item.get("value"))
        )

        amounts: list[ImportantAmount] = []
        for item in (data.get("important_amounts") or []):
            if not isinstance(item, dict) or not item.get("value"):
                continue
            try:
                page = int(item["page"]) if item.get("page") is not None else None
            except (TypeError, ValueError):
                page = None
            amounts.append(
                ImportantAmount(
                    label=str(item.get("label") or "Amount").strip(),
                    value=str(item.get("value") or "").strip(),
                    currency=str(item.get("currency") or "INR").strip() or "INR",
                    page=page,
                )
            )

        page_refs: list[PageReference] = []
        for item in (data.get("page_references") or []):
            if not isinstance(item, dict):
                continue
            try:
                page = int(item.get("page") or 0)
            except (TypeError, ValueError):
                continue
            if page < 1:
                continue
            page_refs.append(
                PageReference(
                    label=str(item.get("label") or "Important section").strip(),
                    page=page,
                    detail=(str(item.get("detail")).strip() if item.get("detail") else None),
                )
            )

        try:
            page_count = int(data["page_count"]) if data.get("page_count") is not None else None
        except (TypeError, ValueError):
            page_count = None

        return StructuredDocumentContext(
            title=data.get("title"),
            authority=data.get("authority"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            summary=data.get("summary"),
            summary_hi=data.get("summary_hi"),
            whatsapp_summary=data.get("whatsapp_summary"),
            action_required=data.get("action_required"),
            action_required_hi=data.get("action_required_hi"),
            issue_date=data.get("issue_date"),
            reference_number=data.get("reference_number"),
            concepts=tuple(data.get("concepts") or ()),
            important_dates=dates,
            deadline=data.get("deadline"),
            applies_to=tuple(str(x) for x in data.get("applies_to") or ()),
            important_amounts=tuple(amounts),
            page_references=tuple(page_refs),
            page_count=page_count,
            related_terms_hi=tuple(data.get("related_terms_hi") or ()),
            related_terms_en=tuple(data.get("related_terms_en") or ()),
            confidence=normalize_confidence(data.get("confidence")),
            key_points=tuple(str(x) for x in data.get("key_points") or ()),
            clean_document_text=(str(data.get("clean_document_text")).strip() if data.get("clean_document_text") else None),
        )
