# Handoff

The full-text size failure is addressed in source and on Oracle `dlr_primary`. Migration: `20261018193000_bound_fts_text_size.sql`. Fresh backup was archive-verified and restored to a disposable database before applying. A separate disposable test verified 2 MB extracted text can be stored and searched. The previously failed job completed after the fix. All 12 recovered WhatsApp processing jobs are completed. Two event receipts remain degraded only at the Gmail outbox stage.
