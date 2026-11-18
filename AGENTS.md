# AGENTS.md — AI SMART CITY (7-day, solo, website-first build)

Place this file in the repository root. If your agent reads `CLAUDE.md`, copy it to that name too.
It is the single source of truth for what to build, how, and when it counts as done.

---

## 0. Inputs the human must give you before Day 1

Do not invent these. If missing, ask once, then continue with the stated default.

| Input | Default if not given |
| --- | --- |
| Public domain name and server (VM with SSH, or PaaS account) | Build and test locally; Day 1 deploy is blocked until given |
| Pilot area centre latitude and longitude | Ask. Do not guess a location |
| Final complaint category list (3 to 6) | pothole, garbage, drainage, streetlight, water_leakage, other |
| College report format or mandated technologies | None; follow this file |

---

## 1. Your role and operating rules

You are a senior software engineer building this project with one student who works alone and has about 7 days. Quality of a working, deployed, tested core matters more than breadth.

1. **Work in small verified steps.** After each step run the tests and the app. Never say "done" without showing the command output or a screenshot that proves it.
2. **Stay inside scope.** Section 3 lists what is in and out. If something not listed seems useful, add it to `docs/PARKING_LOT.md` and keep going.
3. **Never fabricate.** No invented metrics, accuracy numbers, datasets, licences, users or pilot results. If a number does not exist yet, leave a clearly marked placeholder.
4. **Ask when a decision is outside this file**, in one short question with your recommended default. Do not stall on small choices.
5. **Keep two logs:** `PROGRESS.md` (date, what was done, evidence, what is next) and `docs/DECISIONS.md` (one short entry per technical decision: choice, reason, alternative rejected).
6. **Commit at least at the end of every task**, with a clear message. Tag the end of each day `day-N`. Never commit secrets, `.env`, media files or model weights over 50 MB.
7. **If a gate fails, cut scope; do not extend the day.** Use the cut order in section 13.
8. **Explain nothing the student cannot defend in a viva.** Prefer plain, readable Django over clever abstractions. Add a one-line comment above every non-obvious rule (permissions, state machine, geospatial queries).
9. **Verify versions and APIs against current documentation** before pinning dependencies. Do not rely on memory for package versions, Docker image tags or library APIs. Record what you pinned in `docs/DECISIONS.md`.

---

## 2. Product

AI SMART CITY is a website where citizens report civic problems (potholes, garbage, drainage, streetlights, water leakage) with a photo and a map pin. A reviewer triages and routes each complaint to the right department. The department assigns a field worker, who records before and after photos. A supervisor or the citizen verifies the fix. Every change is recorded in an append-only audit log. AI only suggests a category to the reviewer; people make every decision.

Core ideas that must be visible in the code:

- Complaint registration never depends on AI, maps or email being available.
- A department's claim "work done" is stored separately from the verification outcome.
- GPS says where a report was made, not who is responsible; the confirmed map pin plus ward boundary data decides jurisdiction.
- The complaint state machine is the only way status changes.

---

## 3. Scope (frozen)

### In scope (version 1, website)

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

### Out of scope (do not build)

Mobile app, PWA, React, Celery, Redis, Kafka, microservices, SMS, push notifications, SLA escalation chains, multi-city tenant screens, public map, public dashboard, chatbot, IoT, payment, government integrations, phone OTP, social login, multi-language UI, any autonomous AI decision.

Keep `tenant_id` out of v1 code. Mention multi-city only in the roadmap docs.

---

## 4. Stack decisions (locked; verify versions per rule 9)

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django (current LTS), GeoDjango |
| Database | PostgreSQL with PostGIS (official `postgis/postgis` image, pinned tag) |
| UI | Django templates, Bootstrap 5 served from static files, small vanilla JS; responsive and mobile-first |
| Map | Leaflet with OpenStreetMap tiles plus attribution; check tile usage terms and switch to a free-tier tile provider if traffic requires |
| Config | `django-environ` or plain `os.environ`; no secrets in code |
| Static files | WhiteNoise |
| App server | gunicorn |
| Reverse proxy and HTTPS | Caddy (automatic certificates) |
| Containers | Docker Compose: `db`, `web`, `worker`, `caddy` |
| Auth hardening | `django-axes` or equivalent for login lockout; Django password validators |
| Image handling | Pillow |
| Tests | pytest, pytest-django, factory_boy |
| Lint and format | ruff |
| Security checks | `pip-audit`, `bandit`, `manage.py check --deploy`, OWASP ZAP baseline scan against staging |
| CI | GitHub Actions with a PostGIS service container |
| AI (Day 5) | PyTorch fine-tuning in `ml/`, export to ONNX, inference with ONNX Runtime on CPU |

Choose these over alternatives for speed and defensibility. Do not add libraries without a line in `docs/DECISIONS.md`.

---

## 5. Repository layout

```
.
├── AGENTS.md
├── PROGRESS.md
├── README.md                 # what it is, how to run, how to deploy, known limits
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile                # python:3.12-slim + GDAL, GEOS, PROJ system packages
├── Caddyfile
├── .env.example              # every variable, no real values
├── pyproject.toml            # ruff, pytest config
├── requirements/             # base.txt, dev.txt (pinned)
├── manage.py
├── config/                   # settings (base, dev, prod), urls, wsgi
├── apps/
│   ├── accounts/             # custom User, roles
│   ├── geography/            # Ward, Department, Category, RoutingRule
│   ├── complaints/           # Complaint, Evidence, StatusEvent, forms, citizen views
│   ├── workflow/             # transitions.py (state machine), services.py, permissions.py
│   ├── audit/                # AuditEvent (append-only)
│   ├── console/              # triage, department, field, supervisor views
│   └── ai_assist/            # classifier interface, AiSuggestion, worker command
├── templates/  static/
├── ml/                       # train.py, evaluate.py, DATASETS.md, metrics/, export_onnx.py
├── scripts/                  # backup.sh, restore_test.sh, deploy.sh
├── tests/
└── docs/                     # SPEC.md, DECISIONS.md, PARKING_LOT.md, ARCHITECTURE.md, USER_GUIDE.md, LIMITS.md, TEST_REPORT.md
```

Business rules live in `apps/workflow/services.py`, never in views or templates, so an app or API can reuse them later.

---

## 6. Data model

Create `AUTH_USER_MODEL = "accounts.User"` **before the first migration**. Use `USE_TZ = True` and `TIME_ZONE = "Asia/Kolkata"`.

| Model | Fields (minimum) | Notes |
| --- | --- | --- |
| `User` | email (unique, login), name, role, department (FK, null), is_active | Roles: `citizen`, `triage_reviewer`, `department_official`, `supervisor`, `field_worker`, `admin` |
| `Ward` | name, boundary (MultiPolygon, SRID 4326), source, effective_from, effective_to | Record where the boundary came from |
| `Department` | name | |
| `Category` | name, default_due_hours, default_department (FK, null), is_safety_critical | Safety-critical flag shows a visible warning to the reviewer |
| `RoutingRule` | category, ward (null = all), department, version, effective_from | Every routing decision stores the rule it used |
| `Complaint` | public_id, citizen (FK), category (FK), suggested/final category, description, location (Point, SRID 4326), gps_accuracy_m (null), ward (FK, null), department (FK, null), status, assignee (FK, null), due_at, consent_at, created_at, duplicate_of (FK self, null) | `public_id` like `ASC-2026-000001`, generated from the primary key |
| `Evidence` | complaint, kind (`citizen`, `field_before`, `field_after`), original_path, display_path, sha256, uploaded_by, uploaded_at | Original kept private and unchanged |
| `StatusEvent` | complaint, from_status, to_status, actor, role, reason, created_at | Append-only |
| `Resolution` | complaint, claimed_by, claimed_at, claim_note, verified_by (null), verified_at (null), method, outcome | Claim and verification are separate columns |
| `AuditEvent` | actor (null for system), role, action, object_type, object_id, before (JSON), after (JSON), reason, ip, created_at | Append-only |
| `AiSuggestion` | complaint, label, confidence, model_version, status (`pending`, `done`, `failed`), reviewer_decision (`accepted`, `corrected`, null), corrected_to | Day 5 |

Append-only rule for `StatusEvent` and `AuditEvent`: override `save()` to refuse updates and `delete()` to raise; add a test that tries both. If time allows, also revoke UPDATE and DELETE for the application's database role on those tables.

Location handling: store `location` as a geometry point in SRID 4326. For metre-based duplicate queries use `ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)` through a raw or `RawSQL` expression, and cover it with a test using two known points. Do not use `dwithin` with a metre `D()` object on a geometry field.

---

## 7. Roles and permissions

Enforce on the server in one place (`apps/workflow/permissions.py`) and reuse it in every view. Default is deny.

| Role | May see | May do |
| --- | --- | --- |
| citizen | Own complaints only | Submit, cancel before acknowledgement, reply to information requests, confirm or dispute resolution |
| triage_reviewer | All complaints; minimal personal data (no email) | Edit category, route, request information, reject, mark duplicate |
| department_official | Complaints routed to their department | Acknowledge, reject or transfer with reason, assign within department |
| supervisor | Their department's complaints and field workers | Assign, reassign, verify, dispute, reopen |
| field_worker | Only tasks assigned to them | Start work, upload evidence, mark done |
| admin | Configuration and all data | Manage wards, departments, categories, rules, users; any override must carry a reason and is flagged in the audit log |

Query scoping: implement `Complaint.objects.visible_to(user)` and use it everywhere. A request for a complaint the user may not see returns 404, not 403.

---

## 8. State machine (single source of truth)

All status changes go through one function:

```python
transition(complaint, to_status, actor, reason=None, **data)
```

Inside one `transaction.atomic()` it: loads the complaint with `select_for_update()`, checks the transition is allowed for the actor's role, checks required fields, updates the complaint, writes a `StatusEvent` and an `AuditEvent`. No other code assigns `complaint.status`. Add a test that scans the codebase for direct assignments outside this module.

| From | To | Allowed roles | Required |
| --- | --- | --- | --- |
| submitted | in_triage | system | none |
| in_triage | info_requested | triage_reviewer | message |
| info_requested | in_triage | citizen, system (timeout) | reply or timeout |
| in_triage | routed | triage_reviewer, admin | department, rule version |
| in_triage | rejected | triage_reviewer, admin | reason code |
| routed | acknowledged | department_official, supervisor | none |
| routed | in_triage | department_official, supervisor | reason (transfer or reject responsibility) |
| acknowledged | assigned | department_official, supervisor | assignee in same department |
| assigned | in_progress | field_worker | none |
| in_progress | resolved_pending_verification | field_worker, department_official | at least one `field_after` evidence and a note |
| resolved_pending_verification | verified_closed | supervisor, citizen | method |
| resolved_pending_verification | reopened | supervisor, citizen | reason |
| reopened | assigned | supervisor | assignee |
| submitted, in_triage, routed | cancelled | citizen | not yet acknowledged |

Final states: `verified_closed`, `rejected`, `cancelled`. Citizen silence never closes a complaint. Any pair not in this table must be refused.

---

## 9. Feature requirements

### 9.1 Citizen report
- Form fields: category, description (optional), photo (required), location.
- Map: Leaflet map; "Use my location" button (browser geolocation needs HTTPS) places a draggable pin; the citizen must confirm the pin. Store raw GPS accuracy if provided.
- Ward lookup: find the ward containing the pin. If none, refuse with a clear message that the location is outside the supported area.
- Consent checkbox with a short privacy notice; store `consent_at`.
- Emergency notice on the page: the platform is not an emergency service.
- On success: create the complaint and evidence in one transaction, status `submitted` then `in_triage`, return the `public_id`. This must work even if the AI worker and email are off.

### 9.2 Evidence handling
- Allow JPEG, PNG, WebP; maximum 8 MB per file; validate with Pillow (`verify()` then reopen), reject decompression bombs by capping pixel count.
- Store the original bytes unchanged in private storage with the SHA-256 hash. Create a re-encoded display copy with EXIF removed.
- Never expose the media directory publicly. Serve files through an authenticated view that applies the same visibility rules as the complaint.

### 9.3 Triage, department, field and supervisor consoles
- Server-rendered pages with filters by status and ward, and a clear status badge and due date (overdue shown).
- Each page shows only actions the current role may perform for that status; the server still enforces it.
- Reject, transfer, reopen and dispute require a reason.

### 9.4 Audit and history
- Show a timeline on every complaint (status events plus evidence) to those who may see the complaint.
- A read-only audit page for `admin` listing events with filters.

### 9.5 Due date
`due_at = created_at + category.default_due_hours`. Display only. No timers, emails or escalation in v1.

### 9.6 AI slice (Day 5, optional gate)
- Training code in `ml/`: fine-tune a small pretrained image classifier on a public dataset with 3 to 5 classes matching the category list. Record every dataset, source and licence in `ml/DATASETS.md`. Do not use data with unclear licences.
- Split the data so near-identical images cannot appear in both train and test (split by source or collection session, not random image).
- Evaluate on the held-out test set: per-class precision, recall, F1, confusion matrix image, and a short note on limits. Save under `ml/metrics/`. Report results exactly as measured.
- Inference: `apps/ai_assist/classifier.py` exposes `classify(image_path) -> (label, confidence)`, loading an ONNX model from a path in the environment. If the model file is missing, the feature turns itself off.
- A `worker` container runs `python manage.py run_ai_worker`, a simple loop that picks `pending` suggestions, calls the classifier with a timeout, and writes `done` or `failed`. Registration never waits for it.
- The reviewer sees the suggestion, its confidence and "AI suggestion, not a decision". Below a threshold fixed before testing and saved in `ml/THRESHOLDS.md`, show "low confidence". The reviewer's accept or correction is stored.
- Never use AI output to route, close, or set priority automatically.

### 9.7 Duplicate flag (optional)
When triaging, show other open complaints in the same category within a configurable distance (start with 30 m) in the last 7 days. The reviewer may link one as `duplicate_of`. Never delete or hide the citizen's own report.

---

## 10. Security and privacy requirements

- `DEBUG = False` in production; `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set from the environment; secrets only from the environment.
- Behind Caddy set `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, secure session and CSRF cookies; enable HSTS with a short duration first. `python manage.py check --deploy` must pass with the production settings.
- Login lockout and rate limiting on login and on the report endpoint.
- Password validators on; no default or shared passwords in production.
- All object access through `visible_to`; add tests for cross-user and cross-department access (IDOR) on every detail, evidence and action URL.
- Output escaping stays on; no `|safe` on user text; CSP header if time allows.
- Collect only email, name and complaint data. No phone numbers, no government IDs.
- Demo accounts exist only on dev and the demo server. Create them with random passwords printed once by `seed_demo`; disable or rotate them after the demo.
- Backups are encrypted or stored with restricted access; the restore test is a deliverable.

---

## 11. Testing requirements

Write tests as you build, not at the end.

1. **State machine:** a parametrised test over every (from, to, role) combination that asserts exactly the allowed set in section 8 succeeds and everything else is refused, and that each success writes a `StatusEvent` and an `AuditEvent`.
2. **Permissions and IDOR:** citizen A cannot read or change citizen B's complaint; an official cannot see another department; a field worker cannot see unassigned tasks; evidence URLs obey the same rules.
3. **Append-only:** updating or deleting `StatusEvent` or `AuditEvent` fails.
4. **Geography:** point inside a ward is found; point outside is refused; duplicate-distance query returns the expected pair and not a far one.
5. **Evidence:** wrong type, oversized file and a corrupt image are rejected; hash stored; EXIF removed from the display copy.
6. **End to end:** one test that runs the full lifecycle with four users from submission to `verified_closed`, and one that runs the dispute and reopen path.
7. **Failure:** with the AI worker stopped, a complaint is still created and triaged.

CI must run lint, tests, `pip-audit` and `check --deploy` on every push. Keep a short `docs/TEST_REPORT.md` with the final numbers from real runs.

---

## 12. Deployment and operations

- Day 1: deploy a skeleton (login page) to a public HTTPS URL, then redeploy at the end of every day. Use `scripts/deploy.sh`: pull, build, migrate, collect static, restart.
- Compose services: `db` (PostGIS with a named volume), `web` (gunicorn), `worker` (AI loop, enabled from Day 5), `caddy`.
- Environment variables are documented in `.env.example`.
- `scripts/backup.sh` runs `pg_dump` on a schedule and copies media; `scripts/restore_test.sh` restores into a clean database and runs sanity queries. Run it once and save the log in `docs/`.
- Add an uptime check and error tracking (free tier of any reputable service) and write a one-page runbook in the README: deploy, roll back to the previous image, restore.
- Keep the server's firewall to ports 22, 80 and 443 only; SSH keys only.

---

## 13. Day-by-day plan with gates

Each day: read this section, list the files you will create, build in small steps, run tests, deploy, show evidence, update `PROGRESS.md`, tag `day-N`.

| Day | Build | Gate (show evidence) |
| --- | --- | --- |
| 1 | Repo, Docker, Django with PostGIS, custom User, all models and migrations, seed command, role login, CI, **public HTTPS deploy of the skeleton** | Live login page; `pytest` runs in CI; `check --deploy` output |
| 2 | Citizen report flow with map pin, ward lookup, evidence handling, "my complaints" with timeline | A complaint submitted from a real phone appears with photo, location and ward |
| 3 | State machine, permissions, triage queue, department inbox, assign, reject or transfer, audit entries | Transition and IDOR tests pass |
| 4 | Field updates, mark done, verification, dispute and reopen, Django admin setup | Full lifecycle on the live site with four logins |
| 5 | AI slice (about 8 hours), duplicate flag if time remains | Suggestion visible in the live triage queue plus `ml/metrics/`, or the slice is dropped and logged |
| 6 | Hardening: security checks, rate limits, backup and restore test, mobile and browser checks, one-day trial with 5 to 10 people | Restore log; scan report; list of trial bugs fixed or documented |
| 7 | No new features. README, architecture, workflow, user guide, limits, test report, demo rehearsal twice, backup demo video | Fresh-account demo run without notes |

Cut order when behind: duplicate flag, then the AI integration (keep the evaluation if it exists), then extra field screens. Never cut: the lifecycle, the audit log, the deployed site, or the transition tests.

---

## 14. Definition of done

All must have evidence in the repository or in `docs/TEST_REPORT.md`:

- [ ] Every item in section 3 "In scope" works on the live HTTPS site, or is listed in `docs/LIMITS.md` as not delivered.
- [ ] Section 11 tests pass in CI.
- [ ] `check --deploy` passes; dependency and static scans reviewed; no secrets in Git history.
- [ ] Backup restored successfully once, with a saved log.
- [ ] Privacy notice and consent live; retention rule written in the README.
- [ ] Tested on at least two real phones and one desktop; keyboard and contrast check on the report and triage pages.
- [ ] If the AI slice was delivered: `ml/metrics/` with per-class results, `ml/DATASETS.md`, `ml/THRESHOLDS.md`, limits stated. If not: say so in `docs/LIMITS.md`.
- [ ] `docs/LIMITS.md` states: no official integration, small data, GPS and photos are imperfect evidence, AI assists a human only.
- [ ] README lets a stranger run, deploy and restore the system.

---

## 15. Tooling: what to use, and what not to

Use only what helps; extra tooling costs time.

**Skills already available in the student's Claude workspace (engineering and design plugins)**

| When | Use |
| --- | --- |
| Day 1 and any big choice | architecture skill, to write short decision records |
| Day 3 onward | testing-strategy skill, to check test coverage against section 11 |
| Before each merge | code-review skill on the day's diff |
| Day 1 and Day 6 | deploy-checklist skill before deploying |
| Day 6 | accessibility-review skill on the report and triage pages |
| Day 7 | documentation skill for README, runbook and user guide |

**Optional plugins from the Anthropic directory (install only if the student agrees; they run hooks on the codebase)**

- Security Guidance (official): warns about risky patterns as code is written and reviews the diff when a task stops.
- Code Review (official): multi-agent review of a pull request.
- Claude Security (official): deeper vulnerability scan; run once on Day 6.

Do not install unvetted community plugins that request broad permissions on a project this size.

**Non-plugin tools:** ruff, pytest, pip-audit, bandit, OWASP ZAP baseline scan, Locust or k6 for a small load check, Caddy, GitHub Actions, a free error-tracking service and a free uptime monitor. Check each free tier's terms before relying on it.

---

## 16. Prompts the student pastes (one per day)

**Day N prompt:**
> Read AGENTS.md fully. Do Day N only, nothing from later days. First list the files you will create or change. Work in small steps, run the tests after each, and deploy at the end. Stop at the Day N gate, show me the evidence, update PROGRESS.md and docs/DECISIONS.md, commit and tag `day-N`. If something is missing from section 0, ask me once before starting.

**Review prompt (end of Days 3, 4, 6):**
> Review today's diff as a strict reviewer: permission holes, direct status assignments outside `transition()`, missing tests for section 11, secrets, and anything outside the section 3 scope. List findings by severity and fix the high ones.

**Final prompt (Day 7):**
> Do not add features. Check every item in section 14 against the repository and the live site. Produce a table of item, status and evidence link. Mark anything unproven as not done and add it to docs/LIMITS.md.
