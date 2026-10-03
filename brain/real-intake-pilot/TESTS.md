# Tests

Passed 2026-10-03:
- Pilot limit parser accepts 2 and rejects invalid/out-of-range values.
- Real-looking upload is blocked once two real letters are already present.
- Synthetic/test filenames do not consume real pilot slots.
- Pilot UI indicator is covered.
- Focused API/web tests: 58/58.
- Full suite: 275/275.
- Private authenticated capabilities: real intake enabled, pilot mode true, limit 2, remaining 2.
- Public Vercel authenticated capabilities: synthetic-only true, Drive upload false.
- Worker one-shot: idle; timer: active.
- Live database before first real pilot upload: zero letters/jobs/processing rows.

- Second-slot review gate: one existing real letter + locked flag rejects the second real upload with HTTP 409.
- Explicit slot-two unlock allows the second real upload while the hard cap remains enforced.
- Zero-letter live capability state: pilot mode true, remaining 2, review lock false.


## First real-letter pilot live verification

Passed 2026-10-03:
- Human-owned job claimed/completed by dedicated worker while preserving document owner.
- Broken embedded-font Hindi triggered forced OCR fallback.
- OCR processing completed with the configured Hindi+English runtime.
- Deterministic explicit metadata and smart filename were generated.
- Authenticated search returned the real record.
- Authenticated original streaming returned the private original successfully.
- Pilot state: one slot remaining; second slot review-locked.
- Full suite: 280/280.
