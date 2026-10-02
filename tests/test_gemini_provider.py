import json
import os
import unittest
from unittest.mock import patch

from letter_registry.context_hints import ContextHints
from letter_registry.gemini_provider import (
    GeminiDocumentContextProvider,
    GeminiProviderError,
)


class GeminiProviderTests(unittest.TestCase):
    def test_from_environment_requires_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
                GeminiDocumentContextProvider.from_environment()

    def test_structured_response_maps_to_context(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["api_key"] = req.headers["X-goog-api-key"]
            payload = json.loads(req.data.decode("utf-8"))
            seen["payload"] = payload

            model_json = {
                "title": "Inter Exam Form Extension",
                "authority": "BSEB",
                "category": "exam",
                "subcategory": "exam-form",
                "summary": "Synthetic summary",
                "action_required": "Complete form before deadline",
                "concepts": ["exam_form", "deadline_extension"],
                "important_dates": [
                    {
                        "label": "deadline",
                        "value": "2026-10-10",
                        "confidence": 0.9,
                    }
                ],
                "deadline": "2026-10-10T23:59:59+05:30",
                "related_terms_hi": ["परीक्षा प्रपत्र", "अंतिम तिथि"],
                "related_terms_en": ["exam form", "deadline extension"],
                "confidence": 0.92,
            }
            body = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": json.dumps(model_json, ensure_ascii=False)}
                            ]
                        }
                    }
                ]
            }
            return 200, json.dumps(body, ensure_ascii=False)

        provider = GeminiDocumentContextProvider(
            api_key="synthetic-key",
            model="gemini-3.8-flash",
            http_executor=executor,
        )
        context = provider.analyze(
            extracted_text="इंटरमीडिएट परीक्षा प्रपत्र की अंतिम तिथि बढ़ाई गई है।",
            hints=ContextHints(
                concepts=("exam_form", "deadline_extension"),
                matched_terms=("परीक्षा प्रपत्र", "अंतिम तिथि"),
                structure_terms=("विषय",),
            ),
        )

        self.assertEqual(context.authority, "BSEB")
        self.assertEqual(context.deadline, "2026-10-10T23:59:59+05:30")
        self.assertEqual(context.related_terms_hi[0], "परीक्षा प्रपत्र")
        self.assertIn("gemini-3.8-flash:generateContent", seen["url"])
        self.assertEqual(seen["api_key"], "synthetic-key")
        self.assertIn(
            "responseFormat",
            seen["payload"]["generationConfig"],
        )

    def test_invalid_response_raises_clean_error(self) -> None:
        provider = GeminiDocumentContextProvider(
            api_key="synthetic-key",
            http_executor=lambda req: (200, '{"candidates":[]}'),
        )
        with self.assertRaises(GeminiProviderError):
            provider.analyze(
                extracted_text="synthetic",
                hints=ContextHints((), (), ()),
            )


if __name__ == "__main__":
    unittest.main()
