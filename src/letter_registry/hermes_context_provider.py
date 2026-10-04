from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess

from .context_hints import ContextHints
from .structured_analysis import StructuredDocumentContext, ImportantDate
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
    version: str = "hermes:current-default-or-deterministic:text-v1"

    def analyze(self, *, extracted_text: str, hints: ContextHints) -> StructuredDocumentContext:
        prompt = (
            "You are the document-understanding fallback for a school Digital Letter Registry.\n"
            "Analyze the OCR text below. OCR may contain errors. Do not invent unreadable facts. "
            "If an [INTAKE MESSAGE / SENDER INSTRUCTION] section is present, use it for routing, urgency, "
            "priority and requested handling, but never as evidence for document facts.\n"
            "Return ONLY valid JSON with keys: title, authority, category, subcategory, summary, "
            "action_required, issue_date, reference_number, concepts, important_dates, deadline, "
            "related_terms_hi, related_terms_en, confidence, key_points, clean_document_text.\n"
            "Basic metadata and summary must be suitable for an English email. "
            "STRICT EVIDENCE RULES: never reinterpret percentages, thresholds, counts, dates, money, "
            "or who/what a number applies to. Preserve the subject of every numeric rule exactly. "
            "If a numeric sentence is even slightly ambiguous, omit that numeric claim from summary/action. "
            "Do not convert a rule about number/percentage of teachers on leave into a rule about attendance percentage. "
            "Keep official names/reference/date exactly when clearly supported. "
            "Dates must be ISO YYYY-MM-DD only when confident, otherwise null. "
            "important_dates must be an array of objects with label,value,confidence.\n\n"
            "OCR TEXT:\n" + extracted_text[:24000]
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
                confidence=(float(item["confidence"]) if item.get("confidence") is not None else None),
            )
            for item in (data.get("important_dates") or [])
            if isinstance(item, dict) and (item.get("label") or item.get("value"))
        )
        return StructuredDocumentContext(
            title=data.get("title"),
            authority=data.get("authority"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            summary=data.get("summary"),
            action_required=data.get("action_required"),
            issue_date=data.get("issue_date"),
            reference_number=data.get("reference_number"),
            concepts=tuple(data.get("concepts") or ()),
            important_dates=dates,
            deadline=data.get("deadline"),
            related_terms_hi=tuple(data.get("related_terms_hi") or ()),
            related_terms_en=tuple(data.get("related_terms_en") or ()),
            confidence=(float(data["confidence"]) if data.get("confidence") is not None else None),
            key_points=tuple(str(x) for x in data.get("key_points") or ()),
            clean_document_text=(str(data.get("clean_document_text")).strip() if data.get("clean_document_text") else None),
        )
