# Tests

Passed 2026-10-03:
- Pilot limit parser accepts 2 and rejects invalid/out-of-range values.
- Real-looking upload is blocked once two real letters are already present.
- Synthetic/test filenames do not consume real pilot slots.
- Pilot UI indicator is covered.
- Focused API/web tests: 58/58.
- Full suite: 273/273.
- Private authenticated capabilities: real intake enabled, pilot mode true, limit 2, remaining 2.
- Public Vercel authenticated capabilities: synthetic-only true, Drive upload false.
- Worker one-shot: idle; timer: active.
- Live database before first real pilot upload: zero letters/jobs/processing rows.
