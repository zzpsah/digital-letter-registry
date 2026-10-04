import tempfile
import unittest
from pathlib import Path

from letter_registry.autonomous_learning import AutonomousCorrectionMemory


class AutonomousCorrectionMemoryTests(unittest.TestCase):
    def test_repeated_high_confidence_known_term_auto_promotes(self):
        with tempfile.TemporaryDirectory() as td:
            memory = AutonomousCorrectionMemory(
                path=Path(td) / "memory.json",
                minimum_confidence=0.90,
                known_term_threshold=3,
                general_threshold=5,
            )
            raw = "विद्यालय में उपसथिति प्रतिदिन दर्ज करें"
            clean = "विद्यालय में उपस्थिति प्रतिदिन दर्ज करें"

            for index in range(3):
                memory.observe(
                    raw_text=raw,
                    cleaned_text=clean,
                    document_id=f"doc-{index}",
                    confidence=0.96,
                )

            stats = memory.stats()
            self.assertEqual(stats["promoted"], 1)
            self.assertIn(
                "उपस्थिति",
                memory.apply("आज की उपसथिति दर्ज करें"),
            )

    def test_low_confidence_does_not_learn(self):
        with tempfile.TemporaryDirectory() as td:
            memory = AutonomousCorrectionMemory(path=Path(td) / "memory.json")
            for index in range(10):
                memory.observe(
                    raw_text="उपसथिति",
                    cleaned_text="उपस्थिति",
                    document_id=f"doc-{index}",
                    confidence=0.70,
                )
            self.assertEqual(memory.stats()["promoted"], 0)

    def test_numbers_are_never_learned_as_corrections(self):
        with tempfile.TemporaryDirectory() as td:
            memory = AutonomousCorrectionMemory(path=Path(td) / "memory.json")
            for index in range(6):
                memory.observe(
                    raw_text="पत्रांक 720 दिनांक 2026",
                    cleaned_text="पत्रांक 721 दिनांक 2027",
                    document_id=f"doc-{index}",
                    confidence=0.99,
                )
            self.assertEqual(memory.stats()["promoted"], 0)


if __name__ == "__main__":
    unittest.main()
