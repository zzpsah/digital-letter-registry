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
                "issue_date": "2026-10-02",
                "reference_number": "BSEB/TEST-001",
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
        self.assertEqual(context.issue_date, "2026-10-02")
        self.assertEqual(context.reference_number, "BSEB/TEST-001")
        self.assertEqual(context.related_terms_hi[0], "परीक्षा प्रपत्र")
        self.assertIn("gemini-3.8-flash:generateContent", seen["url"])
        self.assertEqual(seen["api_key"], "synthetic-key")
        self.assertIn(
            "responseFormat",
            seen["payload"]["generationConfig"],
        )

    def test_file_analysis_sends_original_bytes_to_gemini(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            payload = json.loads(req.data.decode("utf-8"))
            seen["parts"] = payload["contents"][0]["parts"]
            data = {
                "title": "Synthetic file test",
                "authority": None,
                "category": None,
                "subcategory": None,
                "summary": "Synthetic summary",
                "summary_hi": "सिंथेटिक सारांश",
                "whatsapp_summary": "सिंथेटिक सारांश",
                "action_required": None,
                "action_required_hi": None,
                "issue_date": None,
                "reference_number": None,
                "concepts": [],
                "important_dates": [],
                "deadline": None,
                "applies_to": [],
                "important_amounts": [],
                "page_references": [],
                "page_count": None,
                "related_terms_hi": [],
                "related_terms_en": [],
                "confidence": 0.8,
                "key_points": [],
                "clean_document_text": "Synthetic file content",
            }
            response = {"candidates": [{"content": {"parts": [{"text": json.dumps(data, ensure_ascii=False)}]}}]}
            return 200, json.dumps(response, ensure_ascii=False)

        provider = GeminiDocumentContextProvider(api_key="synthetic-key", http_executor=executor)
        context = provider.analyze_file(
            file_bytes=b"synthetic original file bytes",
            mime_type="application/pdf",
            filename="synthetic.pdf",
            extracted_text="Synthetic extracted text",
            hints=ContextHints((), (), ()),
        )
        self.assertEqual(context.title, "Synthetic file test")
        self.assertEqual(seen["parts"][1]["inlineData"]["mimeType"], "application/pdf")
        self.assertEqual(seen["parts"][1]["inlineData"]["data"], "c3ludGhldGljIG9yaWdpbmFsIGZpbGUgYnl0ZXM=")
        self.assertIn("Original filename: synthetic.pdf", seen["parts"][0]["text"])

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
