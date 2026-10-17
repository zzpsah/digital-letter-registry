# Computer Science Teacher — automatic Important rule

The document-processing repository now applies a deterministic relevance check when source-grounded context is saved.

## Matching policy

- Direct references to Computer Science teachers, computer teachers, and common Hindi spelling variants are eligible.
- A subject-only mention (Computer Science / कंप्यूटर विज्ञान) is eligible only when the same document also contains teacher/service context such as appointment, recruitment, seniority, pay, transfer, qualification, eligibility, or training.
- A generic computer/ICT equipment mention or a general teacher letter without Computer Science evidence is not enough.

## Action on a match

- Set the existing `letters.is_important` flag to `true` and set `important_at` if it is empty.
- Add a `[Auto-CS relevance]` note containing detected evidence and the source-grounded title/summary when available.
- Preserve human-written comments. On reprocessing, replace the previous generated note rather than duplicating it.
- Never change the original file, archive visibility, authority, category, or legal conclusions as part of this rule.
- The comment asks the reader to verify applicability, issuing order, and deadlines; it does not assert a legal entitlement.

## Scope and historical records

The rule runs when a document is processed or reprocessed. It does not scan or bulk-update old archive rows merely by being deployed. Historical backfill must first run in read-only preview, review the matched candidates/evidence, and only then apply a separately approved update. The existing UI is unchanged.

## Validation

`tests/test_teacher_relevance.py` covers explicit English/Hindi matches, subject-plus-service matches, non-matching generic computer mentions, and preservation/idempotency of generated comments. Repository tests cover the Important flag and manual-comment preservation.
