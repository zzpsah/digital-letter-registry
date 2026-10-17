# eLetters / Digital Letter Registry — Information Flow & Deployment Inventory

**Audit date:** 2026-10-16
**Scope:** architecture inventory reconciled with the Oracle PostgreSQL primary and DLR worker state. This documentation update did not migrate data, change production configuration, or deploy the application.
**Evidence labels:** **Verified** means observed in repository source or a read-only live-runtime inspection; **Documented** means recorded in existing project documentation; **Unconfirmed** means current evidence does not prove a component's purpose or health.

**Visual reference:** [Open the full technical algorithm flowchart](TECHNICAL-FLOWCHART.html). The HTML includes decision branches, public routes, observed port mappings, service/timer inventory, integrations, failure conditions, and the documentation maintenance rule.

## 1. System at a glance

DLR (Digital Letter Registry; product name eLetters / Official Letter Intelligence Archive) is a searchable archive for official school/government PDFs and images. The original document is authoritative and immutable. OCR, extracted text, title, summary, authority, category, actions, relationships, and search metadata are derived and reprocessable.

~~~mermaid
flowchart TB
  U[Authorized user: mobile or desktop browser] --> SITE[Public Vercel site: eletters.vercel.app]
  SITE --> APP[Python FastAPI control plane: app.py → letter_registry.api]
  APP --> BRIDGE[Oracle FastAPI compatibility bridge]
  BRIDGE --> AUTH[Local GoTrue Auth: Supabase-compatible]
  BRIDGE --> REST[Local PostgREST: Supabase-compatible Data API]
  REST --> DB[(Oracle PostgreSQL dlr_primary: metadata, RLS, search, provenance, job queue)]
  APP -->|Server-side file operations proxy; port 10001| FUNNEL[Oracle Tailscale Funnel]
  FUNNEL --> API[Oracle DLR FastAPI: loopback port 8877]
  API --> REST
  API --> DRIVE[(Private Google Drive: original files)]
  WORKER -->|Direct Gemini when Bitwarden key is injected| MODEL[Google Gemini document-understanding model]
  WORKER -.->|Legacy fallback only when direct key is absent| GEM[Supabase Edge Function: gemini-ai-gateway]
  GEM --> MODEL
  MODEL --> WORKER
  WA[Approved WhatsApp archive group] --> HERMES[Existing Hermes WhatsApp bridge / allowlisted intake hook]
  HERMES --> STAGE[Protected local staging queue]
  STAGE --> WATCH[systemd path watcher + durable event dispatcher]
  WATCH --> N8N[Authenticated n8n event pipeline]
  N8N --> INTAKE[Bitwarden-aware DLR intake consumer]
  INTAKE --> DRIVE
  INTAKE --> REST
  N8N --> WORKER[One-job DLR worker + postprocess / index refresh]
  WORKER <--> REST
  WORKER -->|Fetch immutable original| DRIVE
  WORKER --> EXTRACT[Native PDF text; Hindi/English OCR fallback]
  EXTRACT -->|Source evidence| MODEL
  WORKER --> REST
  DB --> SEARCH[Authenticated search and document metadata]
  SEARCH --> APP
  API -->|Original-file read/stream| DRIVE
  WORKER --> MAIL[Gmail SMTP delivery]
  WORKER --> WHATSAPP[WhatsApp delivery through existing Hermes runtime]
~~~

### Flow notes

1. The browser uses the Vercel-hosted web/control plane. The root page is informational; the actual application/login UI is at **/app**.
2. Local GoTrue establishes user identity through the Supabase-compatible Auth API. Active archive membership and PostgreSQL Row Level Security (RLS), together with API checks, control archive permissions. Authentication alone does not grant archive access.
3. Original bytes live in the configured private Google Drive archive. Oracle PostgreSQL `dlr_primary` stores structured letter records, source/provenance records, processing state/jobs, authorization, and searchable derived metadata for the migrated workload.
4. Oracle handles private file operations and background processing that are not carried by the public Vercel deployment.
5. Approved WhatsApp intake enters through the existing Hermes session and a narrowly allowlisted connector. It stages supported media locally; a systemd path watcher dispatches a durable event to the authenticated n8n pipeline, which runs intake → one-job worker → postprocess/delivery → Gmail outbox → index refresh. The dispatcher verifies the per-message staged `done/` or `failed/` outcome instead of treating n8n HTTP success alone as proof of ingestion. The live WhatsApp cap is bounded at 150 source messages and 100 MiB per attachment; normal web upload remains capped at 20 MiB.
6. Processing prefers native PDF text and falls back to Hindi/English OCR. Source-subject extraction is bounded to a single line: when a recognized transition heading does not follow, it fails closed instead of absorbing later body text into the subject. Subject/body conflicts still lower confidence and require human review. The Oracle worker now prefers direct Google Gemini when the Bitwarden-managed `DLR_GEMINI_API_KEY` is injected. On 2026-10-16, both a live synthetic text request and a live synthetic original-file request succeeded using `gemini-3.5-flash-lite`; one controlled real archive reprocess reached `complete/100%` and changed context version to `gemini:gemini-3.5-flash-lite:context-v3`. However, confidence remained 0.45 and `needs_reprocessing=true`, so semantic correctness is not verified. The legacy Supabase **gemini-ai-gateway** returned HTTP 402 `exceed_egress_quota` and is not the active primary route.
7. Processing-job creation must read the target letter's `archive_id` and include it in the insert. The local-primary `processing_jobs` table requires this field and RLS checks active archive membership against it; omitting it caused HTTP 403/42501 and blocked manual reprocessing. The queue now resolves the archive from the visible target letter before inserting.
8. The worker writes processing/search metadata and downstream delivery state back through the local Supabase-compatible Data API to Oracle PostgreSQL. Gmail and WhatsApp are delivery channels, not the archive's system of record. Embeddings remain opt-in and were not enabled during Gemini recovery.
9. Search is currently keyword/full-text based with title, metadata, OCR text and fuzzy matching. **Semantic/vector search is not active**; `letter_chunks` remains empty because embedding generation is intentionally disabled.

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

The live connector is event-driven: `dlr-whatsapp-event-dispatch.path` watches the protected staging directory; the legacy one-minute business timers remain inactive. The connector must remain group-allowlisted and preserve provenance/deduplication. Permanent failures are quarantined with explicit reasons and must not be reported as successful intake. The WhatsApp-only upload cap is configurable up to 100 MiB; ordinary web uploads retain the 20 MiB default.

## 5. External services and trust boundaries

| Component | Responsibility | Boundary |
|---|---|---|
| Vercel | Public website, login/application UI, HTTP API/control plane | No private Drive upload credentials |
| Local GoTrue / Oracle PostgREST / PostgreSQL RLS | User identity, archive metadata, source provenance, roles/membership, search projection, processing jobs and status through Supabase-compatible routes | Oracle `dlr_primary` is primary; access remains membership/role-scoped |
| Oracle direct Gemini provider | Primary worker document understanding using Bitwarden-injected `DLR_GEMINI_API_KEY`; live synthetic and one-real-letter checks passed 2026-10-16 | Key is injected only at runtime; embeddings remain separately opt-in |
| Supabase Edge Function **gemini-ai-gateway** | Legacy compatibility path when no direct key is configured | Observed HTTP 402 `exceed_egress_quota` on 2026-10-15; not the active primary route |
| Google Drive API | Private original PDF/image bytes | Server-side OAuth only; never expose Drive object IDs/tokens to browser |
| Oracle DLR FastAPI + worker | Private file operations, intake and background processing | Exposed through the observed Tailscale/Funnel mappings above |
| Hermes WhatsApp runtime | Existing WhatsApp connection, allowlisted inbound group and outbound messaging | Reuse existing session; do not create a parallel client |
| Gmail SMTP | Outbound email delivery | **smtp.gmail.com:465**; app password is injected from the approved secret manager |
| Ollama | Optional local model endpoint | Local loopback listener; not a required production document-understanding path |

Authentication and storage authorization are separate: local GoTrue identity plus archive membership/RLS control archive access; server-side Google OAuth controls Drive operations; Tailscale controls network reachability but does not replace application authorization. Hosted Supabase is a recovery/replication candidate, not a verified replica.

## 6. Current search and processing facts

- Native PDF text extraction is preferred when usable; Hindi/English OCR is a fallback for scanned/image content.
- The original is the authority for exact dates, memo numbers, names, amounts and official wording.
- Document understanding in the Oracle worker uses direct Gemini when the Bitwarden-managed key is present. The direct provider and original-file request were live-tested on 2026-10-16; the worker successfully reprocessed one real letter and saved `gemini:gemini-3.5-flash-lite:context-v3`. The Supabase gateway remains a legacy path and is currently quota-blocked (HTTP 402).
- Keyword/full-text search includes extracted text plus title, summary, reference, authority, concepts, related terms, language aliases and fuzzy matching.
- Vector/semantic search is **not active** according to the current-state documentation because embeddings are not provisioned and **letter_chunks** is empty.
- A failed processing job is recoverable through the Admin Operations flow; retry must preserve job/attempt history and must not duplicate the original document.
- The original document stays immutable. Derived metadata can be regenerated; a revised official document with different bytes is a new document linked to the earlier one.

## 7. Repository and deployment boundaries

- Canonical Git repository: **zzpsah/digital-letter-registry**, default branch **main**.
- Canonical source repository is GitHub; Oracle is the live private runtime. They must be inspected independently.
- Historical note: the 2026-10-10 audit found the Oracle checkout behind GitHub **main**. On 2026-10-16, the Oracle checkout was fast-forwarded to the then-current remote `main`. The implementation changes were reviewed, committed as `aa2c54d`, pushed, and deployed on Oracle as revision `b16c899`. The guarded Ansible deployment ran the full suite before restarting the API; post-deploy health/Auth/REST/search/detail/original checks passed.
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


## 7. PostgreSQL primary dependency checkpoint — 2026-10-16

The migrated DLR workload uses Oracle PostgreSQL `dlr_primary` as the primary data plane. Local GoTrue (Auth), local PostgREST (Data API), and the FastAPI compatibility bridge preserve the expected Supabase-compatible API contracts; PostgreSQL listens only on loopback. Canonical database operations live in `zzpsah/postgresql-services/projects/official-letter-intelligence/database-operations/`. See that repository's `docs/DLR-POSTGRES-INTEGRATION-STATUS-2026-10-16.md` and `docs/PROJECT-ONBOARDING.md` for the database dependency boundary and future-project process.

**Earlier verification checkpoint (2026-10-16; superseded by the latest acceptance note below):** 19 public tables, 28 public functions, 18 RLS-enabled tables; 68 letters and 103 processing jobs (99 completed, 4 failed, 0 active). Live queue integrity passed. The full DLR suite passed 377/377 tests. Authenticated login/search/detail/original checks passed; private storage references were absent from detail JSON and unauthenticated search/original access was rejected. Fresh encrypted local/off-site backups both restored to disposable databases with 19 tables and 28 functions. The guarded Ansible deployment passed (17 tasks OK, 2 expected changes, 0 failures). Direct Gemini synthetic text and file checks passed using `gemini-3.5-flash-lite`.

**Earlier release verification passed for the deployed DLR application revision.** One low-confidence source-conflict result and a second record remain flagged for human review. At that earlier snapshot, four jobs were failed (two prior RLS/archive-scope, two network/timeout), and one worker timer run overlapped an API restart. A later authenticated read on 2026-10-16 reports 99 jobs (98 completed, 1 retired, 0 pending/running/failed); the count/status difference was not reconstructed, and no bulk retry was performed. Embeddings remain disabled. Hosted Supabase is not a verified replica, and schema drift/DR sync/failover remain separate gates.


## Latest Phase 6 acceptance checkpoint — 2026-10-16

- Source-subject parsing commit `1470fe17683dfc1b571e5cf526f376d907a9a4ad` is pushed to canonical `main`. Subject matching is single-line bounded and declines to guess when no recognized transition heading follows; the regression test guards against absorbing body text into the subject. Focused tests passed 4/4 and the full suite passed 385/385.
- Authenticated live search, detail and original streaming returned HTTP 200; detail omitted private storage references; unauthenticated search returned HTTP 401. Authenticated archive/restore and important-mark/clear operations passed against one synthetic row in Oracle, and the row was removed afterward.
- Latest authenticated Oracle snapshot: 19 public tables and 28 public functions (prior catalog check); 67 letters, 67 processing rows and 99 jobs (98 completed, 1 retired, 0 pending/running/failed). No job retry or historical-job reconstruction was performed.
- Guarded Ansible deployment completed from canonical `main` at Oracle checkout `40b03d1`: fresh encrypted local/off-site backups succeeded; 19 tasks OK, 4 changed, 0 failed; full suite 385/385 passed before restart. API/Auth/REST, n8n, DLR bridge and public Vercel health/application routes returned HTTP 200 afterward. Authenticated search/detail/original passed, private storage references remained absent, and unauthenticated search returned HTTP 401. The health check needed one retry immediately after restart, then succeeded.
- Hosted Supabase remains a DR candidate, not a verified replica; schema/data drift blocks sync and promotion.
