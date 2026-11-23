# AI SMART CITY — Roadmap V2 (agent execution plan)

Prepared 2026-11-23 from a read of the repository snapshot (HEAD `19be9fd`, "feat: refresh civic landing page UI").
Audience: the coding agent working in this repo. Owner: Thakur Adithya Singh (solo, college final-year project).

> **Read this first.** No document can guarantee zero bugs. What this plan provides is (a) every known defect and gap with its evidence, (b) acceptance criteria per task, and (c) rules that make mistakes detectable. You are responsible for proof, not claims.

---

## 0. Operating rules (non-negotiable)

1. **Evidence or it did not happen.** Never write "passes", "fixed" or "verified" unless you ran the command in this session. Record command, exit code, counts and commit SHA in `docs/TEST_REPORT.md`. If you could not run it, write "not verified" and why.
2. **No invention.** Do not invent coordinates, ward boundaries, metrics, dataset licences, library versions, API signatures or file contents. If an input is missing, add it to `docs/DECISIONS_NEEDED.md` and continue with other work.
3. **Verify before pinning.** Before adding or changing any dependency, confirm the exact version exists on the package index (`pip index versions <pkg>` or `pip install --dry-run`) and record the date. Same for GitHub Actions versions and Docker image tags.
4. **Check claims in this file against the code.** Items marked **[VERIFY]** are suspected, not confirmed. Reproduce first. If it is not real, close it with evidence and do not "fix" it.
5. **One task = one commit** with focused tests first (red → green). Commit message: `<task-id>: <summary>`. Never mix tasks.
6. **Do not weaken or delete existing tests** to get green. If a test is wrong, explain why in the commit body.
7. **Status writes go only through `apps/workflow/services.py::transition()`** (or a new audited service in the same module). No `complaint.status = ...` anywhere else. Existing test `test_application_status_assignments_stay_inside_transition_service` must keep passing.
8. **Never edit an applied migration.** Add new ones. Run `makemigrations --check --dry-run` before every commit.
9. **No runtime third-party scripts, styles or fonts** (no Tailwind/Lucide/Google Fonts CDNs). Vendor locally with licence files and recorded hashes. The only allowed external request is map tiles (see D6).
10. **Do not delete user data.** `private_media/` holds 349 original photos plus 349 display copies in the snapshot; six local files were already recorded as orphaned. Never delete or commit them.
11. **Never print or commit secrets.** The snapshot's `.env` holds a real-looking `DJANGO_SECRET_KEY`; treat it as exposed (task 0.3).
12. **Ask, don't guess.** Anything in section 2 (owner decisions) blocks only its dependent tasks.
13. **Task report format** (append to `PROGRESS.md`, max 10 lines): task id, what changed, files, tests added, commands run with results, anything not verified.
14. **Stop conditions:** if a task needs a human decision, a credential, or a physical device, stop that task, log it, move on.

---

## 1. Baseline facts (from the snapshot — re-verify in task 0.1)

- Stack: Django 5.2.19, PostGIS 17-3.7, psycopg 3.3.9, Pillow 13.0.0, WhiteNoise, gunicorn, django-axes 9.0.0, Python 3.12 image. Server-rendered templates, no API, no JS framework.
- Apps: `accounts, geography, complaints, workflow, audit, console, ai_assist`. About 1,550 lines of application code (Bandit's own count in the docs) and 1,447 lines of tests across 9 files; 67 tests reported passing locally (not re-run by the reviewer).
- 12 statuses, a single `TRANSITIONS` table, append-only status/audit events at ORM level, `Complaint.objects.visible_to(user)` on every query.
- 11 live templates: base, home, login, register, logged_out, report, my_complaints, complaint detail, triage_queue, department_inbox, field_tasks, field_task_detail. The public landing page is a static Stitch mockup (`docs/ui_reference/public_landing_civicops/code.html`) served by `apps/console/urls.py::ui_showcase`.
- 47 mockup screens exist in `docs/ui_reference/`; they are references, not implementations.
- Not done (per the repo's own `LIMITS.md`/`PARKING_LOT.md`): public deployment, real pilot ward, AI, remote CI, production backups/monitoring, device acceptance.

---

## 2. Owner decisions required (blocking only their dependents)

| ID | Decision | Blocks | Default if owner says "you choose" |
|---|---|---|---|
| D1 | Server/PaaS + domain for public HTTPS | 8.1 | Single VPS with Docker Compose + Caddy (existing scripts) |
| D2 | Pilot area: centre, authoritative ward polygon(s) with source and effective date | 1.12, 8.1 | Use an open municipal GeoJSON the owner names; keep demo ward labelled synthetic |
| D3 | Retention periods (complaints, photos, accounts) and deletion process | 1.9 | Propose values in `docs/PRIVACY.md`; owner approves before production |
| D4 | Email/SMTP provider (SMS/WhatsApp are out unless owner supplies accounts) | 3.1 | Console backend in dev; SMTP via env in prod |
| D5 | AI data source: owner photos in `ml/data/<category>/` (existing preflight) vs a pretrained model; licence review for either | 4.x | Owner photos only (matches `ml/DATASETS.md` decision of 2026-11-20) |
| D6 | Map tiles: OSM at demo traffic, or a keyed provider | 2.3, 8.1 | OSM with attribution for demo only; re-decide before real traffic |
| D7 | What the public may see (map, counts, status), and location coarsening | 5.2 | Counts and statuses only; no photos, text, names, exact pins |
| D8 | SLA numbers per category and escalation levels | 3.2 | Keep `default_due_hours`; no escalation until set |
| D9 | Translation owner/reviewer for Telugu and Hindi | 7.x | English only until a reviewer exists |
| D10 | Submission cut line and deadline date | scheduling | See section 4 |
| D11 | Formal scope amendment: owner confirms the frozen v1 exclusions in `AGENTS.md` §3 (notifications, public map, multi-language, SLA escalation, API) are lifted for the items in this roadmap | all of phases 3–7 | Not assumed; task 0.2 records it |

---

## 3. Phases and tasks

Size: S ≤ half day, M ≈ 1 day, L = 2+ days (agent time, including tests). Each task lists **Acceptance** (all must hold) and **Depends**.

### Phase 0 — Trustworthy baseline (no features)

**0.1 Reproduce the baseline (S).**
Run `docker compose run --rm checks`, `python manage.py check --deploy --settings=config.settings.prod`, and the production image build. Record exact outputs. Compare with the docs' claims (67 tests, Ruff clean, Bandit 0 findings, pip-audit clean).
*Acceptance:* `docs/TEST_REPORT.md` has a dated entry for the current HEAD, with any discrepancy from earlier claims called out.

**0.2 Scope amendment and docs truth (S).** Depends: D11.
Add a dated section to `docs/CLARIFICATIONS.md` listing exactly which frozen exclusions are lifted. Update `AGENTS.md` §3 and `docs/SPEC.md` "v1 exclusions" to match. Remove the duplicated 2026-11-23 row in `docs/DECISIONS.md`. Fix stale statements (e.g. `docs/ARCHITECTURE.md` says the landing is static; update after 2.1).
*Acceptance:* no document contradicts another about scope; `grep -rn "Out of scope"` shows the amended list.

**0.3 Secrets and repo hygiene (S).**
- Rotate `DJANGO_SECRET_KEY` and the local DB password (the old values were shared in a zip).
- Confirm `.env` is untracked (`git ls-files | grep -c '^.env$'` = 0; `.gitignore` already lists it).
- Delete from the working tree (all untracked or ignored): `stitch_civic_operations_platform (1).zip`, `.uv-cache/`, `.python-runtime/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`. Add `*.zip` to `.gitignore`.
- Add a secrets scan (gitleaks or equivalent; verify availability) to CI and run it once over full history.
*Acceptance:* scan reports no findings or each finding is explained; a fresh `git clone` builds without the removed folders.

**0.4 Git remote and first CI run (S).** Needs owner to create the repo.
Push, fix whatever the first remote run reveals. Verify pinned action versions exist (`checkout@v6`, `setup-python@v5` appear in `ci.yml`; confirm).
*Acceptance:* a green run URL recorded with the commit SHA.

**0.5 Resolve the [VERIFY] list (M).** For each, reproduce with a failing test or a captured command, then fix or close with evidence. Each becomes its own commit.

| # | Suspected defect | How to check |
|---|---|---|
| V1 | Password reset is broken or unstyled: `config/urls.py` includes `django.contrib.auth.urls`, there are no `registration/password_reset_*.html` templates and no `EMAIL_*` settings | Hit `/accounts/password_reset/`, submit an email, observe |
| V2 | Email case-variants create duplicate users: `UserManager` uses `normalize_email` (lowercases the domain only) and `CitizenRegistrationForm` stores `user.email` as typed | Register `A@x.com` then `a@x.com`; try logging in with each |
| V3 | Bootstrap CSS/JS are loaded or vendored but unused (`base.html` loads `bootstrap.min.css`; `site.css` defines its own components) | Remove it, diff screenshots of every page |
| V4 | `WardAdmin` is a plain `ModelAdmin`, so polygons are edited as WKT text | Open `/admin/geography/ward/add/` |
| V5 | Overlapping active wards make `Ward.objects.active_on().filter(boundary__covers=point).first()` non-deterministic | Test with two overlapping polygons |
| V6 | Users see raw category slugs (`water_leakage`) because templates print `category.name` | Render pages |
| V7 | No custom 403/404/500 templates | Trigger each |
| V8 | `Category.default_department` is not used by routing (`active_routing_rule` only reads `RoutingRule`) | `grep -rn default_department apps` |
| V9 | N+1 queries: `complaint.department.users.all` inside loops in `department_inbox.html` and `detail.html`; `resolution.claimed_by` and `message.author` per row | `django_assert_max_num_queries` on each page with 30 complaints |
| V10 | `TRANSITIONS` allows `department_official` for `in_progress → resolved_pending_verification` but `mark_work_done` requires `field_worker` | Read `apps/console/views.py::mark_work_done` |
| V11 | Report photo input has no `accept`/`capture` hints | Inspect rendered HTML |
| V12 | Evidence responses lack cache headers (middleware only sets `no-store` for `text/html`) | `curl -I` an evidence URL |
| V13 | Landing page is read from `docs/ui_reference` at runtime, so production depends on the docs folder | Read `ui_showcase` |

---

### Phase 1 — Backend correctness, integrity, privacy

**1.1 Reassignment after assignment (M).**
Evidence: `supervisor_reassign` requires `can_transition(..., ASSIGNED)`, which is only true from `reopened`. If a worker is unavailable in `assigned` or `in_progress`, nobody can reassign.
Work: add `reassign_complaint(complaint, actor, assignee, reason)` in `apps/workflow/services.py`. Roles: supervisor and department official of the same department, plus admin. Status unchanged, reason 5–500 chars, assignee must be an active field worker in the complaint's department, audit event with before/after, visible in the citizen timeline as a neutral entry (no staff names to citizens unless D-policy says so). Update the field worker's task list; the previous worker loses visibility immediately.
*Acceptance:* tests for each role, wrong department, inactive assignee, terminal statuses (refused), concurrent reassign (row lock), old worker 404 on the task and evidence.

**1.2 Info-request timeout (M).**
Evidence: `transition()` accepts `data["timeout"]` but nothing triggers it.
Work: `manage.py expire_info_requests` (configurable days via env, default decided in `DECISIONS_NEEDED.md`) moving `info_requested → in_triage` with `actor=None`, role `system`, reason "no reply within N days". It never closes or rejects. Idempotent; safe to run twice.
*Acceptance:* freeze-time tests; audit row written; triage reviewer sees a "timed out" marker.

**1.3 Align table, views, permissions (S).** Resolves V10. Decide with the owner whether `department_official` may mark work done; then make `TRANSITIONS`, the view, templates and the matrix test agree.

**1.4 Admin capability definition (M).**
Evidence: `role == "admin"` forces a reason on every transition, but admin appears in the table only for `in_triage → routed/rejected`.
Work: define the minimal admin operations (reassign via 1.1, route/reject, cancel a stuck complaint with reason). Every one is audited as `admin_override`. Update `docs/SPEC.md` and the matrix test.

**1.5 Database-level append-only (M).**
Evidence: append-only is enforced in Python (`AppendOnlyQuerySet`, `save()`/`delete()` overrides) only.
Work: new migration creating PostgreSQL triggers that raise on UPDATE/DELETE for `complaints_statusevent` and `audit_auditevent`. Confirm test teardown still works (pytest-django flush behaviour with triggers) before merging.
*Acceptance:* raw SQL `UPDATE`/`DELETE` fails in a test; `migrate` forwards cleanly on an empty and a populated DB; backup/restore script still restores (re-run `scripts/restore_test.sh`).

**1.6 Accounts: normalisation, verification, abuse limits (L).** Resolves V2.
- Lowercase emails in the form, manager and a case-insensitive unique constraint (migration must handle existing duplicates safely).
- Email verification before a citizen may submit (depends on 3.1 for sending), with expiring single-use tokens.
- Rate limit registration and password reset per IP and per email (reuse the cache-based limiter; fail closed like `report`).
- Admin forms: validate role↔department (staff roles other than admin require a department).
- Password policy: set an explicit minimum length (owner approves number), keep the common-password validator.
*Acceptance:* tests for duplicates, token expiry/reuse, limiter, admin validation.

**1.7 Report throttling review (S).**
Evidence: `report()` counts every POST including invalid ones; 5 per hour per citizen.
Work: make limit and window documented env settings with tested defaults (they already read `REPORT_POST_LIMIT` and `REPORT_POST_WINDOW_SECONDS`); count only POSTs that pass form validation or that reach image processing; add a per-IP ceiling. Keep fail-closed behaviour.

**1.8 Evidence pipeline (M).**
- Downscale the display copy (max long edge is a parameter in settings; propose a value, owner confirms) and add a small thumbnail; keep the original untouched for the hash.
- Serve with `Cache-Control: private, max-age=…` and `X-Content-Type-Options: nosniff`; `Content-Disposition: inline`.
- Document that originals keep EXIF/GPS and are never served; add a test that no route returns an original.
- Evidence kinds: allow up to N citizen photos per report (1.8 supports 2.4).
- Reconcile orphaned files with a **report-only** command `manage.py media_reconcile` (lists, never deletes).
*Acceptance:* tests for size limits, pixel bomb, EXIF stripped in display and thumbnail, headers, authorisation for each role and for deactivated users.

**1.9 Privacy, consent, retention (L).** Depends: D3.
- Publish `docs/PRIVACY.md` and an in-app `/privacy/` page; link it from the consent checkbox (currently the text says "privacy notice" but no notice exists).
- Add `consent_version` to `Complaint` (migration) and store it with `consent_at`.
- Citizen self-service: download my data (JSON) and request deletion of my account and complaints; define what must be retained for audit (anonymise actor names rather than delete audit rows).
- `manage.py purge_expired` driven by D3, dry-run by default.
- Have the owner or college review the notice; do not present it as legal advice.
*Acceptance:* tests for export contents, deletion/anonymisation, purge dry-run and real run, and that audit rows survive.

**1.10 Performance and pagination (M).** Resolves V9.
Paginate every list (triage, department, field, my complaints) with stable ordering and page size setting; add search (public id, description) and filters (status, ward, category, overdue). Fix N+1 with `select_related`/`prefetch_related`; precompute department field-worker lists once per request. Add database indexes (status+due_at, department+status, ward+status, created_at) in a migration after `EXPLAIN` on 5,000 seeded rows.
*Acceptance:* query-count tests per page; recorded `EXPLAIN` before/after in `docs/PERFORMANCE.md`.

**1.11 Category model and labels (S).** Resolves V6, V8.
Add `label` (display), optional `icon`, `is_active`; keep `name` as the stable slug. Remove or use `default_department` (decide; if unused, drop it with a migration). Seed command updated.

**1.12 Real geography tooling (L).** Depends: D2. Resolves V4, V5.
- `manage.py load_wards <geojson> --source "<text>" --effective-from YYYY-MM-DD`: validates geometry (`ST_IsValid`, SRID 4326, coerces to MultiPolygon), refuses overlaps with other active wards, idempotent by name, dry-run flag. No default data.
- Model-level overlap validation plus a DB exclusion constraint if feasible (needs `btree_gist`; verify it is present in the image).
- `GISModelAdmin` (or equivalent) so staff can view the polygon on a map.
- Admin report "categories with no routing rule for ward X".
*Acceptance:* tests for invalid, overlapping, self-intersecting, empty and multi-polygon inputs; known inside/outside points for the owner's real ward recorded in the test.

**1.13 Duplicates: make linking useful (M).**
Currently `link_duplicate` only stores `duplicate_of`. Define and implement: linked report shows "N other reports at this location" to staff; status changes of the primary are shown on linked reports' timelines; optional citizen "me too" confirmation counted once per citizen; linking never hides a report (existing rule). Keep detection rules-first.
*Acceptance:* tests for visibility (citizens see only their own), counts, once-per-citizen, concurrent link.

**1.14 Settings and observability (M).**
- Add `LOGGING` (JSON to stdout), request id, no PII in logs (no emails, descriptions, coordinates).
- `/healthz/` endpoint (DB check, no auth, no data) and use it in compose healthchecks.
- `SESSION_COOKIE_AGE`/idle timeout (owner approves), `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SAMESITE`.
- Custom 400/403/404/500 pages (V7).
- Keep dev vs prod separation; confirm `DJANGO_DEBUG` can never be true in prod settings.

---

### Phase 2 — Frontend and design system

**2.1 Replace the static landing page (M).** Resolves V13.
Build `templates/landing.html` extending `base.html`; real content only (what the service is, how it works, recent public updates via the existing `public_updates.html` data path, sign-in and report buttons). Remove: Tailwind CDN, `lucide@latest`, Google Fonts, inline scripts, `ui_showcase` serving from `docs/`. Move mockups to a dev-only route that is `404` when `DEBUG=False`, or remove the route entirely (recommended).
*Acceptance:* `grep -rniE "cdn\.|unpkg|googleapis|tailwind" templates static --include=*.html --include=*.js --include=*.css` returns nothing outside `static/vendor`; test asserts `/ui-showcase/` is 404 in prod settings; test asserts landing contains no external origins.

**2.2 One design system (M).** Resolves V3.
Single token set in `static/css/` (colours, type scale, spacing, radius), documented in `docs/DESIGN_SYSTEM.md`, derived from `docs/ui_reference/civicops_design_system.md` and the current evergreen/terracotta palette (`site.css`). Remove Bootstrap if V3 confirms it is unused. Self-host fonts (verify the licence file and subset) or use the system font stack.
*Acceptance:* screenshots of every live page before/after at 360, 768 and 1280 px; no visual regression other than intended; page CSS weight recorded.

**2.3 Maps for staff and citizens (L).** Depends: D6.
- Read-only map on complaint detail (marker, ward outline, accuracy circle if `gps_accuracy_m` exists).
- Triage and department list: map toggle showing pins for the current filtered page.
- Field task: "Open in maps" link using a standard URL and a copy-coordinates button.
- Reuse the vendored Leaflet 1.9.4; keep tile-error fallback from `report-map.js`.
- Staff pages must not hot-link tiles heavily; document the tile policy decision.
*Acceptance:* works with tiles blocked (graceful fallback), keyboard-reachable controls, no coordinates rendered for roles that must not see them (field workers see only their assigned items).

**2.4 Report flow upgrade (L).** Resolves V11. Reference: `report_an_issue_guided_flow`.
Guided steps (category → photo(s) → location → details → consent → review), `accept="image/jpeg,image/png,image/webp"` and `capture="environment"` hint, client-side size check and preview, double-submit guard, preserved input on server error, optional landmark/address text field (new model field), up to N photos (1.8), clear emergency notice (keep wording that this is not an emergency service). Server validation stays authoritative.
*Acceptance:* tests for every validation path; manual run on a real Android and iPhone-class device recorded as "verified on <device>" or "not verified".

**2.5 Build the live screens (L, split by role).** Use each mockup in `docs/ui_reference/<name>/code.html` as a *visual reference only*; never copy its Tailwind classes, scripts or sample data. Every screen needs: real view + template + visibility check + empty/error/loading states + tests. Group, in this order:

*Citizen:* `citizen_dashboard_mobile`, `my_complaints_citizen_mobile`, `complaint_details_citizen_mobile`, `resolution_feedback_citizen_mobile` (confirm/dispute), `notifications_citizen_mobile` (needs 3.1), `profile_settings_citizen_mobile`, `account_recovery_civicops_auth` (needs 1.6/3.1), `register_civicops_auth`, `sign_in_civicops_auth`, `help_support_civicops`.
*Field:* `field_dashboard_mobile`, `my_assigned_tasks_field_mobile`, `task_location_map_field_mobile` (2.3), `work_order_execution_field_mobile`, `inspection_form_field_mobile`, `task_history_field_mobile`, `officer_profile_field_mobile`.
*Department:* `department_dashboard_water_sewer`, `complaint_queue_water_sewer`, `complaint_review_water_sewer`, `blocked_tasks_water_sewer`, `completed_work_water_sewer`, `team_management_water_sewer`, `work_orders_water_sewer` (needs decision 2.6).
*Supervisor/QA:* `supervisor_overview_qa`, `resolution_review_queue_supervisor`, `resolution_review_supervisor`, `escalation_review_supervisor_qa`, `audit_workspace_supervisor_qa`, `performance_reports_supervisor_qa` (needs Phase 5).
*Admin:* `city_overview_admin_dashboard`, `complaints_admin_queue`, `departments_admin`, `personnel_zones_admin`, `system_settings_admin`, `audit_logs_admin`, `sla_monitoring_admin` and `escalation_center_admin` (need Phase 3), `analytics_reports_admin` and `geographic_issue_map_admin` (need Phase 5), `work_orders_admin`.
*Public:* `public_issues_map_transparency` (needs D7, Phase 5), `nearby_issues_map_citizen_mobile` (needs D7), `complaint_details_cmp_2026_04182` and `work_order_details_wo_2026_0891` (reference detail pages).

Each screen's PR description must say which mockup it implements and list anything intentionally different.

**2.6 Work orders decision (S).**
The mockups show work orders (`WO-2026-0891`) but the data model has none; the complaint is itself assigned. Decide with the owner: (a) keep complaint = unit of work and re-label mockups, or (b) add a `WorkOrder` model (crew, materials, scheduled window, blocked reason) linked to a complaint. Record in `DECISIONS.md` before building any work-order screen.

**2.7 Accessibility (M).**
Target WCAG 2.2 AA. Add automated checks (verify the tool and version, e.g. axe via Playwright) to CI on every live page; manual keyboard-only pass; screen-reader pass (NVDA or VoiceOver) on report, complaint detail and triage; focus order after errors; `lang` attributes (needed again for Phase 7); touch targets at least 24 CSS px (WCAG 2.2 minimum), 44 px on mobile primary actions; reduced-motion respected (already in CSS).
*Acceptance:* zero serious/critical automated violations; manual checklist saved in `docs/A11Y.md` with date, tool and what was not tested.

**2.8 Content security policy (M).** Depends: 2.1, 2.2.
Strict CSP header from middleware: `default-src 'self'`, scripts/styles self only (nonces if any inline remains), `img-src 'self' data: https://tile.openstreetmap.org` (adjust per D6), `frame-ancestors 'none'`, `base-uri 'self'`, `form-action 'self'`. Start in report-only on staging, then enforce.
*Acceptance:* no CSP violations across a full click-through; test asserts the header; ZAP no longer reports missing CSP.

**2.9 Front-end performance (S).**
Compressed static (WhiteNoise manifest exists), long cache for hashed assets, image dimensions set to avoid layout shift, Lighthouse run on landing, report and detail pages. Record scores and the device/network profile used; do not claim a score without the run.

---

### Phase 3 — Notifications, SLA, background work

**3.1 Notifications (L).** Depends: D4.
- `Notification` model (recipient, event, complaint, created_at, read_at, sent_at, attempts, last_error). Created inside the same transaction as the event, so they cannot be lost.
- In-app inbox (unread badge, mark read).
- Email delivery via `manage.py send_notifications` (bounded batch, retry cap, backoff, idempotent). Dev uses the console backend.
- Events: report received; information requested; routed (citizen sees "assigned to a department", not staff names); work claimed (citizen asked to confirm); verified/closed; reopened; assigned to me (worker); overdue (supervisor).
- Email content contains the public id, status and a link only. No exact location, no description, no photos.
*Acceptance:* tests for each event and recipient set, retry/cap, no duplicates when the command runs twice, no PII in the body, failure does not affect the workflow transaction.

**3.2 SLA model and checks (L).** Depends: D8.
Add priority/severity (reviewer-set, never AI-set), SLA clock that pauses while `info_requested`, `sla_breached_at`, and `manage.py check_sla` that flags breaches and notifies the supervisor. Escalation levels only as the owner defines them. All flags audited. UI: overdue lists and SLA monitoring page.

**3.3 Scheduler (M).**
A single `manage.py run_scheduler` process (compose service `scheduler`) that runs 1.2, 3.1, 3.2 and 1.9 purge on intervals, using a PostgreSQL advisory lock so two instances never double-run. Alternative: host cron; choose one and document. No Celery or Redis unless the owner asks.
*Acceptance:* kill/restart test, overlapping-run test, heartbeat visible on `/healthz/`.

**3.4 Citizen reminders (S).** Remind citizens to confirm or dispute a pending resolution after N days (D8). Never auto-close; silence stays open by design.

---

### Phase 4 — AI assist (human-supervised only)

**4.0 Decision gate (S).** Depends: D5.
Choose and record the data source and licence evidence. Run the existing `ml/dataset_preflight.py` on the owner's `ml/data/`; it must pass before training. No download of public datasets without owner approval (current decision: not to).

**4.1 Inference module (M).**
`apps/ai_assist/inference.py::classify(image_path) -> (label, confidence)` using ONNX Runtime CPU with configurable model path; missing model disables the feature. Verify the runtime version on the package index. Threshold chosen *before* evaluating on held-out data.

**4.2 Worker (M).** Resolves the broken compose reference.
Evidence: `docker-compose*.yml` run `python manage.py run_ai_worker`, which does not exist.
Implement `run_ai_worker`: polls complaints with no `AiSuggestion`, uses `select_for_update(skip_locked=True)`, bounded timeout, one retry, then `failed`. Report creation never waits for it. Until it exists, remove the `worker` service from compose so no one starts a crashing container.

**4.3 Reviewer UI and correction flow (M).**
Show "AI suggestion, not a decision" with label and confidence in the triage view. Reviewer accepts or corrects; store `reviewer_decision` and `corrected_to`; audit. Define what correcting does: category change updates routing input but does not silently recompute `due_at` (state the rule; owner confirms). AI never routes, prioritises, assigns or closes.
*Acceptance:* tests with the worker off, model missing, low confidence (no suggestion shown), unsupported category (`other` shows none), and audit rows.

**4.4 Evaluation (L).**
Group-held-out split from the manifest; per-class precision/recall/F1 and confusion matrix from real runs; model card under `ml/` with provenance, licence, split method, threshold and limits. Scripts reproducible from a clean checkout. **Never write a metric you did not compute.**
If data is insufficient, record "not delivered" in `docs/LIMITS.md` rather than weakening the evaluation.

---

### Phase 5 — Analytics and transparency

**5.1 Operational analytics (L).**
Server-side aggregations scoped by role: counts by status/category/ward, median and 90th-percentile time to acknowledge/resolve/verify, SLA compliance, reopen rate, backlog age. Define each metric in `docs/METRICS.md` (numerator, denominator, exclusions). Charts via a vendored library after licence check, or server-rendered SVG.
*Acceptance:* tests with fixtures where the expected numbers are hand-computed; zero rows and one row cases.

**5.2 Public transparency (L).** Depends: D7.
Public page showing only what D7 permits. Safe defaults: category, ward, status, counts; coordinates coarsened to a grid and suppressed where a cell has fewer than a minimum number of reports; no text, photos, names, ids that map to a person.
*Acceptance:* privacy test that no field outside the allow-list appears in the response; tests for small-cell suppression.

**5.3 Audit viewer and exports (M).**
Filterable, paginated audit/status viewer for admin and supervisor (supervisor limited to own department). CSV export must neutralise formula injection (prefix cells starting `= + - @`).

---

### Phase 6 — API and mobile app (only after the website passes its gates)

**6.1 Versioned JSON API (L).** `/api/v1/` using the same service layer and `visible_to` rules; token or session auth chosen by the owner; rate limits; OpenAPI schema generated from code; no business logic in serializers. Verify any framework version before adding.
**6.2 Flutter client (L).** Citizen reporting with offline queue and retry, field worker task list with before/after photos. Separate repository or `mobile/`. Reuse the Sehat Setu offline patterns only as design ideas, not copied code with different licences.
**6.3 Contract tests (M).** API tests mirror the permission matrix; a stale client must get clear errors.

---

### Phase 7 — Languages (Telugu, Hindi, English)

Depends: D9. Enable Django i18n (`USE_I18N` is already true, `LANGUAGE_CODE` is `en-us`), mark templates and messages, add `locale/` for `te` and `hi`, language switcher, translated category labels (1.11), localised dates/numbers, self-hosted Noto fonts with licence files. A native-reader review is a gate; machine translation alone is not accepted. Test layout with long strings and with Telugu/Devanagari rendering on a real phone.

---

### Phase 8 — Production, security, operations

**8.1 Deploy (L).** Depends: D1, D2, D6.
Follow `docs/RUNBOOK_UBUNTU.md` (not reviewed in this analysis; read it first and correct anything stale). Steps: provision, DNS, `.env` from `.env.example` with `DJANGO_SETTINGS_MODULE=config.settings.prod`, `scripts/deploy.sh`, HTTPS verified, `check --deploy` output saved, HSTS stays at 300 s until stable, then raise stepwise.
*Acceptance:* public URL answers over HTTPS; login, report, route, assign, verify exercised on the live site with accounts created through `createsuperuser`/admin (never `seed_demo` on production).

**8.2 CI hardening (M).** Add jobs: migrations check, tests with coverage threshold (set after the baseline), `collectstatic`, browser end-to-end (Playwright; verify version), accessibility checks (2.7), dependency audit, Bandit, secrets scan, Docker image build. Dependabot or equivalent for pins.

**8.3 Backups (M).** Scheduled `scripts/backup.sh` (systemd timer or cron), off-host encrypted copy (tool chosen by the owner), retention rule, documented RPO/RTO, and a **restore drill from the off-host copy** logged in `docs/`.

**8.4 Monitoring (S).** Uptime check on `/healthz/`; error tracking only if the owner approves a provider's data handling (D-list); otherwise log review procedure in the runbook.

**8.5 Security verification (M).**
- Route inventory test: every URL either requires auth or is in a reviewed allow-list; every object route is covered by an IDOR test per role.
- ZAP baseline against the HTTPS staging target; goal 0 FAIL and every WARN explained.
- Short threat model (`docs/THREAT_MODEL.md`): assets, actors, trust boundaries, mitigations, residual risk.
- Re-run pip-audit and Bandit on the final lock.

**8.6 Load and capacity (M).** Test with a tool whose availability you verify; scenario: citizens browsing and reporting, staff queues. Targets are set with the owner from pilot size. Record environment, numbers and bottlenecks; no unmeasured claims.

**8.7 Data operations (S).** Run `media_reconcile` (1.8) on production; owner decides orphan handling; schedule `purge_expired` after D3.

---

### Phase 9 — Test strategy

- Keep the existing matrix and lifecycle tests; add: reassign, timeout, notifications, SLA, privacy export/deletion, evidence headers, pagination and query counts, CSV injection, CSP, route-inventory authorisation.
- Property-style test of the state machine (every sequence of allowed transitions keeps invariants: closed implies a verification record; no status write outside the service). Verify the library before adding.
- End-to-end (Playwright) for the full four-role lifecycle at a phone viewport and a desktop viewport, plus dispute/reopen/reassign and cancellation.
- Failure injection: storage failure mid-upload, DB failure mid-transition, SMTP down, tiles blocked.
- Report line and branch coverage; do not chase 100%, but every service function and every permission branch needs a test.

---

### Phase 10 — Documentation and portfolio

- `README.md` for humans: what it is, screenshots, quickstart (three commands), architecture diagram (Mermaid), ERD (generated from models), role/permission matrix generated from `TRANSITIONS`, roadmap status.
- Consolidate `docs/`: shrink `PROGRESS.md` into a changelog, keep decisions as dated ADRs, delete contradictions, mark the agent-process documents (`AGENTS.md`, `UNDERSTANDING.md`) as internal.
- A 2-minute demo video and a seeded demo script that uses fresh random passwords.
- Pilot validation (the foundation document's P0): talk to at least a few real users or officials; record questions and findings in `docs/PILOT_NOTES.md`. Do not fabricate testimonials or usage numbers.
- Resume bullets with only measured, reproducible numbers (tests, coverage, response times you measured).
- A "defend your design" sheet: why modular monolith, why PostGIS geography for distance, why separate claim and verification, why append-only audit, what you would change at city scale.

---

## 4. Recommended order and cut line

Sequence: **0 → 1.1–1.5, 1.8–1.12, 1.14 → 2.1–2.4, 2.8 → 3.1–3.3 → 4 → 8.1–8.3 → 10 → rest.**

Because the owner's deadline is close (confirm the date in D10), a submission cut is:

1. Phase 0 complete.
2. Backend: 1.1, 1.2, 1.5, 1.8, 1.9 (policy + consent page + export/delete), 1.10, 1.11, 1.12, 1.14.
3. Frontend: 2.1, 2.2, 2.3 (detail + field), 2.4, 2.8, custom error pages, accessibility pass on report/detail/triage.
4. 3.1 (email + in-app) and 3.3 minimum.
5. Phase 4 only if D5 yields usable data in time; otherwise record "not delivered" honestly and rename claims in the README so the project does not advertise AI it does not have.
6. 8.1–8.3, then Phase 10.

Everything else (analytics, public map, API/Flutter, translations, work-order screens) is post-submission and must be labelled as roadmap, not delivered.

---

## 5. Definition of done (project level)

- All tasks in the chosen cut are merged with evidence recorded; every **[VERIFY]** item is closed (fixed or disproved).
- Full test suite, Ruff, Bandit, pip-audit, secrets scan, migrations check green on the remote CI for the exact release commit.
- `check --deploy` passes with only documented, justified warnings.
- Live HTTPS site exercised end-to-end by the owner on two real phones and one desktop; results recorded, untested devices marked unverified.
- Backup restored from the off-host copy at least once, log saved.
- No external runtime assets except the approved tile source; CSP enforced.
- `docs/LIMITS.md` lists, truthfully, everything not delivered.
