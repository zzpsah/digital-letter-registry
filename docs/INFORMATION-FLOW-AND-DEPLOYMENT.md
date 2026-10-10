# eLetters / Digital Letter Registry — Information Flow & Deployment Inventory

**Audit date:** 2026-10-10  
**Scope:** documentation-only architecture inventory. No migration, backup, production configuration change, or application deployment was performed.  
**Evidence labels:** **Verified** means observed in repository source or a read-only live-runtime inspection; **Documented** means recorded in existing project documentation; **Unconfirmed** means current evidence does not prove a component's purpose or health.

**Visual reference:** [Open the full technical algorithm flowchart](TECHNICAL-FLOWCHART.html). The HTML includes decision branches, public routes, observed port mappings, service/timer inventory, integrations, failure conditions, and the documentation maintenance rule.

## 1. System at a glance

DLR (Digital Letter Registry; product name eLetters / Official Letter Intelligence Archive) is a searchable archive for official school/government PDFs and images. The original document is authoritative and immutable. OCR, extracted text, title, summary, authority, category, actions, relationships, and search metadata are derived and reprocessable.

~~~mermaid
flowchart TB
  U[Authorized user: mobile or desktop browser] --> SITE[Public Vercel site: eletters.vercel.app]
  SITE --> APP[Python FastAPI control plane: app.py → letter_registry.api]
  APP --> AUTH[Supabase Auth]
  APP --> DB[(Supabase Postgres: archive metadata, RLS, search, provenance, job queue)]
  APP -->|Server-side file operations proxy; port 10001| FUNNEL[Oracle Tailscale Funnel]
  FUNNEL --> API[Oracle DLR FastAPI: loopback port 8877]
  API --> DB
  API --> DRIVE[(Private Google Drive: original files)]
  APP -->|Document-understanding request| GEM[Supabase Edge Function: gemini-ai-gateway]
  GEM --> MODEL[Gemini document-understanding model]
  MODEL --> GEM
  GEM --> APP
  WA[Approved WhatsApp archive group] --> HERMES[Existing Hermes WhatsApp bridge / allowlisted intake hook]
  HERMES --> STAGE[Protected local staging queue]
  STAGE --> INTAKE[DLR intake consumer / worker]
  INTAKE --> DRIVE
  INTAKE --> DB
  WORKER[DLR processing worker + queue timer] <--> DB
  WORKER -->|Fetch immutable original| DRIVE
  WORKER --> EXTRACT[Native PDF text; Hindi/English OCR fallback]
  EXTRACT -->|Source evidence| GEM
  WORKER --> DB
  DB --> SEARCH[Authenticated search and document metadata]
  SEARCH --> APP
  API -->|Original-file read/stream| DRIVE
  WORKER --> MAIL[Gmail SMTP delivery]
  WORKER --> WHATSAPP[WhatsApp delivery through existing Hermes runtime]
~~~

### Flow notes

1. The browser uses the Vercel-hosted web/control plane. The root page is informational; the actual application/login UI is at **/app**.
2. Supabase Auth establishes user identity. Active archive membership and database Row Level Security (RLS), together with API checks, control archive permissions. Authentication alone does not grant archive access.
3. Original bytes live in the configured private Google Drive archive. Supabase stores structured letter records, source/provenance records, processing state/jobs, authorization, and searchable derived metadata.
4. Oracle handles private file operations and background processing that are not carried by the public Vercel deployment.
5. Approved WhatsApp intake enters through the existing Hermes session and a narrowly allowlisted connector. It stages supported media locally before the DLR intake path stores the original and creates provenance/processing records.
6. Processing prefers native PDF text and falls back to Hindi/English OCR. Document interpretation currently goes through the Supabase **gemini-ai-gateway**, keeping the Gemini key server-side.
7. The worker writes processing/search metadata and downstream delivery state back to Supabase. Gmail and WhatsApp are delivery channels, not the archive's system of record.
8. Search is currently keyword/full-text based with title, metadata, OCR text and fuzzy matching. **Semantic/vector search is not active** in the current-state record because the embedding stage is not provisioned; do not depict semantic search as production-live.

## 2. Public website and application routes

| Surface | Route | Purpose / status |
|---|---|---|
| Public website | https://eletters.vercel.app/ | Product-information homepage; recorded HTTP 200 on 2026-10-10 |
| Sign-in/application | https://eletters.vercel.app/app | Existing eLetters application UI; recorded HTTP 200 on 2026-10-10 |
| Privacy policy | https://eletters.vercel.app/privacy-policy | Public privacy policy; recorded HTTP 200 on 2026-10-10 |
| Health | https://eletters.vercel.app/api/v1/health | Health endpoint; recorded HTTP 200 on 2026-10-10 |

**Verified from repository:** Vercel's Python entry point is **app.py**, which imports **letter_registry.api:app** from **src/letter_registry**. **vercel.json** sets a 60-second maximum duration for **app.py**. Vercel environment variables determine the public origin. The Vercel deployment must not receive private Google Drive upload credentials.

## 3. Observed Oracle runtime and port inventory

The following mappings were read from the live Oracle server's Tailscale Serve status on 2026-10-10. The private Tailscale hostname is intentionally not duplicated in this public document.

### Tailscale Serve / Funnel mappings

| External listener | Exposure observed | Local upstream | Purpose / confidence |
|---|---|---|---|
| HTTPS port **10001** | **Funnel enabled — publicly reachable** | 127.0.0.1:8877 | **Verified:** DLR FastAPI service. Vercel code defaults its server-side file-operations proxy origin to the Oracle Tailscale origin on this port. Protected endpoints must enforce authentication/authorization independently of network location. |
| HTTPS port **10000** | **Funnel enabled — publicly reachable** | 127.0.0.1:9135 | Mapping verified; upstream's application purpose was not conclusively identified during this audit. |
| HTTPS port **8443** | **Funnel enabled — publicly reachable** | 127.0.0.1:9137 | Mapping verified; upstream's application purpose was not conclusively identified during this audit. |
| HTTPS port **10002** | Tailnet only | 127.0.0.1:9136 | Mapping verified; upstream's application purpose was not conclusively identified during this audit. |
| HTTPS port **3010** | Tailnet only | 127.0.0.1:3010 | A Next.js server process was observed on the local port; exact product ownership was not conclusively established. |
| Default HTTPS port **443** on the Tailscale hostname | Tailnet only | 127.0.0.1:9119 | Base reverse-proxy route; application identity not conclusively established in this audit. |
| Path **/bw** on the Tailscale hostname | Tailnet only | 127.0.0.1:9120 | Path mapping verified; do not assume it is part of DLR without a separate service audit. |
| HTTPS port **8877** | Tailnet only | 127.0.0.1:8877 | Direct tailnet route to the DLR FastAPI listener. |

**Exposure warning:** Funnel-enabled ports are public Internet entry points, not tailnet-only services. Port 10001 is intentionally used as the Vercel-to-Oracle file-operations path, but its public exposure must be treated as such. CORS is not authorization. Confirm route-level authentication, role checks, input limits, logging hygiene and rate limiting before changing exposure. Do not open additional ports as part of documentation or migration work.

### Local listeners / processes observed

| Local listener | Observed process / role | Notes |
|---|---|---|
| 127.0.0.1:8877 | Python Uvicorn running **letter_registry.api:app** from the DLR virtual environment | **Verified live process**; DLR FastAPI API and private file-operation surface |
| 127.0.0.1:3000 | Existing Hermes WhatsApp bridge (**bridge.js --port 3000**) | Existing session; DLR intake reuses it rather than starting a second WhatsApp client |
| 127.0.0.1:11434 | Ollama | Optional local experimentation/enrichment; not documented as a synchronous production dependency |
| 127.0.0.1:3010 | Next.js server process | Exact product association remains unconfirmed |
| 127.0.0.1:9135, :9136, :9137 | Tailscale Serve upstream listeners | Their owning application/services need a separate identification pass |
| 127.0.0.1:9119, :9120 | Tailscale Serve upstream listeners | Base and /bw mappings; exact application ownership not established here |

Only the DLR API process and Hermes bridge were conclusively identified from process command lines in this pass. This table is an inventory, not permission to stop, restart, expose, or repurpose any listener.

## 4. Runtime service and scheduled-job names

These DLR-related user-systemd unit filenames were found on the Oracle server. **The active/enabled state of every unit/timer was not established by this documentation audit.** Verify state before relying on a job.

- **dlr-api.service**
- **dlr-worker.service** / **dlr-worker.timer**
- **dlr-whatsapp-intake.service** / **dlr-whatsapp-intake.timer**
- **dlr-postprocess-delivery.service** / **dlr-postprocess-delivery.timer**
- **dlr-index-refresh.service** / **dlr-index-refresh.timer**
- **dlr-gmail-outbox.service** / **dlr-gmail-outbox.timer**
- **dlr-account-access-mailer.service** / **dlr-account-access-mailer.timer**

Related Hermes services also exist on this host. They are shared infrastructure and must not be modified as part of DLR work without checking their dependencies and ownership.

The WhatsApp connector architecture documents a one-minute consumer for the protected staging queue and a separate guarded pilot cap. The live connector must remain group-allowlisted and preserve provenance/deduplication. Do not broaden intake or bulk-import historical documents as part of this inventory task.

## 5. External services and trust boundaries

| Component | Responsibility | Boundary |
|---|---|---|
| Vercel | Public website, login/application UI, HTTP API/control plane | No private Drive upload credentials |
| Supabase Auth | User identity and session authentication | Separate from Drive OAuth |
| Supabase Postgres / PostgREST / RLS | Archive metadata, source provenance, roles/membership, search projection, processing jobs and status | Archive access must remain membership/role-scoped |
| Supabase Edge Function **gemini-ai-gateway** | Server-side document understanding using Gemini | Gemini credential stays server-side |
| Google Drive API | Private original PDF/image bytes | Server-side OAuth only; never expose Drive object IDs/tokens to browser |
| Oracle DLR FastAPI + worker | Private file operations, intake and background processing | Exposed through the observed Tailscale/Funnel mappings above |
| Hermes WhatsApp runtime | Existing WhatsApp connection, allowlisted inbound group and outbound messaging | Reuse existing session; do not create a parallel client |
| Gmail SMTP | Outbound email delivery | **smtp.gmail.com:465**; app password is injected from the approved secret manager |
| Ollama | Optional local model endpoint | Local loopback listener; not a required production document-understanding path |

Authentication and storage authorization are separate: Supabase membership controls archive access; server-side Google OAuth controls Drive operations; Tailscale controls network reachability but does not replace application authorization.

## 6. Current search and processing facts

- Native PDF text extraction is preferred when usable; Hindi/English OCR is a fallback for scanned/image content.
- The original is the authority for exact dates, memo numbers, names, amounts and official wording.
- Document understanding uses the Supabase **gemini-ai-gateway**.
- Keyword/full-text search includes extracted text plus title, summary, reference, authority, concepts, related terms, language aliases and fuzzy matching.
- Vector/semantic search is **not active** according to the current-state documentation because embeddings are not provisioned and **letter_chunks** is empty.
- A failed processing job is recoverable through the Admin Operations flow; retry must preserve job/attempt history and must not duplicate the original document.
- The original document stays immutable. Derived metadata can be regenerated; a revised official document with different bytes is a new document linked to the earlier one.

## 7. Repository and deployment boundaries

- Canonical Git repository: **zzpsah/digital-letter-registry**, default branch **main**.
- Canonical source repository is GitHub; Oracle is the live private runtime. They must be inspected independently.
- At the 2026-10-10 live audit, the Oracle working tree was clean but its checked-out commit was behind GitHub **main**. This documentation update is **not** deployed to Oracle. Before any runtime change or deployment, reconcile the checkout with the canonical branch and inspect the diff.
- Schema changes must be tracked through **supabase/migrations/**; do not make ad-hoc schema changes during this inventory.
- Real letters, extracted private text, Drive object IDs/URLs, Supabase credentials, OAuth tokens, passwords, cookies, SSH keys, private runtime identifiers and personal-data logs must not be committed.
- Preserve the accepted UI/UX exactly. This task changes documentation only.

## 8. Deliberately out of scope

This document does **not** migrate Supabase, establish database replication, create backups, copy originals, change DNS/Tailscale/Vercel configuration, alter firewall rules, restart services, enable new intake, or switch production traffic. Those decisions come only after this information-flow inventory is reviewed and any unresolved listener/service mappings are verified.

## 9. Follow-up verification checklist

- [ ] Identify the service/application owners for local upstreams 9135, 9136 and 9137.
- [ ] Confirm what is served on local ports 9119, 9120 and 3010 before changing them.
- [ ] Review every route exposed through Funnel port 10001 for route-level authentication, authorization, abuse limits and safe error logging.
- [ ] Confirm current state and schedules of each DLR user-systemd service and timer.
- [ ] Verify OCR binaries/language packs and runtime readiness from the actual Oracle environment.
- [ ] Reconcile Oracle Git checkout with GitHub **main** before deploying documentation or application changes.


## 8. Keep the flowchart synchronized

Whenever a code or infrastructure change affects routes, URLs, ports, services/timers, integrations, AI/OCR/translation behavior, storage boundaries, security exposure, or failure handling, update `docs/TECHNICAL-FLOWCHART.html` and this inventory in the same change. Update README and current-state/brain handoff records when architecture or operating status changes. Distinguish verified observations from unconfirmed assumptions; never document secrets, private Tailscale hostnames, private Drive identifiers, or credentials. Live runtime claims require a separate read-only check. Documentation updates do not imply deployment or VPS changes.
