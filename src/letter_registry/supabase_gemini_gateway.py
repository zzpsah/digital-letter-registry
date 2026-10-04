"""File-aware Gemini context provider via the existing Supabase Edge gateway."""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from urllib import error, request

from .context_hints import ContextHints
from .gemini_provider import GeminiDocumentContextProvider, GeminiProviderError
from .structured_analysis import StructuredDocumentContext


def _json_from_output(raw: str) -> dict[str, object]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\\s*", "", text, flags=re.I)
    text = re.sub(r"\\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise GeminiProviderError("Gemini gateway returned non-JSON document analysis") from exc
        data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise GeminiProviderError("Gemini gateway returned a non-object JSON result")
    return data


@dataclass(slots=True)
class SupabaseGeminiFileContextProvider:
    gateway_url: str
    model: str = "gemini-3.6-flash"
    timeout_seconds: int = 90

    @property
    def version(self) -> str:
        return f"supabase-gemini:{self.model}:document-v1"

    @classmethod
    def from_environment(cls) -> "SupabaseGeminiFileContextProvider":
        url = os.environ.get("SUPABASE_GEMINI_GATEWAY_URL", "").strip()
        if not url:
            project_url = os.environ.get("SUPABASE_GEMINI_PROJECT_URL", "").strip().rstrip("/")
            if project_url:
                url = project_url + "/functions/v1/gemini-ai-gateway"
        if not url:
            raise ValueError("SUPABASE_GEMINI_GATEWAY_URL or SUPABASE_GEMINI_PROJECT_URL is required")
        model = os.environ.get("AI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
        return cls(gateway_url=url, model=model)

    def analyze(self, *, extracted_text: str, hints: ContextHints) -> StructuredDocumentContext:
        raise GeminiProviderError("file-aware provider requires original document bytes")

    def analyze_file(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        concepts = ", ".join(hints.concepts) or "none"
        prompt = (
            "Return ONLY one valid JSON object, no markdown and no commentary.\n"
            "Read the attached official Indian/Bihar education document directly. "
            "The original file is authoritative; OCR below is supporting evidence and may be corrupted.\n"
            "Do not invent facts. Read visible headings, tables, memo/reference numbers, dates, amounts and codes. "
            "For Hindi documents write clean professional Hindi. If uncertain, use null. Do not copy OCR garbage. "
            "Summary must explain what the document actually does. key_points must contain useful operational points. "
            "clean_document_text should reconstruct readable meaningful text without guessing unreadable passages.\n"
            "Required keys: title, authority, category, subcategory, summary, action_required, issue_date, "
            "reference_number, concepts, important_dates, deadline, related_terms_hi, related_terms_en, confidence, "
            "key_points, clean_document_text.\n"
            f"Deterministic concept hints: {concepts}\n"
            "Supporting OCR (may be noisy):\n"
            + extracted_text[:40000]
        )
        payload = {
            "action": "analyze-file",
            "prompt": prompt,
            "model": self.model,
            "file_name": filename,
            "mime_type": mime_type,
            "file_data": base64.b64encode(file_bytes).decode("ascii"),
        }
        req = request.Request(
            self.gateway_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                status = response.status
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GeminiProviderError(f"Supabase Gemini gateway HTTP {exc.code}: {body[:500]}") from exc
        except error.URLError as exc:
            raise GeminiProviderError(f"Supabase Gemini gateway unavailable: {exc.reason}") from exc

        if status < 200 or status >= 300:
            raise GeminiProviderError(f"unexpected Supabase Gemini gateway HTTP status: {status}")

        envelope = json.loads(raw)
        if not envelope.get("success"):
            raise GeminiProviderError(str(envelope.get("error") or "Gemini gateway failed"))
        data = _json_from_output(str(envelope.get("output") or ""))
        return GeminiDocumentContextProvider._to_context(data)
