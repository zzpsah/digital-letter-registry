"""Gemini structured-context provider.

Uses the Gemini REST API with structured JSON output. API key and model are
runtime configuration; the archive schema remains provider-neutral.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, request

from .context_hints import ContextHints
from .quality_assessment import normalize_confidence
from .structured_analysis import (
    ImportantAmount,
    ImportantDate,
    PageReference,
    StructuredDocumentContext,
)


class GeminiProviderError(RuntimeError):
    """Raised when Gemini analysis fails or returns an invalid response."""


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=60) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiProviderError(
            f"Gemini request failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GeminiProviderError(f"Gemini request failed: {exc.reason}") from exc


_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": ["string", "null"]},
        "authority": {"type": ["string", "null"]},
        "category": {"type": ["string", "null"]},
        "subcategory": {"type": ["string", "null"]},
        "summary": {"type": ["string", "null"]},
        "summary_hi": {"type": ["string", "null"]},
        "whatsapp_summary": {"type": ["string", "null"]},
        "action_required": {"type": ["string", "null"]},
        "action_required_hi": {"type": ["string", "null"]},
        "issue_date": {"type": ["string", "null"]},
        "reference_number": {"type": ["string", "null"]},
        "concepts": {"type": "array", "items": {"type": "string"}},
        "important_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                    "confidence": {"type": ["number", "null"]},
                },
                "required": ["label", "value", "confidence"],
            },
        },
        "deadline": {"type": ["string", "null"]},
        "applies_to": {"type": "array", "items": {"type": "string"}},
        "important_amounts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                    "currency": {"type": "string"},
                    "page": {"type": ["integer", "null"]},
                },
                "required": ["label", "value", "currency", "page"],
            },
        },
        "page_references": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "page": {"type": "integer"},
                    "detail": {"type": ["string", "null"]},
                },
                "required": ["label", "page", "detail"],
            },
        },
        "page_count": {"type": ["integer", "null"]},
        "related_terms_hi": {"type": "array", "items": {"type": "string"}},
        "related_terms_en": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": ["number", "null"]},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "clean_document_text": {"type": ["string", "null"]},
    },
    "required": [
        "title",
        "authority",
        "category",
        "subcategory",
        "summary",
        "summary_hi",
        "whatsapp_summary",
        "action_required",
        "action_required_hi",
        "issue_date",
        "reference_number",
        "concepts",
        "important_dates",
        "deadline",
        "applies_to",
        "important_amounts",
        "page_references",
        "page_count",
        "related_terms_hi",
        "related_terms_en",
        "confidence",
        "key_points",
        "clean_document_text",
    ],
}


@dataclass(slots=True)
class GeminiDocumentContextProvider:
    api_key: str
    model: str = "gemini-3.8-flash"
    http_executor: HttpExecutor = _default_http_executor

    @property
    def version(self) -> str:
        return f"gemini:{self.model}:context-v3"

    @classmethod
    def from_environment(cls) -> "GeminiDocumentContextProvider":
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required at runtime")

        model = os.environ.get("AI_MODEL", "gemini-3.8-flash").strip()
        if not model:
            raise ValueError("AI_MODEL cannot be empty")

        provider = os.environ.get("AI_PROVIDER", "gemini").strip().lower()
        if provider != "gemini":
            raise ValueError("AI_PROVIDER must be 'gemini' for this adapter")

        return cls(api_key=api_key, model=model)

    def analyze(
        self,
        *,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        prompt = self._build_prompt(extracted_text=extracted_text, hints=hints)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseFormat": {
                    "text": {
                        "mimeType": "application/json",
                        "schema": _CONTEXT_SCHEMA,
                    }
                },
            },
        }

        req = request.Request(
            (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model}:generateContent"
            ),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GeminiProviderError(f"unexpected Gemini HTTP status: {status}")

        try:
            response = json.loads(raw)
            text = response["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GeminiProviderError("Gemini returned an invalid structured response") from exc

        return self._to_context(data)

    @staticmethod
    def _build_prompt(*, extracted_text: str, hints: ContextHints) -> str:
        concepts = ", ".join(hints.concepts) or "none"
        structure = ", ".join(hints.structure_terms) or "none"
        return (
            "Analyze this official Indian/Bihar education document as a whole, not only its first page or heading. "
            "Do not invent dates, memo numbers, authority, deadlines, actions, amounts, audiences, or page numbers. "
            "Use null/empty arrays when uncertain. The input may contain noisy extracted text; silently correct obvious "
            "spelling, spacing, character-confusion and line-break errors when the intended text is clear. "
            "Do not copy unreadable garbage into user-facing fields. The title may follow the source language. Write "
            "summary, action_required, key_points, applies_to, amount labels and page-reference labels in simple concise English for email. "
            "Also write summary_hi and action_required_hi in clear natural Hindi (Devanagari), preserving official names/numbers. "
            "Write whatsapp_summary in simple Roman-English/Hinglish (Latin script, no Devanagari unless an official title/name must be preserved). "
            "Keep clean_document_text in the source language (clean natural Hindi for Hindi documents). "
            "Preserve official names, UDISE codes, reference numbers, dates and amounts exactly.\n\n"
            "INTELLIGENCE PRIORITY RULE: category/subcategory are secondary taxonomy only. Never use a category label or deterministic hint as the basis for title, summary, action, audience, or WhatsApp text unless the document evidence itself supports it. If category/hints conflict with the actual document, trust the document and classify separately. Build user-facing meaning from the document purpose, operative clauses, annexures, filename/context clues, and repeated evidence. "
            "TITLE RULE: create a concise semantic title from the document's actual purpose, preferably 4-12 words. "
            "Avoid generic titles such as 'Official Education Document', 'Official Notice', 'आधिकारिक शैक्षणिक दस्तावेज़', "
            "'आधिकारिक सूचना', or merely 'Letter'. Include the real subject/action, for example fee revision, teacher grievance SOP, "
            "registration schedule, transfer order, scholarship instruction, etc.\n"
            "ACTION RULE: action_required should say exactly what the recipient must do, if anything. "
            "Extract the actual deadline separately. applies_to should identify the affected class, employee group, school type, district, "
            "student group, or other audience.\n"
            "AMOUNT RULE: important_amounts must include operationally relevant rupee amounts/fees/rates with a short label; "
            "do not list incidental numbers.\n"
            "PAGE RULE: if page markers such as [[PAGE 7]] are present, page_references should point to the most useful pages for "
            "the action, deadline, important amount/table, eligibility/rule, or key decision. Use 1-based page numbers and at most 6 entries. "
            "page_count should be the highest reliable page marker, otherwise null.\n"
            "SUMMARY RULE: summary must answer only what the document is about and its main purpose/decision, in 1-2 short sentences. "
            "Do not repeat action steps, deadline, required documents or fee details unless they are the actual central subject; those belong in separate fields. "
            "whatsapp_summary must express the same subject/purpose in clear Roman-English/Hinglish, ideally 1-2 short lines. "
            "key_points should contain 3-6 useful operational points, not boilerplate.\n\n"
            f"Deterministic concept hints: {concepts}\n"
            f"Government structure hints: {structure}\n\n"
            "Extract: title, authority, category, subcategory, summary, summary_hi, whatsapp_summary, action_required, action_required_hi, "
            "issue_date (YYYY-MM-DD only when confidently present), reference_number, concepts, important_dates, deadline, "
            "applies_to, important_amounts, page_references, page_count, related_terms_hi, related_terms_en, confidence, "
            "key_points, clean_document_text.\n\n"
            "LETTER TEXT:\n"
            f"{extracted_text}"
        )

    @staticmethod
    def _to_context(data: dict[str, object]) -> StructuredDocumentContext:
        dates = tuple(
            ImportantDate(
                label=str(item["label"]),
                value=str(item["value"]),
                confidence=normalize_confidence(item.get("confidence")),
            )
            for item in data.get("important_dates", [])
            if isinstance(item, dict) and "label" in item and "value" in item
        )
        amounts = tuple(
            ImportantAmount(
                label=str(item.get("label") or "Amount"),
                value=str(item.get("value") or ""),
                currency=str(item.get("currency") or "INR"),
                page=(int(item["page"]) if item.get("page") is not None else None),
            )
            for item in data.get("important_amounts", [])
            if isinstance(item, dict) and item.get("value")
        )
        page_references = tuple(
            PageReference(
                label=str(item.get("label") or "Important section"),
                page=int(item["page"]),
                detail=(str(item["detail"]).strip() if item.get("detail") is not None else None),
            )
            for item in data.get("page_references", [])
            if isinstance(item, dict) and item.get("page") is not None
        )

        raw_issue_date = data.get("issue_date")
        issue_date = None
        if raw_issue_date:
            from datetime import date
            try:
                issue_date = date.fromisoformat(str(raw_issue_date)).isoformat()
            except ValueError:
                issue_date = None

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
            issue_date=issue_date,
            reference_number=data.get("reference_number"),
            concepts=tuple(str(x) for x in data.get("concepts", [])),
            important_dates=dates,
            deadline=data.get("deadline"),
            applies_to=tuple(str(x) for x in data.get("applies_to", [])),
            important_amounts=amounts,
            page_references=page_references,
            page_count=(int(data["page_count"]) if data.get("page_count") is not None else None),
            related_terms_hi=tuple(str(x) for x in data.get("related_terms_hi", [])),
            related_terms_en=tuple(str(x) for x in data.get("related_terms_en", [])),
            confidence=normalize_confidence(data.get("confidence")),
            key_points=tuple(str(x) for x in data.get("key_points", [])),
            clean_document_text=(
                str(data.get("clean_document_text")).strip()
                if data.get("clean_document_text") is not None
                else None
            ),
        )
