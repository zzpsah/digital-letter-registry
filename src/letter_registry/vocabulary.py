"""Hindi/English/Hinglish government and education vocabulary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConceptRule:
    concept: str
    terms: tuple[str, ...]


CONCEPT_RULES: tuple[ConceptRule, ...] = (
    ConceptRule("registration", ("पंजीयन", "पंजीकरण", "registration", "regn")),
    ConceptRule("exam_form", ("परीक्षा प्रपत्र", "exam form", "examination form")),
    ConceptRule("deadline", ("अंतिम तिथि", "last date", "deadline")),
    ConceptRule(
        "deadline_extension",
        ("तिथि विस्तार", "अवधि विस्तार", "date extension", "deadline extension", "extended"),
    ),
    ConceptRule(
        "required_action",
        (
            "आवश्यक कार्रवाई",
            "अनुपालन सुनिश्चित करें",
            "necessary action",
            "compliance",
        ),
    ),
    ConceptRule("udise", ("udise", "udise+", "यूडाइस")),
    ConceptRule("pen", (" pen ", "pen correction", "पेन")),
    ConceptRule("apaar", ("apaar", "अपार")),
    ConceptRule("eshikshakosh", ("eshikshakosh", "e-shikshakosh", "ईशिक्षाकोष")),
    ConceptRule("matric", ("matric", "मैट्रिक")),
    ConceptRule("intermediate", ("intermediate", "inter exam", "इंटर", "इंटरमीडिएट")),
    ConceptRule("scholarship", ("scholarship", "छात्रवृत्ति")),
    ConceptRule("admission", ("admission", "नामांकन", "प्रवेश")),
    ConceptRule("attendance", ("attendance", "उपस्थिति")),
    ConceptRule("fee", ("fee", "शुल्क")),
    ConceptRule("correction", ("correction", "सुधार", "संशोधन")),
    ConceptRule("verification", ("verification", "सत्यापन")),
    ConceptRule("training", ("training", "प्रशिक्षण")),
    ConceptRule("headmaster", ("headmaster", "प्रधानाध्यापक", "प्रधानाचार्य")),
    ConceptRule("deo", (" deo ", "जिला शिक्षा पदाधिकारी")),
    ConceptRule("dpo", (" dpo ", "जिला कार्यक्रम पदाधिकारी")),
)

STRUCTURE_TERMS: tuple[str, ...] = (
    "पत्रांक",
    "ज्ञापांक",
    "दिनांक",
    "प्रेषक",
    "प्रति",
    "विषय",
    "संदर्भ",
    "आदेशानुसार",
    "निर्देशित किया जाता है",
    "तत्काल प्रभाव से",
    "उपर्युक्त विषयक",
    "प्रासंगिक पत्र",
    "अधोहस्ताक्षरी",
)
