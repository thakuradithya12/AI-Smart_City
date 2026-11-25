# Test report

## 2026-11-25 — deployment settings and DATABASE_URL parsing

- `config.settings.base` now reads `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS`, while retaining the existing `DJANGO_*`/Postgres Compose aliases. The URL parser uses only the Python standard library, percent-decodes credentials and database name, carries connection query options such as `sslmode=require`, and always selects Django's PostGIS engine.
- `python -m pytest -q tests/test_database_config.py` — 6 passed. Python syntax compilation and `git diff --check` passed. Full Django settings loading, Neon connectivity/extension privileges, and `check --deploy` are not yet verified.

## 2026-11-25 — phone-based demo accounts and walkthrough

- Added `docs/DEMO_SCRIPT.md`, a timed role-by-role flow from citizen submission through independent `verified_closed` verification and an admin audit review. Extended local-only `seed_demo` to create synthetic phone logins for citizen, triage, department, field worker, supervisor and admin; new passwords remain random and are printed once. Added a seed idempotence/account test.
- Python syntax compilation, README workflow synchronization, and `git diff --check` pass. Focused pytest could not collect because Django is not installed in the host Python. Seed behavior and CI are not verified.

## 2026-11-25 — human-written README and changelog

- Replaced `README.md` with a product overview, generated workflow status table, role summary, local setup/check commands, and current limits (AI off, synthetic demo geography, local console email, and owner-supplied deployment inputs). Reworked `PROGRESS.md` as a concise dated changelog.
- Added a test asserting the README workflow table stays synchronized with `docs/WORKFLOW.md`. `python scripts/sync_readme_workflow.py --check`, Python syntax compilation, and focused pytest passed (1 passed). Django-backed tests and CI on this commit are not verified.

## 2026-11-25 — Ubuntu operations runbook

- Updated `docs/RUNBOOK_UBUNTU.md` with owner-supplied D1 prerequisites, the complete `.env.example` variable groups, first production startup, local-only demo loading, Caddy/HTTPS, hourly scheduler-driven retention, backups, restore rehearsal, updates and rollback.
- Documentation-only change; no tests added. `git diff --check` passes. No VM, domain, public TLS, backup or restore operation was run; those remain unverified.

## 2026-11-25 — route authorisation inventory

- Added a resolver-wide route inventory. Public routes must appear on a named allow-list; private app routes must be listed with the source-level role/object guard and carry `login_required`; Django admin routes must be wrapped by its staff permission gate. Any new unclassified route fails the test.
- `python -m py_compile tests/test_route_authorisation.py` and `git diff --check` pass. Focused pytest could not collect because Django is not installed in the host Python (`ModuleNotFoundError: django`); runtime behavior and CI are not verified.

## 2026-11-25 — phase1 promotion

- GitHub Actions run [45601898000](https://github.com/thakuradithya12/AI-Smart_City/actions/runs/45601898000) succeeded on `6de99703e478dea3f5defbda3c2bc5e7965071ce`. The owner refreshed CI artifacts on this exact SHA: 201 pytest tests passed, all checks passed, Bandit reported no issues, and pip-audit reported no known vulnerabilities.
- Fast-forwarded `master` to the tested SHA and pushed tag `verified-phase1-2` at that same SHA. This report entry is a follow-up documentation change and is not itself CI-verified.

## 2026-11-25 — CI dashboard fixture correction

- Run [45569758547](https://github.com/thakuradithya12/AI-Smart_City/actions/runs/45569758547) on `e6960b38d66bf11bc9ef46cfac8ac31ab13b6342` failed: 1 failed, 200 passed. The only failure was `tests/test_role_dashboards.py::test_role_dashboard_uses_role_scoped_complaints_and_quick_links[citizen-Your reports-My reports]` (assertion at the recent-complaints visibility check): the fixture assigned every operational complaint to the citizen, while expecting her to see only her own complaint. Corrected test data to use a separate reporter for operational complaints and reserve the citizen account for `DASH-CITIZEN`; production visibility logic is unchanged. This corrects an invalid test fixture, not an authorization behavior.
- `python -m py_compile tests/test_role_dashboards.py` and `git diff --check` pass. Runtime pytest and the CI fix are not verified until the owner refreshes `_ci` files.

## 2026-11-25 — E.5 audit workspace and safe CSV

- Added admin and department-scoped supervisor audit pages, filters, pagination and CSV export. Added formula-cell neutralisation and tests for role access, supervisor department scope, CSV output and cells beginning with `=`, `+`, `-` and `@`.
- `python -m py_compile` and `git diff --check` pass. Runtime tests are not verified because the host lacks Django and Docker cannot reach its engine.

## 2026-11-25 — E.4 reduced role dashboards

- Added role-specific dashboard summaries and shortcuts for five roles, using `Complaint.objects.visible_to(user)` for complaint counts and recent records. Existing list/detail/action screens remain the linked role workflows.
- Added a parametrised five-role test for dashboard metrics and cross-role complaint exclusion. `python -m py_compile` and `git diff --check` pass; runtime test is not verified because Django is unavailable and the Docker engine cannot be reached.

## 2026-11-25 — E.3 citizen verification reminder

- Implemented a one-time citizen reminder three days after each work-completion claim, queued through the scheduled command and reusing the email/in-app delivery path. The service only writes `Notification`; status and resolution remain unchanged.
- Added a boundary/idempotency/no-auto-close test. `python -m py_compile` and `git diff --check` pass; runtime pytest is not verified because Django is not installed and Docker is unavailable.

## 2026-11-25 — E.2 D14 rolling session test

- Added a test that checks a later authenticated request refreshes the stored 12-hour expiry and cookie max-age. The settings already matched D14 (`43200`, `SESSION_SAVE_EVERY_REQUEST=True`).
- `python -m py_compile tests/test_observability.py` — exit 0; `git diff --check` — exit 0. Runtime Django test is not verified in this host; Docker engine is unavailable.

## 2026-11-25 — E.1 privacy and retention

- Added a privacy notice/export/deletion flow, versioned consent, account anonymisation that preserves audit actor references, and a PostGIS-backed retention command for expired complaint details and evidence. Added coverage for phone-number export, complaint visibility, account anonymisation, retention cleanup, the 24-month inactive-account rule, consent version and overlapping-run lock behavior.
- `python -m py_compile` on changed Python modules and tests — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_privacy.py tests/test_workflow_invariants.py -q` — exit 1 during collection (`ModuleNotFoundError: No module named 'django'`). `docker compose run --rm checks` cannot connect to `npipe:////./pipe/dockerDesktopLinuxEngine`; runtime tests, migrations and PostgreSQL locking are not verified.

## 2026-11-25 — C workflow lock

- Added generated workflow documentation and invariant tests for reachability, terminal states, pre-acknowledgement cancellation, separate claim/verification fields, citizen silence, and generated-document freshness.
- `python scripts/generate_workflow_doc.py --check` — exit 0; `python -m py_compile scripts/generate_workflow_doc.py tests/test_workflow_invariants.py` — exit 0; `git diff --check` — exit 0.
- `docker compose run --rm checks` — not run: Docker could not connect to `npipe:////./pipe/dockerDesktopLinuxEngine`. Host Python has no Django, so runtime tests are not verified.

## 2026-11-25 — phase1 CI promotion evidence

- GitHub Actions run [45562646639](https://github.com/thakuradithya12/AI-Smart_City/actions/runs/45562646639) — **success** for commit `b91531009a681f5ab293f0d1aa3a6c6b7a633630` (`tests: include login route in error page URL config`). Owner-provided `_ci/runs.txt` and `_ci/checks.txt` agree on the successful run; checks report no pending migrations, `179 passed`, Ruff and Bandit clean, and pip-audit found no known vulnerabilities.
- This green run verifies the code and tests on that SHA, including accounts migration `0005`, the CI migration-state check, and the error-page test URL fixture. It does not verify deployment, physical-device acceptance, or work outside that commit.


## 2026-11-25 — CI pytest notification retry accounting

- Run #26 showed notification delivery tests with `attempts == 0` after a send and four sends despite a three-attempt limit. Both send result paths omitted `attempts` from `save(update_fields=...)`; the counter increment therefore was not persisted. Added it to success and failure updates.
- `python -m py_compile apps/notifications/management/commands/send_notifications.py` — exit 0; focused pytest exited 2 during collection because Django is not installed locally; `git diff --check` — exit 0. Runtime behavior is pending CI.

## 2026-11-25 — CI pytest information-request fixture

- Run #26 could not set up either expiry test because `day4_setup` was module-local to `test_day4_workflow.py`. Added a local, minimal expiry fixture.
- `python -m py_compile tests/test_info_request_expiry.py` — exit 0; pytest collection exited 2 because Django is not installed locally; `git diff --check` — exit 0. Runtime behavior is pending CI.

## 2026-11-25 — CI pytest console supervisor fixture

- Run #26 reported `KeyError: 'supervisor'` in the complaint-detail query-count test because its shared console fixture omitted the supervisor account. Added a department-scoped supervisor to that fixture.
- `python -m py_compile tests/test_console_workflow.py` — exit 0; `git diff --check` — exit 0. Runtime pytest is pending CI.

## 2026-11-25 — CI pytest Axes identifier canonicalization

- Run #26's phone-format and legacy-email-case lockout tests reached the expected Axes lockout, then authenticated successfully using a variant spelling because Axes keyed attempts by the raw submitted username. Configured `AXES_USERNAME_CALLABLE` to reuse login's phone normalizer and case-fold legacy email identifiers; the Axes 9.0 API was checked against its official documentation.
- `python -m py_compile apps/accounts/backends.py config/settings/base.py` — exit 0; `git diff --check` — exit 0; focused pytest exited 2 during collection because Django is unavailable locally. CI verification is required.

## 2026-11-25 — CI pytest in-app-only notification test

- The no-email notification test reused a citizen fixture with a non-empty email. Clear the address before invoking the command so the test exercises the intended email-less path.
- `python -m py_compile tests/test_notifications.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest development email backend assertion

- Run #26 showed the test's `settings.EMAIL_BACKEND` read as Django's expected `locmem` test backend. Updated the test to inspect `config.settings.dev.EMAIL_BACKEND`, the actual development default, rather than Django's test-time override.
- `python -m py_compile tests/test_notifications.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest idempotent ward import

- Run #26 showed the second `load_wards` invocation failing `full_clean()` with duplicate `id` and `name` errors. Validation used a new instance carrying the existing primary key; now it validates the persisted instance that will be updated.
- `python -m py_compile apps/geography/management/commands/load_wards.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest configurable map tile assertion

- Run #26's map accessibility test expected the obsolete hardcoded OSM tile URL in JavaScript. The implementation correctly reads D6's configurable `map_tile_url` from the template; updated the assertion to cover that contract.
- `python -m py_compile tests/test_accessibility.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest reassignment test ID length

- Run #26's department-official reassignment cases exceeded the complaint `public_id` field's 32-character maximum while constructing test records. Replaced generated IDs with short role/status identifiers.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest admin reassignment audit assertion

- Run #26's admin reassignments correctly included `operation: complaint_reassigned` in the `admin_override` audit payload, while the test expected only `assignee_id`. Updated the test to assert the full intentional audit record.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest triage pagination fixture

- Run #26's pagination assertion expected only `PAGE-T-` IDs from an unfiltered triage queue. The queue correctly includes other active statuses; filtered the test to `in_triage` for that case.
- `python -m py_compile tests/test_console_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

## 2026-11-25 — CI pytest streamed evidence response test

- Run #26 reported a closed database connection in the multi-role `FileResponse` test. The test closes each streamed response between requests, triggering request-finished connection cleanup inside the default database transaction. Changed it to transactional DB mode so subsequent role requests can reconnect; this diagnosis awaits CI confirmation.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

## 2026-11-25 — CI run #25 error-template URL fix

- The supplied pytest output reports four custom error-page failures: `NoReverseMatch: Reverse for 'home' not found` while rendering templates. `tests.error_urls` overrides the root URLConf but did not provide the named `home` route used by the shared error templates.
- Added a minimal test-only `home` route. `python -m py_compile tests/error_urls.py` — exit 0; `git diff --check` — exit 0. `python -m pytest tests/test_error_pages.py::test_custom_error_templates_render -q` — exit 4 during collection because Django is not installed locally; behavior awaits CI verification.
- Also marked the two public landing tests that access the database for recent status events with `django_db`. `python -m py_compile tests/test_error_pages.py` — exit 0; `git diff --check` — exit 0; pytest is unavailable locally without Django.

## 2026-11-25 — CI run #24, pytest startup failure

- The owner-provided log for commit `b5ad417` shows pytest exits during `pytest_load_initial_conftests` while `django.setup()` populates `INSTALLED_APPS`. Exact exception: `django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library ... Is GDAL installed?` at Django's installed `django/contrib/gis/gdal/libgdal.py:64`; this is a runner system-library omission, before test collection.
- Added a CI apt install step for `binutils gdal-bin libgdal-dev libgeos-dev libproj-dev`, matching the Dockerfile. CI database config matches Django settings: host `127.0.0.1`, port `5432`, with the PostGIS service exposing `5432:5432`.
- The fix has not yet been exercised by a new CI run. The workflow should proceed past pytest startup; pip-audit and `check --deploy` will run if pytest exits successfully.

## 2026-11-23 — ROADMAP_V2 task 2.4

- Added report flow tests for rendered wizard/photo controls, optional landmark persistence, the 160-character server-side limit, and preservation of description/landmark/coordinates after ward validation errors.
- `python -m py_compile apps/complaints/forms.py apps/complaints/views.py apps/complaints/models.py apps/complaints/migrations/0005_complaint_landmark.py tests/test_day2_reporting.py` — exit 0.
- `node --check static/js/report-flow.js` and `node --check static/js/report-map.js` — exit 0 for each.
- `python -m pytest tests/test_day2_reporting.py -k 'guided_flow or saves_optional_landmark or landmark_over_limit or photo_input' -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`); Django behavior is not verified.
- `git diff --check` — exit 0. Manual run on Android and iPhone-class hardware remains not verified; no physical devices were available.

## 2026-11-23 — ROADMAP_V2 task 2.8 blocked by D6

- Did not add CSP middleware because the roadmap says `img-src` must match the owner-selected tile provider; D6 is unresolved. The exact provider/traffic question and OSM demo recommendation are recorded in `docs/DECISIONS_NEEDED.md`.
- `git push origin phase1` for task 2.4 — exit 0; remote branch advanced from `5ec4072` to `6b97f7b`. Remote CI was not inspected.
- `git diff --check` — exit 0; no application test applies to this documentation-only blocker.

## 2026-11-23 — ROADMAP_V2 task 2.8 after owner decisions

- Implemented exact D6 CSP directives; development defaults to report-only, production enforces unless `CSP_REPORT_ONLY=True`. `MAP_TILE_URL` is configurable, defaults to OSM canonical tile URL, and is rendered into the report map.
- Added CSP header mode, production default, map URL, 12-hour rolling session and provisional retention-setting tests.
- `python -m py_compile config/middleware.py config/settings/base.py config/settings/prod.py apps/complaints/views.py tests/test_observability.py tests/test_day2_reporting.py` — exit 0.
- `python -m pytest tests/test_observability.py tests/test_day2_reporting.py -k 'csp or retention or idle_session or configured_tile_url' -q` — exit 1 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same reason.
- `node --check static/js/report-map.js` — exit 0. `docker compose config -q` — exit 0. `git diff --check` — exit 0. `python -m ruff check ...` — exit 1 (`No module named ruff`).
- `rg -n --pcre2 '<script(?![^>]*\\bsrc=)|<style\\b|\\sstyle=' templates static -g '!static/vendor/**' -g '!*.map'` — exit 1, no inline script/style tags or style attributes found in application templates/static files.
- Browser click-through and ZAP with enforced CSP remain unverified: Django is unavailable to run the site locally; no browser scan was performed.
- OSM heavy-production-use limitation and all owner decisions are recorded in `docs/LIMITS.md` and `docs/DECISIONS.md`.

## 2026-11-23 — ROADMAP_V2 task 3.1

- Added transactional, deduplicated notification creation for report receipt, information requests, routing, work claimed, verified/closed, reopened and field-worker assignment/reassignment. Added overdue-to-department-supervisor notification service for the following SLA task.
- Added private in-app inbox, unread badge and mark-read POST action; email command processes at most 500 rows, retries up to three times with increasing delay, skips email-less users while preserving in-app notices, and stores only exception class names.
- Added tests for every transition recipient, overdue department scoping, inbox IDOR, report-transition rollback, message contents, retry cap/idempotency and SMTP failure isolation.
- `python -m py_compile apps/notifications/apps.py apps/notifications/models.py apps/notifications/services.py apps/notifications/views.py apps/notifications/urls.py apps/notifications/context_processors.py apps/notifications/admin.py apps/notifications/management/commands/send_notifications.py apps/notifications/migrations/0001_initial.py apps/workflow/services.py config/settings/base.py config/settings/prod.py config/urls.py tests/test_notifications.py tests/test_observability.py` — exit 0.
- `docker compose config -q` — exit 0. `git diff --check` — exit 0. `python -m ruff check apps/notifications apps/workflow/services.py config/settings/base.py config/settings/prod.py config/urls.py tests/test_notifications.py tests/test_observability.py` — exit 1 (`No module named ruff`).
- `python -m pytest tests/test_notifications.py tests/test_day4_workflow.py tests/test_observability.py -q` — exit 1 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same reason.
- Runtime migration, inbox/email behavior and end-to-end workflow remain unverified in this workspace.

## 2026-11-23 — ROADMAP_V2 task 3.3 (implementation in progress)

- Added a single-process scheduler protected by a session-scoped PostgreSQL advisory lock, periodic jobs, graceful unlock on normal exit, and a shared heartbeat read by `/healthz/`. Compose includes the scheduler in development and production.
- `check_sla` is supplied by task 3.2. `purge_expired` remains a dependency on the privacy task 1.9 work. PostgreSQL overlap and process kill/restart acceptance remain unverified.
- `python -m py_compile apps/scheduler/apps.py apps/scheduler/models.py apps/scheduler/migrations/0001_initial.py apps/scheduler/management/commands/run_scheduler.py config/views.py config/settings/base.py tests/test_scheduler.py tests/test_observability.py` — exit 0.
- `docker compose config -q` — exit 0. `git diff --check` — exit 0.
- `python -m pytest tests/test_scheduler.py tests/test_observability.py -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). PostgreSQL overlap and process kill/restart integration tests remain unverified because the Docker engine is unavailable.

## 2026-11-23 — ROADMAP_V2 task 3.2

- Added a reviewer-set priority field/service with reasoned audit entries, pause/resume of due time while information is requested, an idempotent audited SLA breach marker, and supervisor in-app notifications. The marker never changes complaint status and no escalation chain is implemented under D8.
- Added tests for priority permissions/audit, pause/resume duration, SLA idempotency, supervisor notification, and paused/final states.
- `python -m py_compile apps/complaints/models.py apps/complaints/migrations/0006_complaint_sla_fields.py apps/complaints/management/commands/check_sla.py apps/workflow/services.py tests/test_sla.py` — exit 0.
- `python -m pytest tests/test_sla.py tests/test_notifications.py tests/test_day4_workflow.py -q` — exit 1 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` is likewise unavailable for that reason. PostgreSQL/Docker integration checks were not run.

## 2026-11-23 — ROADMAP_V2 task 3.4 decision record

- No reminder code was added because the roadmap requires an owner-selected delay and D8 did not set one. `docs/DECISIONS_NEEDED.md` records the exact question and a 3-day, one-reminder recommendation.

## Static risk notes for unverified Phase 0 commits

These notes are based on the named `git show` diffs. No runtime verification is implied. Any item marked **not confirmed** needs a later executable test or owner/environment evidence.

### V1 — `204d1f0` password reset

- **Files/behavior:** `.env.example`, `config/settings/{base,dev,prod}.py`, reset templates, `tests/test_accounts.py`; adds Django password-reset UI, development console email, and production SMTP configuration read from environment variables.
- **Migration:** No.
- **Risk:** A malformed/missing SMTP environment may prevent delivery; new phone-only citizen accounts have no email recovery path. No credentials appear in the diff. The generic done page says instructions were sent. **Not confirmed:** actual enumeration behavior/runtime delivery; the test diff focuses on a legacy staff account and did not run.

### V2 — `9066970` email normalization

- **Files/behavior:** `apps/accounts/models.py`, migration `0003_user_email_case_insensitive_unique.py`, `tests/test_accounts.py`; trims/lowercases manager-created email identifiers and adds `LOWER(email)` uniqueness.
- **Migration:** Yes. Existing case-insensitive collision groups raise `RuntimeError` before row updates; it does not merge accounts. Unique emails are lowercased. Reverse data operation is `RunPython.noop`, so the lowercase transformations are **not reversible**; reversing schema constraint alone cannot restore original casing.
- **Risk:** Deploy is blocked if legacy collision groups exist and requires owner cleanup. **Not confirmed:** test coverage for `A@x.com`/`a@x.com` registration and login behavior; migration tests/current database collision state were not confirmed from the diff and no test ran.

### V3 — `715ce36` Bootstrap use review

- **Files/behavior:** `PROGRESS.md`, `docs/TEST_REPORT.md`; no application behavior change. The recorded source review says base loads Bootstrap CSS and live templates use `.card` and `.badge`.
- **Migration:** No.
- **Risk:** Removing Bootstrap later could change layout. **Not confirmed:** independent grep/test evidence in this session; commit changes only record the conclusion and contain no grep output.

### V4 — `0504b53` GIS ward admin

- **Files/behavior:** `apps/geography/admin.py`, `tests/test_geography_admin.py`; WardAdmin changes from `ModelAdmin` to `GISModelAdmin` for polygon editing.
- **Migration:** No.
- **Risk:** Admin widget behavior depends on GIS-capable Django deployment configuration. **Not confirmed:** admin page/widget runtime behavior; added test was not run.

### V5 — `8620490` overlapping active wards

- **Files/behavior:** `apps/geography/services.py`, `apps/complaints/views.py`, `tests/test_day2_reporting.py`; ward lookup raises validation error when two active boundaries cover a pin.
- **Migration:** No.
- **Risk:** Citizen submission is refused with “This pin is covered by multiple active wards. Please contact support while the service area is reviewed.” No admin alert, log, or resolution workflow is added in this diff; support must identify overlap separately. **Not confirmed:** actual rendered error, logging/admin visibility, and test runtime.

### V6 — `6d6e3c6` category labels

- **Files/behavior:** `apps/geography/models.py`, complaint/console/home templates, `apps/console/urls.py`, `tests/test_geography_admin.py`; adds a computed `display_label` property that replaces underscores and title-cases the stored name, and switches render sites to it.
- **Migration:** No; it is a property, not a database field, so existing rows need no data default. **Not confirmed:** `seed_demo` runtime behavior; the diff does not edit the seed command.
- **Risk:** Acronyms/brand capitalization and multiword labels may be displayed mechanically; stored slugs remain unchanged.

### V7 — `1b72e72` custom error pages

- **Files/behavior:** four error templates, `tests/error_urls.py`, `tests/test_error_pages.py`; adds custom 400/403/404/500 rendering.
- **Migration:** No.
- **Risk:** Template errors or configured handler wiring could interfere with error responses. **Not confirmed:** production handler invocation or test results; the commit adds tests but they did not run.

### V8 — `0020030` category-default routing (reverted in f071b46)

- **Files/behavior:** `apps/workflow/services.py`, `docs/SPEC.md`, `tests/test_console_workflow.py`; routing prefers an active `RoutingRule`, otherwise uses `Category.default_department` when configured.
- **Migration:** No.
- **Audit/version behavior:** The fallback passes `rule_version=0` and `routing_source="category_default"` through `transition()`. `transition()` rejects only a missing (`None`) rule version, so zero is accepted; the status/audit payload records `routing_rule_version: 0`, and the separate routing audit records source `category_default` and version `0`. If neither rule nor category default exists, routing raises `ValidationError` and refuses.
- **Risk:** Version zero is a reserved sentinel, not a persisted rule version; consumers that assume every routed complaint references a real `RoutingRule` could misinterpret it. This is explicitly documented in the routing audit, but downstream consumers were not inspected. **Not confirmed:** transition/service integration runtime and full audit persistence; test was not run.

### V9 — `f2e6cb6` query scaling

- **Files/behavior:** complaint/console views, complaint/department templates, `tests/test_console_workflow.py`; preloads department workers and complaint related objects/messages to reduce per-row lookups.
- **Migration:** No.
- **Risk:** Prefetch/select-related changes may affect missing/null relationship cases or query ordering; query-count expectations may be backend-sensitive. **Not confirmed:** measured query counts or page output; tests did not run.

### V11 — `89c14c1` report photo hints

- **Files/behavior:** `apps/complaints/forms.py`, `tests/test_day2_reporting.py`; adds browser `accept` and camera `capture` hints to file input.
- **Migration:** No.
- **Risk:** These are client hints, not server-side validation; browser behavior varies. **Not confirmed:** rendered attributes at runtime; test did not run.

### V12 — `13223da` evidence response headers

- **Files/behavior:** `apps/complaints/views.py`, `tests/test_day2_reporting.py`; adds private `max-age=300`, `nosniff`, inline disposition and a display-path-only assertion.
- **Migration:** No.
- **Risk:** Private caching retains sensitive display images in an authorized user's browser cache for up to five minutes. **Not confirmed:** tests for owner, other citizen, assigned worker, unassigned worker, deactivated user, and absence of any original-file route; the committed test only constructs a citizen-owned complaint and checks headers/path access, and it did not run.

### V13 — `0c9327b` landing archive decoupling

- **Files/behavior:** `apps/console/urls.py`, `templates/landing.html`, `static/css/site.css`, `tests/test_error_pages.py`; homepage renders a Django template, authenticated requests go to dashboard, showcase URLs are removed.
- **Migration:** No.
- **Risk:** Landing template links or route reverse names may break; public updates depend on status-event data. **Not confirmed:** production-settings 404, all landing links resolving, no external origins, or content privacy assertions; the added test did not run.

### 0.3 — `d7f41bd` local hygiene and secret scan workflow

- **Files/behavior:** `.github/workflows/ci.yml`, `.gitignore`, docs; configures full-history checkout and Gitleaks Action v3, ignores ZIP files, and records local secret rotation/hygiene.
- **Migration:** No.
- **Risk:** CI may fail because action configuration/permissions or history scanning differs from assumptions. Local PostgreSQL password rotation and full-history scan were not completed. **Not confirmed:** actual key/DB rotation state, Gitleaks findings, or workflow execution.

### 0.4 — `eb3a32e` remote/CI records

- **Files/behavior:** `docs/DECISIONS_NEEDED.md`, `docs/DECISIONS.md`, `docs/TEST_REPORT.md`, `PROGRESS.md`; records missing remote and action-tag claims; no workflow behavior change in this commit.
- **Migration:** No.
- **Risk:** CI cannot be evaluated until an owner-controlled remote exists. The documentation cites official release pages for checkout v6.0.0 and setup-python v5.6.0, but their availability was not independently checked in this static review. **Not confirmed:** current action tag availability, remote configuration, or CI run.

## 2026-11-23 — ROADMAP_V2 Phase 0.1 current-HEAD baseline

**Code under test:** `61c37fa1e2aed79423969c5e59418c75d8afc3f4` (captured before this report edit). No checks below passed in this session; Docker/Python environment access was unavailable.

| Command | Exit | Exact observed result |
| --- | ---: | --- |
| `docker compose run --rm checks` | 1 | Exact stdout/stderr: `permission denied while trying to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` |
| `python --version` | 0 | `Python 3.15.0` (not the repository's Python 3.12 runtime) |
| `python manage.py check --deploy --settings=config.settings.prod` | 1 | Traceback ends `ModuleNotFoundError: No module named 'django'` |
| `.python-runtime\python.exe` existence check | n/a | `PYTHON_312_RUNTIME_NOT_FOUND` |
| `docker compose build web` | 1 | Exact stdout/stderr: ` Image ai-smart_city-web Building` followed by `open C:\Users\thaku\.docker\buildx\.lock: Access is denied.` |

**Counts:** pytest/Ruff/Bandit/pip-audit and migration results: not run; Docker image build: not built. The older 67-test and static-scan results below are historical and do not verify this HEAD. No remote or public deployment check was possible.

## 2026-11-23 — ROADMAP_V2 Phase 0.3 hygiene and secret handling

**Code under test before this documentation update:** `7c717bf783a40aa7adae949b17eff64800d62405`.

| Check/action | Result | Evidence |
| --- | --- | --- |
| `.env` tracking check | Passed | `git ls-files --error-unmatch .env` exited 1 (not tracked); `.env` exists and was not printed or staged. |
| Django key rotation | Completed locally | `DJANGO_SECRET_KEY` regenerated in `.env` using 64 random bytes; generated value was not printed. |
| PostgreSQL role password rotation | Not verified | `localhost:5432` connection check failed; Docker API unavailable. Did not change only the env value and leave the existing database volume mismatched. |
| Cache/archive cleanup | Completed | Removed `.uv-cache/`, `.python-runtime/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, and the named untracked ZIP. `private_media/` remains present. |
| Full-history secret scan | Not verified | No `gitleaks`, `trufflehog`, or `git-secrets` executable is installed; no Git remote exists. CI now checks out full history and invokes Gitleaks Action v3. |
| Secret scan action version | Source-verified | Official `gitleaks/gitleaks-action` README/releases were checked 2026-11-23; v3 exists and uses Node 24. No CI run is claimed. |

## 2026-11-23 — ROADMAP_V2 Phase 0.4 remote and CI

| Check | Result | Evidence |
| --- | --- | --- |
| Configured Git remotes | None | `git remote -v` produced no output (exit 0). No push or remote CI run was attempted. |
| Existing action tags | Source-verified | Official release pages confirm `actions/checkout@v6.0.0` and `actions/setup-python@v5.6.0` on 2026-11-23. |
| Green Actions run | Not verified | Requires owner-controlled GitHub repository URL and authenticated remote setup; see `docs/DECISIONS_NEEDED.md`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V1 password reset

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `config/urls.py` includes `django.contrib.auth.urls`; `templates/registration/` had only `logged_out.html` and `login.html`; `rg` found no email settings. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_accounts.py -k password_reset` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Added styled reset form/done/confirm/complete/email templates, safe dev console email, production SMTP environment settings and a focused legacy-staff reset test. No provider credentials were added. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V2 legacy email uniqueness

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `UserManager._create_user()` called `normalize_email()`, which only normalizes the domain; the new-citizen form has no email field because accounts are phone-based. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_accounts.py -k email_accounts` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Lowercase and trim legacy manager emails; added an atomic-safe preflight data migration and case-insensitive database uniqueness; added a focused duplicate test. Migration application and current-data collision state are not verified. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V3 Bootstrap use

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Closed as not unused | `templates/base.html` loads `vendor/bootstrap/bootstrap.min.css`; live templates use `.card` and `.badge`; Bootstrap's `.card` flex layout remains in effect because `site.css` does not override `display`. `site.css` styles those components further. No Bootstrap JS is loaded. |
| Change | None | Removing the stylesheet would alter component layout; therefore no asset or page change is justified by this suspicion. No screenshot comparison was needed because no UI was changed. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V4 Ward GIS admin

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `Ward.boundary` is `MultiPolygonField(srid=4326)` while `WardAdmin` inherited plain `admin.ModelAdmin`. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_geography_admin.py` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | `WardAdmin` now inherits Django 5.2 `GISModelAdmin`; added a focused inheritance test. API confirmed against official Django 5.2 docs on 2026-11-23. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V5 overlapping wards

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | Report lookup used `active_on().filter(boundary__covers=point).first()` with no ordering or ambiguity check. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_day2_reporting.py -k overlapping_active_wards` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | New `active_ward_for_point()` returns a sole match and refuses multiple active matches; report creation fails closed before image storage. Added an overlapping-ward end-to-end regression test. |
| Syntax check | Passed | Python `ast.parse` parsed `apps/geography/services.py`, `apps/complaints/views.py`, and `tests/test_day2_reporting.py`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V6 category labels

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `rg` found direct `{{ complaint.category.name }}` rendering in home, citizen, triage, department, and field templates; public update context also exposed the raw name. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_geography_admin.py -k display_label` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Added a derived human label (`water_leakage` → `Water Leakage`), used it in live templates, public update context and `Category.__str__`; added model and template-source tests. |
| Static checks | Passed | `rg` found no remaining direct `complaint.category.name` renders; Python `ast.parse` parsed the changed model/view/test files. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V7 error pages

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | The root `templates/` contained none of `400.html`, `403.html`, `404.html`, or `500.html`; `config/urls.py` did not override handlers. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_error_pages.py` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Added four plain-language error templates and a test URLconf/test covering 400, 403, 404 and 500 handler rendering under `DEBUG=False`. |
| Syntax check | Passed | Python `ast.parse` parsed `tests/error_urls.py` and `tests/test_error_pages.py`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V8 category routing default (reverted in f071b46)

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `Category.default_department` appeared in the model/admin/seed, while `active_routing_rule()` and `route_complaint()` only selected `RoutingRule` records. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_console_workflow.py -k category_default_department` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Routing now falls back to `Category.default_department` only when no active ward or global rule exists. The audit records `routing_source=category_default`, `routing_rule_version=0`; a regression test verifies fallback routing and audit fields. |
| Syntax check | Passed | Python `ast.parse` parsed `apps/workflow/services.py` and `tests/test_console_workflow.py`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V9 query scaling

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Partly confirmed | `department_inbox.html` queried `complaint.department.users.all` once per acknowledged complaint. Detail timeline already used `select_related("author")` for messages; this portion of the suspicion was disproved. Resolution actors and detail relations were not eager-loaded. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_console_workflow.py -k query_count` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Department workers are fetched once per request; complaint detail eager-loads resolution actors and complaint relations and prefetches status, messages/authors, and evidence. Added query-growth tests comparing 1 vs 30 inbox rows and 0 vs 30 messages. |
| Static checks | Passed | No `complaint.department.users.all` or redundant per-message query pattern remains; Python `ast.parse` parsed the changed views and query tests. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V10 work-done permission

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `TRANSITIONS` allows both `field_worker` and `department_official`; `mark_work_done` explicitly requires `field_worker`. The roadmap requires the owner to choose. |
| Decision | Blocked on owner | No code changed. Recommended default: field worker only, matching the role matrix and current view. See `docs/DECISIONS_NEEDED.md`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V11 report photo hints

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `ReportForm.photo` used default `ImageField` widget attrs and the report template rendered it directly, with no `accept` or `capture` hints. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_day2_reporting.py -k mobile_file_hints` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Set accepted JPEG/PNG/WebP types and `capture="environment"` on the report photo input; added a rendered-page regression test. |
| Syntax check | Passed | Python `ast.parse` parsed `apps/complaints/forms.py` and `tests/test_day2_reporting.py`. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V12 evidence headers

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `evidence_file()` returned a `FileResponse` without cache, nosniff, or disposition headers. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_day2_reporting.py -k evidence_response` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Change | Implemented, not runtime-verified | Display evidence now has `private, max-age=300`, `X-Content-Type-Options: nosniff`, and `Content-Disposition: inline`. Added a test verifying the endpoint opens only `display_path`; existing visibility checking remains before file access. |

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V13 remove runtime mockup dependency

| Check | Result | Evidence |
| --- | --- | --- |
| Suspected defect reproduction | Confirmed from source | `/` called `ui_showcase()` which read `docs/ui_reference/public_landing_civicops/code.html`; showcase routes read further archive files. |
| Change | Implemented, not runtime-verified | Public `/` renders `templates/landing.html`; authenticated `/` delegates to the dashboard; UI showcase routes and file reads removed. A test points `BASE_DIR` at an empty temporary directory and checks the homepage remains available and the old showcase path is 404. |
| Focused test attempt | Not run to assertions | `python -m pytest -q tests/test_error_pages.py -k public_landing` exited 2 during collection: `ModuleNotFoundError: No module named 'django'`. |
| Syntax and source checks | Passed | Python `ast.parse` accepted the changed Python files; `rg` found no runtime references to `ui_showcase`, `ui_reference`, or `ui-showcase` under `apps`, `templates`, or `config`; `git diff --check` passed. |

## 2026-11-22 — Final local backlog and access-control pass

| Check | Result | Evidence |
| --- | --- | --- |
| v1 spec and remaining-work record | Passed | Added `SPEC.md` and `PARKING_LOT.md`; clarified that the local Hyderabad polygon is synthetic demo geography and not pilot coverage. |
| Duplicate candidates | Passed | Triage complaint detail suggests recent open reports in the same category within 30 m, using geography-distance metres and a seven-day window. A triage reviewer can link a candidate; both reports remain visible and open. |
| Duplicate authorization and audit | Passed | Tests cover near/far, category, age and terminal-state filtering; reviewer linking creates an audit event; citizens cannot invoke the action. |
| Department default-deny | Fixed and tested | Staff accounts without a department now see no unassigned complaints. Department officials and supervisors receive 404 for detail access and zero dashboard rows; regression covers both roles. |
| Full Docker gate | Passed | Migration check `No changes detected`; `67 passed in 67.57s`; Ruff passed; Bandit 0 findings across 1,544 lines; pip-audit found no known vulnerabilities. |
| Production configuration check | Passed with documented warnings | `check --deploy` exited 0; only HSTS subdomain/preload warnings `security.W005` and `security.W021` remain pending a confirmed domain/subdomain policy. |
| Production image and route smoke | Passed | Latest web image rebuilt; `collectstatic` copied 152 files and post-processed 446. `/` returned 200; protected `/workspace/`, `/console/triage/`, and `/console/department/` returned expected signed-out 302 redirects. |
| Release gates requiring external inputs | Still open | No public domain/server, pilot boundaries, rights-cleared AI photos/manifest, Git remote, production monitoring account, or physical-device test environment is configured. See [`PARKING_LOT.md`](PARKING_LOT.md). |

## 2026-11-22 — Citizen-to-department routing visibility

| Check | Result | Evidence |
| --- | --- | --- |
| Live complaint state | Confirmed | `ASC-2026-000001` is `in_triage`, has no department yet, belongs to Demo Ward, and has an active pothole rule targeting Demo Department — Roads. The department dashboard's zero is correct until a triage reviewer routes it. |
| Cross-role routing visibility | Passed | Regression test verifies a department official cannot see an untriaged report, then sees it on both dashboard and inbox immediately after the triage reviewer routes it. |
| Full Docker checks | Passed | `No changes detected`; `61 passed in 75.34s`; Ruff passed; Bandit reported no issues; pip-audit found no known vulnerabilities. |
| Dashboard guidance | Updated | Empty states now explain triage routing, assignment and role-specific visibility. |

## 2026-11-22 — Landing, auth, map and interaction regression

| Check | Result | Evidence |
| --- | --- | --- |
| Full Compose gate | Passed | Migration check `No changes detected`; `61 passed in 100.44s`; Ruff passed; Bandit 0 findings across 1,457 scanned lines; `pip-audit` found no known vulnerabilities. |
| Production static manifest build | Passed | `docker compose up -d --build web`; `collectstatic` copied 152 files and post-processed 446. |
| Login/navigation browser walkthrough | Passed | Landing sign-in reaches login when signed out; sign-in after authentication goes to `/workspace/`; valid local test login reaches the workspace; Sign out returns to the login page. |
| Report map browser walkthrough | Passed locally | Leaflet controls and basemap render; clicking the map changes the coordinate fields. No report was submitted. Geolocation permission was not requested. |
| OpenStreetMap response policy | Passed locally | The prior browser showed 403 blocked tiles. Switched to the canonical tile host and verified the running response header is `strict-origin-when-cross-origin`; map tiles then rendered. This is local browser evidence, not production traffic acceptance. |
| Scope | Partial manual interaction coverage | Landing/auth/citizen navigation and report-map interactions were exercised in-browser. Role-specific complaint actions remain covered by the automated lifecycle tests rather than manual clicks in this walkthrough. |

## 2026-11-21 — Phase 6 local acceptance

**Verified code commit:** `e806d63799ebb374d644b1746465d2ae858769b7` (the uploaded ZIP was untracked and excluded; tracked source was clean).

| Check | Result | Evidence |
| --- | --- | --- |
| Full Compose gate | Passed after commit | `No changes detected`; post-commit rerun on the verified code SHA: `58 passed in 57.76s`; Ruff passed; Bandit: 0 findings across 1,453 lines; pip-audit: no known vulnerabilities. |
| Django production check | Passed with known warnings | Exit 0 using the actual protected Compose key; only `security.W005` and `security.W021` remain for the short HSTS configuration without owner-confirmed domain/subdomain policy. |
| Local route smoke | Passed | `/`, `/ui-showcase/`, `/ui-showcase/citizen_dashboard_mobile/`, `/accounts/login/` returned 200; `/workspace/` redirected to login and then returned 200. |
| Browser/accessibility acceptance | Partial | Local browser showed the landing page, 47-screen showcase index and citizen dashboard mockup. Four new tests cover labelled report/triage controls, error announcements/field links and focus-indicator contrast ≥3:1. Viewport was narrow; no full desktop keyboard, screen-reader or real-device result is claimed. |
| Workflow rehearsal | Automated paths passed | Existing tests cover the four-role lifecycle, separate work claim/verification, dispute/reopen/reassign, cancellation, permissions and transition matrix. No live fresh-account rehearsal was performed. |
| Local code commit | Passed | `e806d63799ebb374d644b1746465d2ae858769b7`; full Compose gate rerun after commit. The uploaded UI ZIP was excluded and remains untracked. |
| Remote CI and push | Not verified | No Git remote is configured, so no remote Actions result or push is claimed. |

The fresh-account rehearsal twice, two-phone and full desktop keyboard/screen-reader checks, public deployment, and production restore/monitoring remain open. See [`PHASE6_ACCEPTANCE.md`](PHASE6_ACCEPTANCE.md) and [`LIMITS.md`](LIMITS.md).

## 2026-11-21 — Phase 5 local operations and security gate

| Check | Result | Evidence |
| --- | --- | --- |
| Integrated Compose suite | Passed | `No changes detected`; final rerun: `54 passed in 64.78s`; Ruff passed; Bandit found no issues across 1,453 lines; pip-audit found no known vulnerabilities. |
| Production settings | Passed with warnings | `check --deploy` using the actual Compose key exited 0. Only `security.W005` and `security.W021` remain for the deliberately short HSTS policy. |
| Production Compose parsing | Passed | Production Compose validation passed with temporary process-only image/domain placeholders. No production deployment was attempted. |
| Caddy config | Passed | `caddy fmt` and `caddy validate` succeeded using `DOMAIN=localhost`; upstream `Server` response header is removed. |
| Browser policy and caching headers | Passed | Main routes returned `Permissions-Policy`, same-origin CORP, and HTML `Cache-Control: no-store`. |
| ZAP passive baseline | Passed with reviewed warnings | Final local HTTP scan, rerun after the Phase 6 accessibility changes: 128 URLs, 0 FAIL, 5 WARN categories, 57 PASS. Reports: [`JSON`](zap-baseline-2026-11-21-final.json) and [`HTML`](zap-baseline-2026-11-21-final.html). This is passive, not an active penetration test or production scan. |
| Caddy proxy behavior | Passed locally | Disposable internal Caddy HTTPS request returned 200, stripped upstream `Server`, and retained `Cache-Control: no-store`. The upstream was the local development server, not production Gunicorn. |
| Secret file ACL and key | Passed locally | `.env` is ignored/untracked with inheritance disabled; only the current user, SYSTEM, and Administrators have Full Control. The weak local key was rotated to a random 64-byte key, never displayed. |
| Git whitespace check | Passed | `git diff --check` returned no whitespace errors. |

The five remaining ZAP warning categories are third-party JavaScript without SRI, cross-domain JavaScript inclusion, inline design-page comments, the development runserver banner, and missing CSP on showcase/error responses. The runserver banner occurs in the local test target; the Caddy proxy check proved that the configured reverse proxy removes the upstream `Server` header. CSP/SRI require bundling and auditing the supplied UI's inline and third-party resources; a permissive policy or guessed integrity hashes would be unsound. The cache-control warning was resolved by setting `no-store` on HTML, and the final scan no longer reports cacheable content or COEP. No finding was confirmed exploitable by this passive scan. `tests/test_day2_reporting.py` covers report throttling; django-axes provides login lockout. Public HTTPS and production-edge enforcement remain unverified.

## 2026-11-21 — Local Docker verification

**Code under test:** current worktree after commit `97433e4`, including the public CivicOps landing/gallery route and local fixes to its tests/template. This is not a GitHub Actions result and no final release commit is claimed.

| Check | Result | Evidence |
| --- | --- | --- |
| Docker build/start | Passed | `docker compose up -d --build db web`; PostGIS healthy and web started. |
| Migration consistency | Passed | Checks container: `No changes detected`. |
| pytest | Passed | `38 passed in 64.17s`. |
| Ruff | Passed | `All checks passed!`. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Django production deploy check | Passed with documented warnings | Exit 0; warnings `security.W005` (HSTS subdomains) and `security.W021` (HSTS preload) remain intentionally unset pending a confirmed stable domain. |
| HTTP smoke | Passed | `/`, `/ui-showcase/`, `/ui-showcase/citizen_dashboard_mobile/`, `/workspace/` (login redirect followed), `/accounts/login/` returned HTTP 200. Login protection for `/workspace/` is also asserted by pytest. |
| Browser visual check | Passed | Local browser rendered the supplied CivicOps landing at `http://localhost:8000/`; title and landing content observed. |

### Initial test findings and fixes

The first suite run produced `2 failed, 35 passed`: the complaint timeline template had dropped the expected `Evidence:` label, and the old login test expected the home route to be private after the product was changed to expose the supplied public landing page. Restored the evidence label and updated login tests to assert the intended public landing and authenticated `/workspace/`. The rerun passed with 38 tests.

### Limits

- No GitHub Actions run was checked or inferred.
- The `check --deploy` HSTS warnings are recorded above; public deployment remains unconfigured.
- This report covers local Docker tests on the worktree state identified above, not the final completion of every backend roadmap phase.

## 2026-11-21 — Backend Phase 1: workflow integrity

**Code under test:** Phase 1 worktree after `7a4038e`, including workflow-service routing transaction and ORM append-only guards. The Phase 0 public landing/login tests remain included.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | `docker compose run --rm checks`: `No changes detected`. |
| pytest | Passed | `39 passed in 61.03s`. Includes route-audit failure rollback and instance/queryset append-only tests. |
| Ruff | Passed | `All checks passed!`. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Django production deploy check | Passed with same documented warnings | Exit 0 on rebuilt container; only HSTS subdomain/preload warnings remain. |
| Fresh web image | Passed | `docker compose up -d --build db web`; PostGIS healthy and web started. |

### Phase 1 changes

- Ward/category routing rule selection, override validation, transition and routing audit now execute inside a single transaction in `apps/workflow/services.py`. Injected routing-audit failure rolls the status and event writes back.
- `StatusEvent` and `AuditEvent` now reject instance save/delete updates and queryset update/delete operations. Tests cover all four bypass paths.
- No schema changes were needed. Existing complaint creation transaction and state-machine-only status assignment were rechecked by the passing suite/code scan.

Phase 1 gate passed locally. GitHub CI was not checked; no production deployment or pilot ward data is claimed.

### Independent rerun on committed Phase 1

Reran the gate on **2026-11-21** with `HEAD=fac743d` after rebuilding the image from that commit. Results: migration check `No changes detected`; `39 passed in 92.20s`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`. `check --deploy` exited successfully with only the same two intentional HSTS warnings. Requests to `/`, `/ui-showcase/` and `/workspace/` returned HTTP 200 (workspace response includes the login redirect, covered by its test). Docker Desktop Linux engine access was granted for these commands. This independently confirms the Phase 1 report above.

## 2026-11-21 — Phase 2 security and Phase 3 generic geography checks

**Code under test:** worktree changes following `fac743d`; this report is local Docker evidence, not CI or a release verification.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | Latest Compose checks: `No changes detected`. |
| pytest | Passed | Latest Compose checks: `45 passed in 77.18s`. Added inactive-user visibility, stale field upload state, atomic evidence/audit rollback cleanup, and effective ward dates. |
| Ruff | Passed | Latest Compose checks: `All checks passed!`. |
| Bandit | Passed | Latest Compose checks: no issues in 1,431 scanned lines. |
| pip-audit | Passed on Phase 2 run | The preceding Phase 2 check reported no known vulnerabilities; dependency pins were unchanged for the subsequent effective-date tests. |
| Production `check --deploy` and rebuilt web smoke | Not rerun for this worktree | Prior Phase 1 result is historical. The attempted fresh build was blocked when the environment approval service hit its usage limit; no bypass attempted. |

### Scope and limits

- Field evidence writes now lock and validate the current complaint state in the same transaction as evidence and audit writes. Failure rolls database changes back and removes newly stored private files. Regression tests cover stale model state and audit failure cleanup.
- Complaint visibility denies inactive accounts. Active ward lookup requires the pin date to fall within the ward's effective dates; tests cover future and expired boundaries.
- The Phase 3 code path is implemented generically, but real jurisdiction is not configured: pilot centre coordinates and authoritative ward boundary/source data remain owner inputs. Do not treat generic tests as proof of a real pilot ward.
- GitHub CI, public deployment, backup/restore, and full acceptance remain unverified.

## 2026-11-21 — Phase 4 secure data-intake preparation

No model or inference feature was built. The user selected `ml/data/<category>/` for the five owner photo folders. Created the local intake structure and a read-only preflight requiring image/group manifest consistency; `other` is counted for evaluation only and is not a model output. Added tests for valid grouped samples, missing manifest, traversal, corrupt images, and duplicate-image split leakage.

| Check | Result | Evidence |
| --- | --- | --- |
| Integrated Compose suite | Passed | `No changes detected`; `54 passed in 57.91s`; Ruff passed; Bandit no findings; pip-audit no known vulnerabilities. |
| Dataset preflight against selected path | Correctly blocked | Exit 1; all five folders contained 0 images and `manifest.csv` was missing. It explicitly reported that no training/evaluation was run. |
| Docker build context | Passed | Rebuilt image context was 97.49 kB. Bare-image inspection confirmed `.env`, `.git`, `ml/data`, `/app/private_media`, `/app/backups`, and the uploaded ZIP are absent. |

The actual photo dataset is not in the workspace. No model, split, evaluation metrics, ONNX output, or worker is claimed. Phase 4 model work remains gated on the files, group manifest, and earlier core prerequisites.

The owner-selected path was checked directly: the five category folders were empty and `manifest.csv` was absent, so `python ml/dataset_preflight.py` exited 1 as designed and reported that training/evaluation had not run. The bare rebuilt app image does not contain `.env`, `.git`, `ml/data`, `private_media`, `backups`, or the uploaded UI ZIP. The Compose image build context was 97.49 kB after exclusions.

### ROADMAP_V2 task 2.2 attempt (2026-11-23)

- Added a regression test for the shared base page not requesting Bootstrap and for the site token set/system font stack.
- `python -m py_compile tests/test_error_pages.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_error_pages.py -k 'design_system' -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`).
- Source inspection found no Bootstrap layout/control classes in live templates; removed its base stylesheet reference. Screenshot comparison at 360/768/1280 and browser verification remain not verified because Django and Docker are unavailable. CSS source size: 14,782 bytes.

### ROADMAP_V2 task 2.3 attempt (2026-11-23)

- D6 map tile provider is unresolved. Per the roadmap stop condition, no tile or map changes were made; this task is not implemented pending owner input.
- `git diff --check` — exit 0. No tests apply to this documentation-only decision record.

### Independent integrated rerun

On **2026-11-21**, reran Compose checks for Phase 4 intake plus Phases 0–3: `No changes detected`; `54 passed in 60.80s`; Ruff passed; Bandit found no issues across 1,453 lines; pip-audit found no known vulnerabilities. The real-data preflight again exited 1 as designed: zero images in the five folders and no manifest. `migrate --check` and production `check --deploy` exited 0; only the documented HSTS warnings remain. Container-local landing, showcase, login and workspace requests all returned HTTP 200. This verifies the existing backend and intake preflight, not classifier quality or model behavior.

## 2026-11-21 — Phase 5 local backup and restore rehearsal

| Check | Result | Evidence |
| --- | --- | --- |
| Bash script syntax | Passed | `bash -n` succeeded for `backup.sh`, `restore_test.sh`, and `deploy.sh` in the project image. |
| Database backup and restore | Passed | A local custom-format dump restored into a disposable PostGIS container; sanity query found 35 migration records, 6 users, and 0 complaints. |
| Private-media backup and restore | Passed | Archive extracted into an isolated temporary volume; 6 files restored. |
| Temporary resource cleanup | Passed | Disposable containers/volume and restricted temporary backup directory were removed after verification. |
| Saved evidence | Passed | [`restore-test-2026-11-21.log`](restore-test-2026-11-21.log) contains counts and SHA-256 checksums only. |

### Finding

The local development private-media volume has six files with zero matching `Evidence` rows (six unreferenced files). They were not deleted because their ownership and retention are uncertain. The restored media archive preserves them. Production backups and off-host retention have not been tested.

### Integrated Phase 2 regression rerun

Reran the complete check service on **2026-11-21** against the Phase 2 worktree together with Phases 0 and 1: migration check `No changes detected`; `45 passed in 49.17s`; Ruff passed; Bandit reported no findings across 1,431 lines; pip-audit reported `No known vulnerabilities found`. Rebuilt and restarted `web` from the same worktree. Production `check --deploy` exited 0 with only the two documented HSTS warnings (`security.W005`, `security.W021`). Container-local HTTP requests to `/`, `/ui-showcase/`, `/accounts/login/` and `/workspace/` all returned HTTP 200; the workspace request followed its login redirect. This confirms the local integrated regression gate, not GitHub CI or production deployment.

## 2026-11-21 — Phase 3 geography and routing

**Code under test:** current worktree after adding effective-date validation, rule-precedence tests, and the ward date-window migration. This is local Docker evidence; GitHub CI and a live pilot area are not covered.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | Compose checks: `No changes detected`. |
| pytest | Passed | `49 passed in 69.33s`, including all Phase 0–2 coverage plus ward date-window validation, future/expired ward rejection, routing precedence, future rule exclusion, rule-version audit, and safety-critical triage warning. |
| Ruff | Passed | `All checks passed!`. |
| Bandit | Passed | No findings in 1,453 scanned lines. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Database migration | Passed | Rebuilt web container and applied `geography.0002_ward_ward_effective_window_valid` successfully. |
| Production check | Passed with known warnings | Exit 0; only `security.W005`/`security.W021` remain for HSTS subdomains/preload. |
| HTTP smoke | Passed | Container-local `/`, `/ui-showcase/`, `/accounts/login/`, and `/workspace/` returned HTTP 200; workspace followed its login redirect. |

The first run produced one failed **test expectation** because its shared fixture still contained a valid older ward rule. The service correctly chose that ward-specific rule. The fixture was corrected to make every ward-specific rule future-dated; the rerun passed all 49 tests. No routing service defect was found.

### ROADMAP_V2 task 1.1 attempt (2026-11-23)

- `python -m py_compile tests/test_day4_workflow.py apps/workflow/services.py apps/console/views.py apps/complaints/views.py` — exit 0.
- `git diff --check` — exit 0.
- `python -m pytest tests/test_day4_workflow.py -q` — exit 2 during collection: `ModuleNotFoundError: No module named 'django'`.
- `docker compose run --rm checks python -m pytest tests/test_day4_workflow.py -q` — exit 1: Docker API pipe unavailable (`dockerDesktopLinuxEngine`).
- `python manage.py makemigrations --check --dry-run` — exit 1: `ModuleNotFoundError: No module named 'django'`.
- Test and migration behavior are **not verified** in this workspace. No CI run was available.

### ROADMAP_V2 task 1.2 attempt (2026-11-23)

- Added command tests for aged and fresh information requests, idempotence, system audit/status records, and the triage timeout marker.
- The command default is 14 days, configurable with `INFO_REQUEST_TIMEOUT_DAYS`.
- `python -m py_compile apps/complaints/management/__init__.py apps/complaints/management/commands/__init__.py apps/complaints/management/commands/expire_info_requests.py apps/console/views.py tests/test_info_request_expiry.py` — exit 0.
- `git diff --check` — exit 0.
- `python manage.py makemigrations --check --dry-run` — exit 1: `ModuleNotFoundError: No module named 'django'`. Focused Django tests were not executable in this workspace.
- Functional behavior remains **not verified** in this workspace; no CI result is available.

### ROADMAP_V2 task 1.3 (2026-11-23)

- Blocked on the owner decision recorded as D-V10 in `docs/DECISIONS_NEEDED.md` (department official work-done authority).
- Existing policy remains field-worker-only; no code or test was changed. `git diff --check` — exit 0. `python manage.py makemigrations --check --dry-run` — exit 1 (`ModuleNotFoundError: No module named 'django'`). Runtime matrix tests were not run because Django/Docker are unavailable.

### ROADMAP_V2 task 1.4 attempt (2026-11-23)

- Added transition matrix and endpoint tests for admin cancellation of an active complaint, reason recording, and `admin_override` audit.
- `python -m py_compile apps/workflow/services.py apps/console/views.py apps/complaints/views.py apps/console/urls.py tests/test_workflow_transitions.py tests/test_console_workflow.py tests/test_day4_workflow.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_workflow_transitions.py tests/test_console_workflow.py -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- Workflow behavior remains **not verified** in this workspace; no CI result is available.

### ROADMAP_V2 task 1.5 attempt (2026-11-23)

- Added raw SQL `UPDATE` and `DELETE` attempts against both append-only tables; each expects a database error. Migration defines reversible PostgreSQL triggers.
- `python -m py_compile apps/audit/migrations/0002_append_only_database_triggers.py tests/test_workflow_transitions.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_workflow_transitions.py -k database_triggers -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- PostgreSQL migration application, raw SQL trigger assertions, and test database teardown are **not verified** because the Docker engine/database is unavailable.

### ROADMAP_V2 task 1.8 attempt (2026-11-23)

- Added evidence tests for original-byte/hash preservation, display/thumbnail downscaling and EXIF stripping, pixel limit, configured photo count, and a report-only reconciliation command. Response tests assert private caching, `nosniff`, inline disposition, and that only the display path is opened; authorization is covered for all complaint-visible roles and a deactivated account is denied.
- `python -m py_compile apps/complaints/models.py apps/complaints/migrations/0003_evidence_thumbnail_path.py apps/complaints/services.py apps/complaints/forms.py apps/complaints/views.py apps/complaints/management/commands/media_reconcile.py apps/workflow/services.py config/settings/base.py tests/test_day2_reporting.py tests/test_day4_workflow.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_day2_reporting.py -k 'multiple_citizen_photos or configured_max_edge or original_hash_and_exif_free_display or reconcile or deactivated_account' -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- Django image/upload tests and migration application are **not verified** because local Django and the Docker engine are unavailable.

### ROADMAP_V2 task 1.9 (2026-11-23)

- Not implemented: D3 retention periods and the deletion process are owner decisions. The blocker is recorded in `docs/DECISIONS_NEEDED.md`; no data retention values or purge behavior were invented.
- No code or tests changed for this decision-only commit. `git diff --check` — exit 0. `python manage.py makemigrations --check --dry-run` — exit 1 (`ModuleNotFoundError: No module named 'django'`).

### ROADMAP_V2 task 1.10 attempt (2026-11-23)

- Added tests for stable second pages across triage, department, field, and citizen lists, plus a combined triage search/status/ward/category/overdue filter.
- Added four complaint indexes and recorded the EXPLAIN plan status in `docs/PERFORMANCE.md`; required 5,000-row before/after plans are **not measured**.
- Python compilation and `git diff --check` are run before commit. Django tests, migration consistency, query counts, and EXPLAIN cannot run because Django and Docker/PostGIS are unavailable.

### ROADMAP_V2 task 1.11 attempt (2026-11-23)

- Added tests for explicit labels preserving slugs, inactive categories excluded from citizen forms, seeded display labels, and default-department triage preselection.
- Migration adds `label`, optional `icon`, `is_active`, and populates existing category labels from their existing slugs.
- `python -m py_compile apps/geography/models.py apps/geography/admin.py apps/geography/migrations/0003_category_display_fields.py apps/complaints/forms.py apps/accounts/management/commands/seed_demo.py tests/test_geography_admin.py tests/test_day2_reporting.py tests/test_console_workflow.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_geography_admin.py tests/test_day2_reporting.py -k 'category or seed_demo' -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- Django tests and migration consistency are **not verified** because local Django and Docker are unavailable.

### ROADMAP_V2 task 1.12 attempt (2026-11-23)

- Added importer/model tests for valid Polygon and MultiPolygon, empty and self-intersecting geometry, invalid geometry type, proposed/existing active overlaps, dry-run, idempotence, and the admin routing-gap report.
- D2 real pilot polygon/inside/outside evidence remains pending. Database exclusion constraint omitted pending verification of `btree_gist` support in the pinned PostGIS image.
- `python -m py_compile apps/geography/models.py apps/geography/geometry.py apps/geography/admin.py apps/geography/management/__init__.py apps/geography/management/commands/__init__.py apps/geography/management/commands/load_wards.py tests/test_ward_import.py tests/test_geography_admin.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_ward_import.py tests/test_geography_admin.py -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- Django/PostGIS tests and migration consistency are **not verified** because local Django and Docker are unavailable.

### ROADMAP_V2 task 1.14 attempt (2026-11-23)

- Added health endpoint success/failure tests, generated request ID response and JSON log tests, explicit cookie SameSite tests, and a subprocess check that production remains `DEBUG=False` even with `DJANGO_DEBUG=True`. Existing custom error page tests remain in `tests/test_error_pages.py`.
- `SESSION_COOKIE_AGE` remains the framework default pending owner decision D14.
- `python -m py_compile config/logging.py config/middleware.py config/views.py config/urls.py config/settings/base.py tests/test_observability.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_observability.py tests/test_error_pages.py -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- `docker compose config -q` — exit 0. `docker compose -f docker-compose.prod.yml config -q` — exit 1 because required `.env` values `APP_IMAGE` and `DOMAIN` are unset.
- Django tests and production `check --deploy` are **not verified** in this workspace.

### ROADMAP_V2 task 2.1 attempt (2026-11-23)

- Landing now includes `public_updates.html` and report/track/sign-in/account actions. Added tests for these actions, public-update content, no external origins or CDN assets outside vendor files, and production `/ui-showcase/` 404.
- Updated prior landing expectations from the archived CivicOps mockup to the implemented AI Smart City page and protected `/complaints/` tracking link; the redirect itself remains asserted.
- `python -m py_compile tests/test_error_pages.py tests/test_login.py tests/test_accessibility.py` — exit 0; `git diff --check` — exit 0.
- `python -m pytest tests/test_error_pages.py tests/test_login.py tests/test_accessibility.py -k 'landing or ui_showcase' -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). `python manage.py makemigrations --check --dry-run` — exit 1 for the same missing module.
- `rg -ni 'cdn\.|unpkg|googleapis|tailwind' templates static -g '*.html' -g '*.js' -g '*.css' -g '!static/vendor/**'` — exit 1 with no matches.
- Django template behavior remains **not verified** because local Django and the Docker engine are unavailable.

### Independent integrated rerun

On **2026-11-21**, reran the Compose checks on the resulting Phase 3 worktree: `No changes detected`; `49 passed in 62.49s`; Ruff passed; Bandit found no issues in 1,453 lines; pip-audit found no known vulnerabilities. `migrate --check` exited 0. Repeated `check --deploy` exited 0 with only the two documented HSTS warnings, and the four container-local HTTP smoke requests each returned 200. This rerun includes the prior workflow, authorization, evidence, and UI-route regression coverage.

### Phase 3 limits

- Centre coordinates and authoritative ward boundary/source data remain unavailable. Test polygons are synthetic fixtures only; no real pilot ward, routing data, or location-specific availability is claimed.
- GitHub CI, public deployment, backup/restore, and full acceptance remain unverified.

