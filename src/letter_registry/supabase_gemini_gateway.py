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
        return f"supabase-gemini:{self.model}:document-v3"

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
            "Read the attached official Indian/Bihar education document directly and understand the WHOLE document, "
            "including later pages, tables, annexures and final memo/date lines. The original file is authoritative; "
            "supporting extracted text may be imperfect. If the supporting text contains an "
            "[INTAKE MESSAGE / SENDER INSTRUCTION] section, use it only for routing/priority, never as evidence for document facts.\n"
            "Do not invent facts, dates, memo numbers, authority, deadlines, actions, amounts, audiences or page numbers. "
            "The title may follow the source language. Write summary, action_required, key_points, applies_to, amount labels "
            "and page-reference labels in simple concise English for email. Also write summary_hi and action_required_hi in clear natural Hindi (Devanagari). Write whatsapp_summary in simple Roman-English/Hinglish "
            "(Latin script, no Devanagari unless an official title/name must be preserved). Keep clean_document_text in the source language "
            "(clean professional Hindi for Hindi documents). If uncertain use null/empty arrays.\n"
            "INTELLIGENCE PRIORITY RULE: category/subcategory and deterministic concept hints are secondary taxonomy only. Never derive title, summary, action, audience, or WhatsApp text from a category/hint unless the document itself supports it. If taxonomy conflicts with document evidence, trust the document and keep classification separate. "
            "TITLE RULE: create a concise semantic title from the actual purpose, preferably 4-12 words. Never use generic titles "
            "such as 'Official Education Document', 'Official Notice', 'आधिकारिक शैक्षणिक दस्तावेज़', 'आधिकारिक सूचना' or merely 'Letter'. "
            "Name the real subject/action such as fee revision, teacher grievance SOP, registration schedule, transfer order, scholarship instruction, etc.\n"
            "ACTION RULE: action_required must state exactly what the recipient must do, if anything. deadline is the actual last date/time. "
            "applies_to lists affected classes, employees, school types, districts, students or other audiences.\n"
            "AMOUNT RULE: important_amounts lists operationally relevant rupee amounts/fees/rates with a short label, currency INR, "
            "and page number when confidently visible. Do not list incidental numbers.\n"
            "PAGE RULE: page_references contains at most 6 useful 1-based page references for action, deadline, amount/table, eligibility/rule, "
            "or key decision. page_count is the document page count when reliable.\n"
            "SUMMARY RULE: summary must answer only what the document is about and its main purpose/decision in 1-2 short sentences. "
            "Do not repeat action steps, deadline, required documents or fee details unless they are the central subject. "
            "whatsapp_summary must express the same subject/purpose in clear Roman-English/Hinglish, ideally 1-2 short lines. "
            "key_points contains 3-6 operational points. "
            "clean_document_text reconstructs readable meaningful text without guessing unreadable passages.\n"
            "Required keys: title, authority, category, subcategory, summary, summary_hi, whatsapp_summary, action_required, action_required_hi, issue_date, "
            "reference_number, concepts, important_dates, deadline, applies_to, important_amounts, page_references, page_count, "
            "related_terms_hi, related_terms_en, confidence, key_points, clean_document_text.\n"
            f"Deterministic concept hints: {concepts}\n"
            "Supporting extracted text (may be noisy):\n"
            + extracted_text[:50000]
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
