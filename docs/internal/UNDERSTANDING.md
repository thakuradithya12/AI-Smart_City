# Understanding AI SMART CITY

Prepared 2026-11-18 after reading every section of `docs/internal/AGENTS.md`. This document records understanding and a proposed Day 1 plan only; no implementation or verification commands have been run.

**Update:** The owner subsequently approved Day 1 and supplied binding decisions in [CLARIFICATIONS.md](../CLARIFICATIONS.md). Those decisions supersede any open-question wording or recommended defaults below. Do not ask those questions again. The Day 1 order is now login skeleton, models, then CI.

## 1. Project in my own words

AI SMART CITY is a website for citizens to report civic issues with a photo and confirmed map pin, and follow them through a documented resolution.
Reviewers triage reports and route them to departments; department staff assign field workers, who record before/after evidence and notes.
Supervisors or citizens verify or dispute a claimed resolution; changes are kept in append-only status history and audit records.
AI may suggest a complaint category with confidence for a human reviewer; it must never make routing, closure, priority, or other decisions.
Reports must remain usable when AI or email is unavailable; jurisdiction comes from the confirmed pin and ward boundaries.
The seven-day build is done only with evidence for the in-scope live HTTPS product or explicit limits, passing CI tests/security checks, a successful backup restore, documented privacy and limits, device/accessibility checks, and stranger-usable run/deploy/restore instructions.

## 2. Frozen scope

### In scope (version 1)

1. Accounts with roles; email and password login.
2. Citizen: report (photo, map pin, category, description), see own complaints with a status timeline, confirm or dispute a resolution, cancel before acknowledgement.
3. Triage queue for reviewers; routing to a department from ward and category rules; override with reason.
4. Department inbox: acknowledge, reject or transfer with reason, assign to field worker.
5. Field worker: see assigned tasks only, upload before and after photos and a note, mark work done.
6. Supervisor: verify or dispute; reopen.
7. Admin: manage wards, departments, categories and users through the Django admin.
8. Append-only audit log and status history.
9. Due date per complaint from category (display and overdue badge only).
10. AI slice (Day 5, only if Days 1 to 4 gates passed): category suggestion with confidence shown to the reviewer, plus a documented evaluation.
11. Duplicate flag using a PostGIS distance query (only if time remains).
12. Deployment with HTTPS, CI, backups and a restore test.

### Out of scope

Mobile app, PWA, React, Celery, Redis, Kafka, microservices, SMS, push notifications, SLA escalation chains, multi-city tenant screens, public map, public dashboard, chatbot, IoT, payment, government integrations, phone OTP, social login, multi-language UI, any autonomous AI decision.

`tenant_id` is excluded from v1 code. Multi-city is mentioned only in roadmap docs.

## 3. Inputs from section 0

- Public domain name and server (VM with SSH or PaaS account): **not provided**. Default is local build/test; Day 1 public deployment is blocked until supplied.
- Pilot area centre latitude and longitude: **not provided**. The instruction explicitly says ask and do not guess. This is needed for the pilot area; no value is assumed here.
- Final complaint category list (3 to 6): **not explicitly confirmed**. Section 0 default is pothole, garbage, drainage, streetlight, water_leakage, other. Please confirm or supply the final list.
- College report format or mandated technologies: **not provided**. Section 0 default is none; follow `docs/internal/AGENTS.md`.

## 4. Key rules

### a. Status changes

Every status change must go through `transition(complaint, to_status, actor, reason=None, **data)`. Within one `transaction.atomic()`, it loads the complaint with `select_for_update()`, checks role/transition and required fields, updates status, and writes both a `StatusEvent` and an `AuditEvent`; no other code assigns complaint status.

### b. Work claim and verification

The department/worker's work-done claim is recorded separately in `Resolution` (claimant, claimed time and note). Verification has its own verifier, time, method and outcome fields; a claim does not itself mean verified closure.

### c. Jurisdiction and GPS

The confirmed map pin is tested against ward boundary data to find jurisdiction, and a pin outside supported wards is refused. Raw GPS only says where the report was made; it does not establish responsibility, and the user must confirm the draggable pin.

### d. Photo validation, storage and serving

Accept JPEG, PNG and WebP up to 8 MB; Pillow must verify and then reopen the image, with a pixel cap to reject decompression bombs. Preserve original bytes privately with SHA-256, create an EXIF-free re-encoded display copy, never expose media publicly, and serve evidence through an authenticated view applying the complaint's visibility rules.

### e. Duplicate distance

Use a metre-based PostGIS geography query equivalent to `ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)`, through raw SQL or `RawSQL`, and test known points. Do not use `dwithin` with a metre `D()` object on a geometry field.

### f. AI and worker-off behavior

AI may propose a category and confidence to a reviewer, with low-confidence labeling below a threshold fixed before testing; humans decide and reviewer acceptance/correction is stored. AI must not route, close, or set priority; if its model is missing the feature disables, and if the worker is off report registration still succeeds and triage proceeds without waiting for AI or email.

### g. Cut order and never-cut list

When behind, cut duplicate detection first, then AI integration (retain evaluation if it exists), then extra field screens. Never cut the lifecycle, audit log, deployed site, or transition tests.

### h. End-of-day evidence

For every day, list files, work in small steps, run tests, deploy, show gate evidence, update `docs/CHANGELOG.md`, and tag `day-N`. Day-specific gates are: Day 1 live login page, CI pytest run, and `check --deploy` output; Day 2 a real-phone submission visible with photo/location/ward; Day 3 transition and IDOR tests; Day 4 live lifecycle with four logins; Day 5 live suggestion plus evaluation artifacts or documented dropped slice; Day 6 restore log, scan report and trial bugs; Day 7 fresh-account demo without notes. The task instructions also require command output or screenshot proof for claims of completion.

## 5. Issues and recommended defaults

These are issues in the instructions, not silently resolved decisions. “Question” entries need the student's answer before Day 1 as requested.

| Section | Issue | Recommended default / question |
|---|---|---|
| 0, 9.1, 13 | The pilot centre is required but no radius/shape for the supported pilot area is specified; ward boundaries may be the true extent. | Use supplied ward polygons as the supported area; treat centre coordinates as informational unless a radius is explicitly supplied. Confirm the centre coordinates and source of ward boundaries. |
| 0, 3, 9.6 | Section 0's six-category default conflicts with AI's requirement for a public dataset with only 3–5 classes matching the category list. | Keep all six product categories; omit the optional AI slice unless a defensible 3–5 category subset and compatible licensed dataset are specified. Do not silently reduce categories. |
| 1.1, 2, 9.1 | Core idea says registration never depends on maps being available, while report requirements mandate ward lookup and refusal outside known ward coverage. | Interpret this as no third-party interactive map/tile dependency for submission: allow manual pin coordinates; perform server-side lookup against locally available ward data and clearly report unavailable ward data. Confirm intended behavior if map/ward data itself is unavailable. |
| 1.1, 13 Day 1 | Day 1 gate requires public HTTPS, while section 0 says domain/server details may be missing and default explicitly blocks deployment. | If no server/domain arrives, record deployment as blocked and show local skeleton evidence; do not claim the Day 1 gate passed. |
| 1.1, 13 | “After each step run the tests and the app” is not measurable and can be expensive for every file operation. | Define a step as a coherent feature/configuration change; run its focused tests and startup/smoke check, with full suite at gate. |
| 1.5, 13, user task | AGENTS says commit at every task and tag each day, but this task explicitly permits touching only `docs/internal/UNDERSTANDING.md` and says stop. | For this read-and-understand task, save only the named file and do not commit/tag; resume the repo's commit/tag rule when implementation is authorized. |
| 4, 5 | “Django (current LTS)” is temporally variable and no exact compatible package matrix is stated; Python 3.12 and GeoDjango/system libraries constrain it. | Verify official Django and dependency docs plus compatibility before pinning; record exact tested versions in DECISIONS before writing requirements. |
| 4, 5, 12 | Compose lists a worker from the start, but it is enabled from Day 5; Docker tags must be pinned, yet no tag/update policy is defined. | Define worker as optional Compose profile/service disabled until Day 5; pin tested image tags (including PostGIS and Python base) and document update policy. |
| 4 | Bootstrap “served from static files” and Leaflet are specified without saying whether vendored assets or a package manager/CDN is allowed. CDN use complicates availability/privacy and local-first operation. | Vendor pinned static assets locally and record their versions/licences, subject to verifying distribution terms. |
| 4, 12 | “Free-tier” tile provider, error tracking, uptime monitor and “reputable” are undefined and their terms can change. | Start with OSM standard tiles only within current published usage policy; defer third-party telemetry unless a suitable service and terms are approved/documented. |
| 5, 6 | `public_id` “generated from the primary key” has no concurrency-safe generation specification. | Create row, then assign a deterministic year/sequence value transactionally; decide sequence/year rollover and uniqueness constraint before implementation. |
| 6, 8 | Section 8 puts transition logic in `apps/workflow/services.py` but names the sole status function as `transition`; Day 1 says all models, Day 3 builds state machine. | Put transition implementation in services.py on Day 3; Day 1 may define status fields/models but must not introduce other status-writing paths. |
| 6 | Append-only ORM overrides do not prevent bulk `QuerySet.update()`, raw SQL, or DB-owner changes; optional DB grants are time permitting. | Treat ORM guards plus tests as baseline; use a restricted application DB role and table grants if feasible, document that database owners can still alter data. |
| 6, 9.2 | Original photo is “unchanged” while the user uploads to private storage; no retention, encryption-at-rest, deletion, backup access or storage backend is specified. | Keep originals private with restricted filesystem/object-store access and backup permissions; document retention before launch, and never transform originals. |
| 7, 8 | Role table permits citizen to reply to info requests, while transition table says `info_requested -> in_triage` requires reply or timeout but does not define where reply/message is stored. Admin “any override” is not mapped to explicit transitions. | Store citizen reply as an auditable complaint message/evidence record; admin may only use explicitly supported transitions with mandatory reason and audit record. Confirm whether additional admin transitions are intended. |
| 8 | `submitted -> in_triage` is system-only, but report success requires both statuses; no system actor identity or failure behavior is specified. | Use a null actor/system role for the second transition in the same report transaction and roll back the report if the transition/audit write fails. |
| 8 | `routed -> in_triage` conflates transfer and rejection of responsibility; the new department/rule selection and notification are unspecified. | Require reason and re-run the routing rule for current category/ward, recording the new rule version; no notifications unless separately specified. |
| 8, 9.1 | The state diagram says citizen cancellation through routed, but section 3 says cancel before acknowledgement; these broadly align, but no race handling is described. | Lock the complaint and allow cancellation only if it is still pre-acknowledgement at transition time. |
| 8, 9.3 | “Dispute” appears as supervisor action and citizen action but the transition table only names `reopened`; no distinct dispute outcome or state is defined. | Map dispute to `reopened` with required reason, retaining the resolution outcome and recording actor/method. Confirm if a distinct dispute state is required. |
| 9.1 | Registration requires a map pin and ward lookup, while “registration never depends on maps” is ambiguous between map UI, geocoding, and ward boundary lookup. | Keep pin entry/map tiles client-side optional and do not call external geocoding; use confirmed coordinates plus local ward polygons. Ask how to handle missing local boundary data. |
| 9.2 | “8 MB per file” does not say whether limit applies before or after request parsing, or to display copy. | Enforce upload/request size at proxy and application layers; cap original bytes at 8 MB and constrain re-encoded output too. |
| 9.3, 7 | Reviewer sees all complaints but only “minimal personal data”; exact fields hidden and how filtering by ward interacts with privacy are unspecified. | Hide citizen email and unrelated profile data from reviewer; show only name and complaint facts needed for triage. |
| 9.6 | Public dataset availability/licensing and suitable 3–5 labels may not match civic categories; “small pretrained” and evaluation protocol are not quantified. | Treat Day 5 AI as optional and drop if no clearly licensed, sufficiently representative dataset and time for group-held-out evaluation; report no invented performance. |
| 9.6 | Worker timeout, polling interval, concurrency/locking, retry policy and failed-item handling are unspecified. | Single worker process with short bounded classifier timeout, row locking/atomic claim, no automatic retries beyond a documented single retry; mark terminal failure. |
| 9.7 | Configurable distance and “open” statuses for duplicates are not defined. | Start at 30 metres and 7 days as written; define open as all statuses except verified_closed/rejected/cancelled. |
| 10, 12 | “Rate limiting” has no thresholds; “short HSTS” has no initial duration; CSP is optional; encryption may depend on hosting. | Choose conservative documented limits and short initial HSTS only after HTTPS validation; use host-level encrypted/restricted backups where available. |
| 11 | State-machine parametrization over every role/from/to pair needs fixtures for required data and assertions for refused cases; not specified how exception/DB side-effects are checked. | Build a table-driven test matrix; assert disallowed transitions leave complaint and both logs unchanged. |
| 11, 13 | CI requires `check --deploy`, but production settings may require secrets/domain values unavailable to CI. | Use CI-only dummy secrets and safe test hosts, never production credentials; run deploy checks with production settings and documented test environment. |
| 11 | “Every detail, evidence and action URL” can become a large matrix; precise URL inventory is absent. | Maintain a route inventory and parameterize role/object ownership cases for every object-bearing endpoint. |
| 12, 13 | Day 1 already includes all models/migrations/CI and a public deploy; seven days also require broad workflows, security and real-device testing, solo. | Treat deployment credentials and working PostGIS host as Day 1 prerequisites; strictly apply cut order and document all gates not achieved rather than overclaim. |
| 12 | Deployment script says pull/build/migrate/collect/restart but lacks health check, rollback procedure details and image pinning strategy. | Add health check before traffic switch and retain previous image for rollback; document exact commands in runbook. |
| 12, 14 | A one-day trial with 5–10 people and two real phones is required but no participants, consent process or schedule is supplied. | Arrange consenting testers and device access before Day 6; if unavailable, record the test as not done, do not fabricate results. |
| 13, 14 | Day 7 demands backup demo video and two rehearsals but does not state storage location/privacy or format. | Store only with participant consent and redact personal complaint data; mark absent if no suitable consent/storage is available. |
| 14 | “Every in-scope item works live, or is listed as not delivered” allows a definition-of-done checkbox to pass with core omissions documented, while section 13 says never cut lifecycle/audit/deployment/transitions. | Treat the never-cut items as mandatory; document other omissions in LIMITS and report overall completion honestly as incomplete if required live scope is missing. |
| 15 | Referenced architecture/testing/review/deploy/accessibility/documentation skills are said to exist in a different student's Claude workspace, not this environment; no actual skill paths are provided. | Use available local instructions/tools where present; do not install plugins. Record unavailable skills and perform equivalent manual checks only when implementation is authorized. |
| 15 | The optional plugins “run hooks on the codebase”, but approval/impact and exact permission scopes are not given. | Do not install without the student's explicit agreement, as the file itself says. |
| 16 | Prompt says ask about missing section 0 once “then continue with stated default,” while this user explicitly requires stopping pending approval and answers. | Follow the current explicit user instruction; no Day 1 work until approval and open inputs/questions are answered. |

## 6. Dependencies, image tags and APIs to verify before pinning

No versions are pinned in this document. Verify current official documentation and compatibility for every item below before adding a version or image tag, and record the selected versions/reasons in `docs/DECISIONS.md`.

### Runtime, framework and system packages

- Python 3.12 runtime and `python:3.12-slim` Docker base tag/digest policy.
- Django current LTS, GeoDjango, Django database backend and migration APIs.
- PostgreSQL server version and official `postgis/postgis` image tag; PostGIS extension/version compatibility with Django and GEOS/PROJ.
- OS packages and APIs for GDAL, GEOS, PROJ, PostgreSQL client libraries and `psycopg` (or chosen supported driver).
- Docker Engine and Docker Compose specification/plugin syntax, profiles, health checks, secrets/env handling and named volumes.
- Caddy version/image tag, Caddyfile syntax, automatic HTTPS, reverse-proxy headers and certificate behavior.
- Gunicorn version and Django WSGI worker/configuration.
- WhiteNoise version and static storage/compression API compatible with chosen Django.
- `django-environ` only if chosen; otherwise Python `os.environ` behavior (explicit choice is allowed by AGENTS).

### UI and map

- Bootstrap 5 exact version and local static distribution/licence.
- Leaflet exact version, JavaScript/CSS APIs, marker drag and event behavior.
- OpenStreetMap standard tile usage policy, attribution requirements, caching and request limits; any alternate provider terms before use.
- Browser Geolocation API secure-context requirements, permissions and accuracy fields.
- Any vanilla-JS/browser APIs used for coordinate validation and map fallback.

### Authentication, images and app security

- `django-axes` current compatible version and middleware/authentication-backend/settings APIs, or the documented equivalent selected.
- Django password validator APIs and production security settings, including CSRF, secure cookies, HSTS, `SECURE_PROXY_SSL_HEADER`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `check --deploy`.
- Pillow version and `Image.verify()`, reopen/decode, decompression-bomb limits, EXIF handling and re-encoding APIs.
- Django upload handlers/request size limits, private storage APIs and authenticated file response behavior.
- Rate-limit implementation/API (the stack specifies the requirement but no library or mechanism).
- CSP configuration/API if used.

### Database/geography and domain APIs

- Django GeoDjango geometry fields, spatial lookups, GEOS/GDAL integration, migrations and PostGIS backend APIs.
- PostgreSQL/PostGIS `ST_DWithin`, geography casts, `ST_SetSRID`, `ST_MakePoint` and parameter binding through raw SQL/`RawSQL`; confirm coordinate order is longitude then latitude.
- `transaction.atomic()`, `select_for_update()`, custom model manager/queryset behavior, custom user model and migration ordering.
- Django admin APIs, auth user manager, custom authentication by unique email, and timezone-aware `USE_TZ`/Asia-Kolkata behavior.

### Testing, lint, security scanning and CI

- pytest, pytest-django, factory_boy, and any pytest plugins; Django/PostGIS test database setup.
- ruff command/configuration and supported Python target.
- pip-audit CLI/API and its Python/dependency database behavior.
- bandit CLI/configuration.
- GitHub Actions workflow syntax, runner image labels and PostgreSQL/PostGIS service container tag/health checks; action versions must be verified and pinned per current guidance.
- OWASP ZAP baseline scan command/image tag and staging scan scope.
- Any CI use of `manage.py check --deploy` and required production environment variables.

### Optional AI and operational tools

- PyTorch version compatible with Python 3.12, selected pretrained model/weights and dataset-loading APIs.
- ONNX export API/opset version, ONNX format compatibility, ONNX Runtime CPU package/version and inference APIs.
- Dataset source URLs, licences, terms, class mapping and permitted training use before downloading anything.
- Any CLI/API for backup scheduling, `pg_dump`/restore compatibility, encrypted/restricted storage and restore verification.
- Free-tier terms and current APIs for any selected uptime/error-tracking service; no provider selected yet.
- Locust or k6 only if used; verify version and invocation/API.
- Any package for rate limiting, storage, static asset handling or image processing beyond the stack list must have an explicit decision record before addition.

## 7. Proposed Day 1 plan

This is a plan only. It is not authorization to start Day 1. Exact versions, package contents, and deployment configuration must be settled from current documentation and the missing inputs before pinning.

### Files to create or change, in order

1. `docs/DECISIONS.md` — create concise initial records for verified runtime/dependency/image choices and key architecture decisions.
2. `.env.example` — list required variables with placeholders only; no secrets or real deployment values.
3. `requirements/base.txt` and `requirements/dev.txt` — pinned only after current-documentation and compatibility checks; separate runtime and development/test tooling.
4. `Dockerfile` — Python 3.12 slim plus verified GDAL/GEOS/PROJ/system dependencies.
5. `docker-compose.yml` — local db/web and named PostGIS volume; worker disabled/optional until Day 5, Caddy arrangement documented.
6. `config/__init__.py`, `config/settings/{__init__,base,dev,prod}.py`, `config/urls.py`, `config/wsgi.py` — create settings package with custom user configured before any migration, PostGIS, timezone and secure environment handling.
7. `manage.py` — standard Django command entry point.
8. `apps/accounts/{__init__,apps,models,managers}.py` — custom email-login user and role choices.
9. `apps/geography/{__init__,apps,models}.py` — Department, Ward, Category and RoutingRule.
10. `apps/complaints/{__init__,apps,models}.py` — Complaint, Evidence, StatusEvent and Resolution model definitions; no alternate status mutation path.
11. `apps/audit/{__init__,apps,models}.py` — AuditEvent and append-only ORM guards.
12. `apps/ai_assist/{__init__,apps,models}.py` — AiSuggestion model shell only if Day 1 “all models” is interpreted literally; AI behavior remains gated to Day 5.
13. `apps/{workflow,console}/{__init__,apps}.py` — app registration scaffolding; no Day 3 workflow implementation yet.
14. `config/settings/base.py` — complete installed-app and database/auth configuration after app stubs exist (adjust ordering as needed while keeping custom user before first migration).
15. Initial migrations for all Day 1 models, generated only after settings and model definitions are correct.
16. `templates/registration/login.html`, `templates/base.html`, `static/` local assets as needed — minimal responsive role-login page.
17. `README.md` — local run instructions, current limits and environment setup for the skeleton.
18. `tests/conftest.py` and focused Day 1 tests under `tests/` — custom user creation/email login, model registration/constraints, settings/timezone and login page smoke behavior.
19. `pyproject.toml` — pytest and ruff configuration with verified options.
20. `.github/workflows/ci.yml` — verified/pinned GitHub Actions workflow for lint, pytest, dependency audit and production deploy check against PostGIS service.
21. `docs/CHANGELOG.md` — dated Day 1 work, evidence, next step, and explicit blocked/unblocked gate status.
22. `scripts/deploy.sh`, `Caddyfile`, and `docker-compose.prod.yml` — only if domain/server credentials exist and deploy is within authorized Day 1 work; otherwise list as blocked, do not invent production values.

The file order is a dependency-aware proposal, not a requirement to create empty app trees before their contents. Keep the custom user model configured before creating the initial migration.

### Tests and checks to run during Day 1

- After settings/model skeleton: `python manage.py check`.
- Verify the custom user is configured before migration generation; inspect migration graph and run migrations against the local PostGIS container only after the test database is available.
- Run focused pytest tests for custom user/email login, model import/registration and login view; run `pytest` for the Day 1 suite.
- Run `ruff check .` (and formatter check if configured).
- Run `pip-audit` on the pinned environment.
- Run production settings `python manage.py check --deploy` with CI-only dummy secrets/hosts where needed; save actual command output in gate evidence.
- Build/start the local Compose services and smoke-test the login page; retain command output or screenshot.
- CI must show a successful pytest run against PostGIS and the configured lint, audit and deploy-check jobs.
- If a public deployment is possible, verify the HTTPS login page in a browser and preserve a screenshot/URL as evidence. If the domain/server remains unspecified, explicitly report this gate blocked; do not claim deployment.

### Day 1 gate evidence to show

- Public HTTPS login page screenshot/link (or explicit blocked status tied to missing domain/server).
- GitHub Actions run showing pytest against PostGIS.
- Captured `check --deploy` output from production settings.
- Local app/Compose smoke-test output as supporting evidence.
- Updated `docs/CHANGELOG.md` and `docs/DECISIONS.md`; commit/tag only when carrying out the authorized Day 1 task, not for this read-only understanding task.

## Input status after binding clarification

- Domain/server: none yet; local-only and the public deploy gate is blocked.
- Pilot centre coordinates: still blank in the supplied input. Do not guess or ask again. Hand-drawn ward polygons, when supplied, define supported coverage and use source `hand-drawn, <date>`.
- Categories: confirmed as the six defaults: pothole, garbage, drainage, streetlight, water_leakage, other.
- College requirements: none.
- Ward absence/outside pin: fail closed; no tile/geocoding dependency.
- Dispute: transition to `reopened` with a required reason.
- All other owner decisions are recorded in `docs/CLARIFICATIONS.md`; that document controls where it differs from this understanding snapshot.
