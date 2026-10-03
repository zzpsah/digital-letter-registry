# Current State

Observed 2026-10-03:
- Private Oracle runtime real intake is enabled.
- Hard pilot limit is 2 real letters.
- Second slot is explicitly locked by default with `DLR_REAL_INTAKE_PILOT_SECOND_SLOT_UNLOCKED=false`.
- With zero real letters, authenticated private capabilities report pilot mode active, 2/2 remaining, review lock false.
- After the first real letter exists, the API automatically blocks a second real-looking upload until slot two is explicitly unlocked after review.
- Public Vercel remains synthetic-only for intake and has no Drive upload capability.
- Dedicated worker is healthy and timer active.
- Live archive is empty before the first pilot upload.
- Full suite passes 275/275.

Next action: manually upload the first real official letter in the private Oracle DLR UI. Review OCR/search/metadata/original access. Only then unlock slot two if the review passes.
