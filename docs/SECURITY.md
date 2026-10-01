# Security

## Public repository boundary

This repository is public source/documentation only.

Never commit:
- real departmental/school letters or scans,
- student/personnel/private identifiers,
- WhatsApp exports or private message identifiers,
- credentials, API keys, tokens, cookies, OTP/MFA values,
- SSH private keys or secret connection strings,
- private storage URLs that grant access,
- OCR/context extracted from real private documents.

## Runtime principles

- originals stored privately with authenticated access;
- original files immutable after ingestion;
- web UI authenticated;
- least-privilege storage/database credentials;
- derived metadata may be corrected/reprocessed without modifying originals;
- bulk rename/reprocess operations should support preview and audit;
- provider/model changes must not expose archive contents unintentionally.

## AI/privacy

AI is an optional processing provider behind an adapter. Before enabling a cloud provider for live letters, review what document content is transmitted and confirm that this use is approved.

## Deployment

No production deployment, live archive import, public endpoint, or secret configuration is authorized by repository scaffolding alone.
