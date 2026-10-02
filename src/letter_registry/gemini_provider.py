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
from .structured_analysis import ImportantDate, StructuredDocumentContext


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
        "action_required": {"type": ["string", "null"]},
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
        "related_terms_hi": {"type": "array", "items": {"type": "string"}},
        "related_terms_en": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": ["number", "null"]},
    },
    "required": [
        "title",
        "authority",
        "category",
        "subcategory",
        "summary",
        "action_required",
        "concepts",
        "important_dates",
        "deadline",
        "related_terms_hi",
        "related_terms_en",
        "confidence",
    ],
}


@dataclass(slots=True)
class GeminiDocumentContextProvider:
    api_key: str
    model: str = "gemini-3.8-flash"
    http_executor: HttpExecutor = _default_http_executor

    @property
    def version(self) -> str:
        return f"gemini:{self.model}:context-v1"

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
            "Analyze this official Indian/Bihar education letter. "
            "Do not invent dates, memo numbers, authority, deadlines, or actions. "
            "Use null when uncertain. Keep summaries concise and preserve Hindi meaning.\n\n"
            f"Deterministic concept hints: {concepts}\n"
            f"Government structure hints: {structure}\n\n"
            "Extract: title, authority, category, subcategory, summary, action_required, "
            "concepts, important_dates, deadline, related_terms_hi, related_terms_en, confidence.\n\n"
            "LETTER TEXT:\n"
            f"{extracted_text}"
        )

    @staticmethod
    def _to_context(data: dict[str, object]) -> StructuredDocumentContext:
        dates = tuple(
            ImportantDate(
                label=str(item["label"]),
                value=str(item["value"]),
                confidence=(
                    float(item["confidence"])
                    if item.get("confidence") is not None
                    else None
                ),
            )
            for item in data.get("important_dates", [])
            if isinstance(item, dict) and "label" in item and "value" in item
        )

        return StructuredDocumentContext(
            title=data.get("title"),
            authority=data.get("authority"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            summary=data.get("summary"),
            action_required=data.get("action_required"),
            concepts=tuple(str(x) for x in data.get("concepts", [])),
            important_dates=dates,
            deadline=data.get("deadline"),
            related_terms_hi=tuple(str(x) for x in data.get("related_terms_hi", [])),
            related_terms_en=tuple(str(x) for x in data.get("related_terms_en", [])),
            confidence=(
                float(data["confidence"])
                if data.get("confidence") is not None
                else None
            ),
        )
