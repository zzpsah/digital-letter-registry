from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from .vocabulary import CONCEPT_RULES, STRUCTURE_TERMS


_WORD_RE = re.compile(r"[A-Za-z\u0900-\u097f][A-Za-z\u0900-\u097f._+-]*", re.UNICODE)


def _known_terms() -> set[str]:
    terms: set[str] = set()
    for rule in CONCEPT_RULES:
        for phrase in rule.terms:
            terms.update(token.casefold() for token in _WORD_RE.findall(phrase))
    for phrase in STRUCTURE_TERMS:
        terms.update(token.casefold() for token in _WORD_RE.findall(phrase))
    return terms


KNOWN_TERMS = _known_terms()


def _safe_token(value: str) -> bool:
    if len(value) < 3 or len(value) > 48:
        return False
    if any(ch.isdigit() for ch in value):
        return False
    return bool(_WORD_RE.fullmatch(value))


@dataclass(slots=True)
class AutonomousCorrectionMemory:
    path: Path
    minimum_confidence: float = 0.90
    known_term_threshold: int = 3
    general_threshold: int = 5

    @classmethod
    def from_environment(cls) -> "AutonomousCorrectionMemory":
        raw = os.environ.get(
            "DLR_OCR_LEARNING_FILE",
            "/home/prashant/.hermes/state/dlr-learning/ocr-corrections.json",
        ).strip()
        return cls(path=Path(raw))

    def _load(self) -> dict[str, object]:
        if not self.path.is_file():
            return {"schema": 1, "revision": 0, "candidates": {}, "promoted": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"schema": 1, "revision": 0, "candidates": {}, "promoted": {}}
        if not isinstance(data, dict):
            return {"schema": 1, "revision": 0, "candidates": {}, "promoted": {}}
        data.setdefault("schema", 1)
        data.setdefault("revision", 0)
        data.setdefault("candidates", {})
        data.setdefault("promoted", {})
        return data

    def _save(self, data: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        data["revision"] = int(data.get("revision") or 0) + 1
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=".ocr-learning-",
            delete=False,
        ) as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            temp = Path(handle.name)
        temp.chmod(0o600)
        temp.replace(self.path)

    def apply(self, text: str) -> str:
        data = self._load()
        promoted = data.get("promoted")
        if not isinstance(promoted, dict) or not promoted:
            return text

        replacements = {
            str(source): str(item.get("target") or "")
            for source, item in promoted.items()
            if isinstance(item, dict) and item.get("target")
        }
        if not replacements:
            return text

        pattern = re.compile(
            r"(?<!\w)("
            + "|".join(
                sorted((re.escape(key) for key in replacements), key=len, reverse=True)
            )
            + r")(?!\w)",
            flags=re.IGNORECASE,
        )

        def replace(match: re.Match[str]) -> str:
            return replacements.get(match.group(0).casefold(), match.group(0))

        normalized = {key.casefold(): value for key, value in replacements.items()}
        replacements = normalized
        return pattern.sub(replace, text)

    def observe(
        self,
        *,
        raw_text: str,
        cleaned_text: str,
        document_id: str,
        confidence: float | None,
    ) -> int:
        if confidence is None or confidence < self.minimum_confidence:
            return 0
        if not raw_text.strip() or not cleaned_text.strip() or not document_id.strip():
            return 0

        raw_tokens = _WORD_RE.findall(raw_text)
        clean_tokens = _WORD_RE.findall(cleaned_text)
        matcher = SequenceMatcher(
            None,
            [token.casefold() for token in raw_tokens],
            [token.casefold() for token in clean_tokens],
            autojunk=False,
        )

        observations: list[tuple[str, str]] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "replace" or i2 - i1 != 1 or j2 - j1 != 1:
                continue
            source = raw_tokens[i1]
            target = clean_tokens[j1]
            if not _safe_token(source) or not _safe_token(target):
                continue
            if source.casefold() == target.casefold():
                continue
            similarity = SequenceMatcher(
                None, source.casefold(), target.casefold(), autojunk=False
            ).ratio()
            if similarity < 0.55:
                continue
            observations.append((source.casefold(), target))

        if not observations:
            return 0

        data = self._load()
        candidates = data.get("candidates")
        promoted = data.get("promoted")
        if not isinstance(candidates, dict):
            candidates = {}
            data["candidates"] = candidates
        if not isinstance(promoted, dict):
            promoted = {}
            data["promoted"] = promoted

        promoted_now = 0
        for source, target in observations:
            if source in promoted:
                continue
            key = source
            item = candidates.get(key)
            if not isinstance(item, dict) or str(item.get("target") or "").casefold() != target.casefold():
                item = {
                    "target": target,
                    "documents": [],
                    "observations": 0,
                    "average_confidence": 0.0,
                }
                candidates[key] = item

            documents = [str(x) for x in (item.get("documents") or [])]
            if document_id in documents:
                continue
            documents.append(document_id)
            old_n = int(item.get("observations") or 0)
            old_avg = float(item.get("average_confidence") or 0.0)
            new_n = old_n + 1
            item["documents"] = documents[-20:]
            item["observations"] = new_n
            item["average_confidence"] = round(
                ((old_avg * old_n) + float(confidence)) / new_n,
                4,
            )

            threshold = (
                self.known_term_threshold
                if target.casefold() in KNOWN_TERMS
                else self.general_threshold
            )
            if new_n >= threshold and float(item["average_confidence"]) >= self.minimum_confidence:
                promoted[key] = {
                    "target": target,
                    "documents": documents[-20:],
                    "observations": new_n,
                    "average_confidence": item["average_confidence"],
                    "auto_promoted": True,
                }
                candidates.pop(key, None)
                promoted_now += 1

        self._save(data)
        return promoted_now

    def stats(self) -> dict[str, int]:
        data = self._load()
        candidates = data.get("candidates")
        promoted = data.get("promoted")
        return {
            "revision": int(data.get("revision") or 0),
            "candidates": len(candidates) if isinstance(candidates, dict) else 0,
            "promoted": len(promoted) if isinstance(promoted, dict) else 0,
        }
