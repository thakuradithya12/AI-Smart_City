# Progress

## 2026-11-25 — E.3 citizen verification reminder

- Added the D8-R three-day reminder service and management command, scheduled hourly. It creates one in-app/email notification per work-completion status event and never changes complaint or resolution state.
- Added a test for the pre-deadline boundary, one-time enqueue, and no automatic closure; recorded D8-R.
- `python -m py_compile` and `git diff --check` passed. Runtime test is not verified because Django is unavailable locally and Docker cannot connect to its engine.

## 2026-11-25 — E.2 D14 rolling session test

- Kept the already configured 12-hour rolling session policy and added a database-backed test that advances the request clock, checks session-store expiry moves forward, and checks the refreshed cookie max-age.
- `python -m py_compile tests/test_observability.py` and `git diff --check` passed. Runtime test is not verified because Django is unavailable to the host Python and Docker is unavailable.

## 2026-11-25 — E.1 privacy and retention

- Added the public privacy page, versioned consent capture, signed-in JSON export (including phone number), citizen deletion requests with anonymised accounts and preserved audit actors, and `purge_expired` for 12/6/24-month retention. The scheduler already discovers and runs this command hourly.
- Added five privacy/retention tests, a report consent-version assertion, and a missing privacy URL in the isolated error-page fixture. Complaint references and append-only status/audit rows are kept; expired report details and evidence files are removed.
- `py_compile` and `git diff --check` passed. Runtime pytest is **not verified**: collection fails because host Python has no Django; Docker checks cannot connect to the Docker engine. Migration application and overlapping PostgreSQL execution remain unverified.

## 2026-11-25 — C workflow lock

- Added a generator and generated transition reference from `Complaint.Status` and `TRANSITIONS`; comparison records the approved V2 admin cancellation extension and the citizen pre-acknowledgement cancellation alignment.
- Added six workflow invariant tests for reachability, terminal states, citizen cancellation during an information request, separate claim/verification, no silence-based closure, and generated-doc freshness.
- `python scripts/generate_workflow_doc.py --check`, Python syntax compilation, and `git diff --check` passed. Django tests are **not verified**: Docker could not connect to its engine pipe, and the host Python lacks Django.

## 2026-11-25 — B.4 phase1 CI promotion

- Owner-provided checks and Actions run `45562646639` are green on `b91531009a681f5ab293f0d1aa3a6c6b7a633630` (179 tests passed; migration check, Ruff, Bandit, pip-audit and deploy check completed successfully).
- Recorded the run in `docs/TEST_REPORT.md` and marked only roadmap task 0.4 as verified for this run. Promoted this documentation commit to `master` and tagged it `verified-phase1`; deployment and device acceptance remain unverified.

## 2026-11-23 — Phone-based citizen accounts and shared UI motion

- Changed new citizen registration and login to use unique Indian mobile numbers, normalized to `+91` format. Added a custom authentication backend and login lockout-compatible form normalization. Existing email-only staff/demo accounts remain able to sign in until an administrator assigns a phone number; new citizen accounts store no email.
- Added and applied `accounts.0002_user_phone_number_alter_user_email` to the local PostGIS database. Existing accounts are preserved with a nullable phone field; no phone numbers were fabricated or backfilled.
- Added a shared civic street-map illustration with subtle pointer response and slow breathing motion. Reduced-motion users and coarse-pointer devices receive a static, lower-opacity treatment. Applied the treatment to the Django site and supplied static UI showcase screens.
- Updated the register/sign-in screens, the supplied auth mockups, privacy wording, project specification, and operating guide. The form explicitly states that SMS/OTP ownership verification is not available.
- Evidence: rebuilt the `web` container and collected 154 static files; migration applied successfully; `manage.py check` reported `System check identified no issues (0 silenced)`; `git diff --check` passed. Browser verified `/register/` has phone/name/password fields and `/accounts/login/` has phone/password fields, with the animated map artwork visible. Automated tests were not run for this task.
- Next: test phone registration/sign-in including normalization and uniqueness; decide whether to migrate existing staff/demo users to phone credentials when owner-supplied numbers are available.

## 2026-11-23 — Refresh public landing UI

- Reworked the public landing page and shared application palette from navy/blue to deep evergreen, warm stone and terracotta, enlarged the CivicOps mark, and changed the header to a three-column layout with a compact mobile breakpoint.
- Removed the floating top-right showcase control; its temporary "All screens" link now sits in the page footer. Updated the screen index page to the same palette.
- Filled the landing-page whitespace with a live recent-report activity list sourced from status events. It shows category, ward, status and timestamp only; no names, descriptions or exact coordinates. Empty state is database-backed and does not invent activity.
- Updated the public area label to Telangana demo area. Rebuilt the `web` image; browser preview verified at 1280×720 with document height exactly 720px, no vertical overflow, the update feed and footer visible, and no browser console errors. The feed displayed actual database content: pothole · Demo Ward · In triage · Nov 22 · 13:23.
- `docker compose exec web python manage.py check` reported `System check identified no issues (0 silenced)`. `git diff --check` passed. No test suite was run for this UI-only task.

## 2026-11-22 — Keep local demo coverage in Telangana

- Changed `seed_demo` to always place its synthetic demo area in central Hyderabad, Telangana; removed latitude/longitude overrides so the command cannot seed this demo ward in another state. Its source is explicitly labeled synthetic and not pilot data.
- Expanded the synthetic square to cover the central Hyderabad demo area. Updated the seed regression test to check the Hyderabad center, an interior test point, and an outside point. Updated local setup and user guide instructions.
- Rebuilt and restarted the Docker web image, then reseeded the local database with output suppressed so passwords were not exposed. Database verification shows bounds `(78.3867, 17.285, 78.5867, 17.485)`, the Hyderabad center and an interior point are covered, Bengaluru is outside, and the ward source says synthetic/not pilot data.
- Docker Compose checks passed: migration check reported `No changes detected`; all `61` tests passed; Ruff passed; Bandit reported no issues across 1,455 lines; pip-audit found no known vulnerabilities. `compileall` and `git diff --check` also passed. An initial check invocation returned errors; a clean full rerun passed.

## 2026-11-22 — Complete local v1 backlog items

- Audited the project limits and corrected stale docs: README, clarifications, limits, and roadmap now distinguish the synthetic Hyderabad demo area from pilot ward data. Added the missing v1 specification and the required deferred-work/owner-input register.
- Implemented the optional duplicate review: same category, open status, within 30 geography metres, created within the last seven days. The triage detail page shows candidates; only an active triage reviewer can link one. Linking is audited and does not change status or hide either report.
- Added tests for near/far distance, category, age, final statuses, link audit, citizen denial, and the cross-role route-to-department visibility sequence.
- Final Docker gate before the null-department access fix: `No changes detected`; `65 passed in 67.64s`; Ruff passed; Bandit 0 findings across 1,535 lines; pip-audit found no known vulnerabilities. The later gate is recorded below.
- External release items remain recorded in [`docs/PARKING_LOT.md`](docs/PARKING_LOT.md): production host/domain, authoritative pilot polygons, licensed AI photos plus manifest, Git remote/CI, production operations, and physical-device acceptance. They cannot be truthfully completed from this local workspace without the required owner environment/data.

## 2026-11-22 — Close department null-scope access gap

- Full access-control audit found that a department official or supervisor with `department_id=NULL` was scoped using `department IS NULL`, which could expose unassigned complaint details/dashboard rows. Changed the visibility queryset to fail closed when no department is assigned and added tests for both roles.
- Final Docker gate after the permission helper change: `No changes detected`; `67 passed in 67.57s`; Ruff passed; Bandit reported no issues across 1,544 lines; pip-audit found no known vulnerabilities.
- Rebuilt the exact serving image; production `check --deploy` exited 0 with only documented `security.W005`/`W021` HSTS warnings; `collectstatic` copied 152 files and post-processed 446. Landing returned 200 and signed-out workspace, triage, and department routes returned expected 302 redirects. `git diff --check` passed.

## 2026-11-22 — Verify citizen-to-department routing

- Investigated the screenshots against the live PostGIS database. `ASC-2026-000001` exists for the citizen, is inside Demo Ward, and has an active pothole routing rule to Demo Department — Roads. It remains `in_triage` with no department because no triage reviewer has routed it yet; that matches the human-review workflow and is why the department account correctly sees zero complaints.
- Fixed misleading empty-state guidance on the department dashboard and inbox: new reports first enter triage and appear to the department after a reviewer routes them. Empty filtered inboxes now explain that no complaints match the selected status.
- Expanded the route regression test across roles: the department sees no untriaged complaint; after the reviewer routes via the active ward/category rule, the complaint and count appear on the department dashboard and inbox.
- Docker Compose checks passed: `No changes detected`; `61 passed`; Ruff passed; Bandit found no issues; pip-audit found no known vulnerabilities. Rebuilt and restarted the local web image; `/workspace/` and `/console/department/` both returned the expected signed-out HTTP 302 redirect.

## 2026-11-22 — Repair public sign-in and landing/report interactions

- Reproduced the landing sign-in defect: click changed the address to `/#login` and did not open the Django login route. Registration/login then redirected to the landing mockup instead of the authenticated workspace. Updated both CTAs and redirects; authenticated Overview/brand links now return to `/workspace/`.
- Removed public-map, FAQ/contact, and legal-placeholder links from the landing because those routes are not implemented in the frozen scope. Replaced the fake tracking form/sample complaint with a scoped sign-in link to the citizen's own complaint list.
- Browser review had shown an empty map. Found the Leaflet assets absent from the project; corrected the checked-in official Leaflet 1.9.4 integrity value and extended the vendor script to download all CSS-referenced images. The first production image rebuild then exposed missing `layers.png` and `layers-2x.png`; added both and the vendor script verified JS/CSS hashes, PNG signatures, and library licences.
- Added an accessible live location status and permission/error fallback to the report form. Added regression tests for real landing hrefs, successful auth redirects, and all required Leaflet files.
- First full run identified one failed registration redirect assertion (the POST-success branch had not been changed); corrected it. The follow-up full Compose suite passed 60 tests, Ruff passed, Bandit had zero findings, and pip-audit reported no known vulnerabilities.
- Final map audit found HTTP 403 tiles because Django's actual local response used `Referrer-Policy: same-origin`; the app also used OSM subdomains. Switched to the canonical tile host, configured the origin-only cross-origin referrer policy in shared settings, and added an accessible fallback on tile errors. OSM's official asset policy is recorded in [`DECISIONS.md`](DECISIONS.md).
- Final verification: Docker Compose checks — `No changes detected`; `61 passed in 100.44s`; Ruff clean; Bandit 0 findings across 1,457 scanned lines; pip-audit found no known vulnerabilities. Docker production-style image build passed `collectstatic` (152 files copied, 446 post-processed). Container response reports `Referrer-Policy: strict-origin-when-cross-origin`.
- Browser click-through confirmed signed-out landing Sign in opens `/accounts/login/`, valid test sign-in opens `/workspace/`, signed-in Sign in goes directly to workspace, Sign out returns to login, and the report map renders real basemap tiles; clicking the map updates latitude/longitude fields. No complaint was submitted. The browser geolocation action was not invoked because it requests access to precise device location.

## 2026-11-21 — Phase 6 local acceptance and handoff

- Reran the integrated Docker gate after accessibility fixes and local commit `e806d63799ebb374d644b1746465d2ae858769b7`: migrations consistent; post-commit 58 tests passed in 57.76s; Ruff clean; Bandit 0 findings across 1,453 lines; pip-audit clean. Production Django check exited 0 with the two documented short-HSTS warnings. Five local routes were smoke-tested; workspace redirected to login.
- Browser review showed the landing, 47-screen showcase listing and citizen dashboard design. This in-app viewport is narrow, and no phone, full desktop keyboard/contrast or live fresh-account demo evidence is claimed.
- Accessibility review found the old focus outline was only 2.13:1 against the page canvas. Replaced it with #1d4ed8 (6.24:1 against the canvas), added visible focus to native disclosure summaries and moved keyboard focus to an announced, field-linked report validation summary. Four regression tests now cover the report and triage template controls and contrast ratio. The final ZAP rerun against 128 URLs found 0 FAIL, 5 reviewed WARN categories and 57 PASS.
- Added [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md), and [`docs/PHASE6_ACCEPTANCE.md`](docs/PHASE6_ACCEPTANCE.md); linked them from README and wrote the currently applicable no-auto-deletion retention rule without inventing a retention duration.
- Phase 6 release gate remains open for owner domain/server and pilot geography, remote CI, live demo rehearsal, two-phone/accessibility checks, production operations and strict showcase CSP/SRI work. No day tag or push is claimed; no remote is configured. The local code commit exists and passed the post-commit suite.

## 2026-11-21 — Phase 5 local security gate

- Integrated Compose suite passed after final middleware change: `No changes detected`, `54 passed in 64.78s`, Ruff clean, Bandit 0 findings/1,453 lines, and pip-audit clean. Production check using the actual Compose key exited 0 with only the two short-HSTS warnings. Caddy config validated and the internal HTTPS proxy check stripped upstream `Server`; local HTML routes include `Cache-Control: no-store`, Permissions-Policy, and same-origin CORP.
- Final ZAP passive baseline against the isolated local HTTP target: 128 URLs, 0 FAIL, 5 WARN categories, 57 PASS. Reports are saved under `docs/`; cacheable HTML and COEP warnings are gone. `.env` key was rotated to a random 64-byte value without displaying it; ACL remains limited to current user, SYSTEM, and Administrators. `git diff --check` passed.
- The local disposable backup/restore rehearsal is recorded in `docs/restore-test-2026-11-21.log`. Production HTTPS, production-edge scan, CSP/SRI/COEP cleanup, remote CI, pilot geography, and owner photo/model inputs remain outstanding. The repository has no configured remote.

## 2026-11-21 — Phase 2 security checks and Phase 3 geography groundwork

- Field evidence creation now locks the current complaint row, validates the actor and current status inside the transaction, and writes evidence/audit together. If storage or audit work fails, DB writes roll back and newly written private files are removed. Added regression coverage for stale model state and audit failure cleanup.
- Complaint scoping now rejects inactive accounts. Ward containment uses only boundaries effective on the report date; future and expired ward cases now have regression tests.
- Added Bandit to the local Compose checks and GitHub Actions CI.
- Docker Compose verification on this worktree: `No changes detected`; `45 passed in 77.18s`; Ruff passed; Bandit reported no findings across 1,431 lines. The preceding Phase 2 run reported no known vulnerable dependencies; pins did not change after that audit.
- Rebuilding/rechecking `web` for the changed worktree was attempted but the environment's automatic approval service refused further Docker approval due to its usage limit. No workaround was attempted. Prior production check results are historical, not claimed for this worktree.
- Real pilot ward data remains unavailable; no centre coordinates or authoritative polygon source was invented. GitHub CI and public deployment remain unverified.
- Next: once Docker approval is available, rebuild `web`, rerun `check --deploy` and HTTP smoke; then obtain owner-provided geography inputs before loading actual wards. Continue production backup/restore and final acceptance gates afterward.
- Detailed results: [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

## 2026-11-21 — Integrated Phase 2 regression rerun

- On request, reran the full Compose check suite against the Phase 2 worktree and all prior phases: migrations `No changes detected`; `45 passed in 49.17s`; Ruff passed; Bandit zero findings / 1,431 lines; pip-audit `No known vulnerabilities found`.
- Rebuilt/restarted the local web service from the current worktree. `check --deploy` exited 0 with only HSTS subdomain/preload warnings. Container-local HTTP smoke: `/`, `/ui-showcase/`, `/accounts/login/`, `/workspace/` all returned HTTP 200 (workspace followed the login redirect).
- Current local Phase 2 integration gate passes. GitHub CI and public production remain unverified. Real pilot boundary data remains unavailable.
- Detailed results: [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

## 2026-11-21 — Phase 3 geography and routing groundwork

- Added a ward effective-date check in both model validation and the database, preventing end dates before start dates. Generated and applied `geography.0002_ward_ward_effective_window_valid` to the local database.
- Added routing tests for ward-specific precedence over a newer global rule, ignoring future ward rules and recording the rule version in the audit, plus a reviewer-visible safety-critical warning assertion.
- Full Compose gate: `No changes detected`; `49 passed in 69.33s`; Ruff clean; Bandit zero findings across 1,453 lines; pip-audit `No known vulnerabilities found`.
- Rebuilt/restarted `web`; migration applied; production `check --deploy` exit 0 with only documented HSTS warnings; container-local landing, showcase, login and workspace smoke requests all returned HTTP 200.
- One initial routing test had an incorrect expectation because its fixture contained an active ward rule. The fixture was corrected and the full suite rerun successfully; the implementation behavior was correct.
- Phase 3 generic logic is verified. Real ward setup remains blocked on the previously recorded absence of centre coordinates and authoritative boundary data; no pilot geography has been fabricated.
- Detailed results: [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

## 2026-11-21 — Independent Phase 3 regression rerun

- Reran the integrated Compose suite after the Phase 3 changes: `No changes detected`; `49 passed in 62.49s`; Ruff passed; Bandit zero findings in 1,453 lines; pip-audit no known vulnerabilities.
- `migrate --check` exited 0; rebuilt-container `check --deploy` exited 0 with only documented HSTS warnings; landing, showcase, login, and workspace HTTP requests all returned 200 inside the web container.
- This verifies the local integration of Phases 0–3, including workflow/lifecycle regressions. It does not unblock real pilot geography, deployment, or GitHub CI.

## 2026-11-21 — Phase 4 secure data-intake preparation

- The owner selected `ml/data/<category>/` for the five photo folders. Created the local category paths and a tracked manifest template. Added `.gitignore` and `.dockerignore` exclusions so private photos and local secrets cannot enter Git or the app image.
- Added read-only `ml/dataset_preflight.py` to validate allowed image formats, decodability/pixel limit, relative paths, group IDs, manifest/file parity, and exact duplicate grouping. It prints only category counts/errors and does not modify images. `other` is evaluation-only.
- Added five synthetic-fixture tests. Full Compose gate passed: `No changes detected`; `54 passed in 57.91s`; Ruff passed; Bandit no findings; pip-audit no known vulnerabilities.
- Real intake preflight exited 1 as expected: folders are empty and `manifest.csv` is absent. No training/evaluation/model work was run. Bare image inspection confirmed `.env`, Git metadata, photo folder, private media, backups and uploaded ZIP were excluded from the image.
- Phase 4 model work remains blocked on the actual photo files and group manifest; real pilot geography also remains unresolved. Details in [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) and `ml/DATA_INTAKE.md`.

## 2026-11-21 — Phase 5 local operations rehearsal

- Syntax-checked `scripts/backup.sh`, `scripts/restore_test.sh`, and `scripts/deploy.sh` with Bash in the project image.
- Created a restricted temporary database dump and private-media archive, restored the database into a disposable PostGIS container, and extracted media into a disposable volume. Sanity query: 35 migrations, 6 users, 0 complaints; media restore: 6 files. SHA-256 checksums and counts are in [`docs/restore-test-2026-11-21.log`](docs/restore-test-2026-11-21.log). Disposable resources and temporary backup files were removed.
- Rebuilt/restarted local web image; confirmed `.env`, `.git`, `ml/data`, private media, backups, and the UI ZIP are absent from the bare image. Production `check --deploy` exited 0 with only documented HSTS warnings; migration check and four HTTP smoke routes passed.
- Finding: the development media volume has six files without matching current Evidence records. Preserved them because their ownership is unclear; recorded in [`docs/LIMITS.md`](docs/LIMITS.md).
- This is local disposable evidence only, not an off-host production backup or public deployment.

## 2026-11-21 — Phase 4 integrated regression rerun

- Reran Compose checks with all prior phases: `No changes detected`; `54 passed in 60.80s`; Ruff passed; Bandit zero findings across 1,453 lines; pip-audit no known vulnerabilities.
- The real-data preflight still exits 1 as designed: all five owner-selected folders contain zero images and `manifest.csv` is absent. No training/evaluation was run.
- Migration check and production `check --deploy` exited 0 (only the two documented HSTS warnings); all four container-local HTTP smoke requests returned 200.
- This is a verified pass for preflight tooling and previous backend phases only. Model, ONNX, worker, and real-data metrics remain undelivered pending data and Phase 3 pilot inputs.

## 2026-11-21 — Independent Phase 1 test rerun

- Independently rebuilt `HEAD=fac743d` with Docker Desktop's Linux engine, DB reported healthy, then ran `docker compose run --rm checks`.
- Results: `No changes detected`; `39 passed in 92.20s`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`.
- Re-ran rebuilt-container `check --deploy`: exit 0 with only `security.W005`/`security.W021` HSTS warnings. Smoke requests to `/`, `/ui-showcase/`, and `/workspace/` each returned HTTP 200 (workspace redirects to login; automated test asserts the redirect).
- Details: [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md). This confirms the local Phase 1 gate on the committed code; no GitHub CI result is inferred.

## 2026-11-21 — Backend roadmap Phase 1 complete

- Moved active ward-specific/all-ward routing rule selection, override reason validation, state transition and routing audit write into a single atomic workflow service. The console view now calls the service and handles display messages only.
- Added a failure-injection test proving routing status, `StatusEvent` and all `AuditEvent` writes roll back if the routing-specific audit write fails.
- Closed ORM-level append-only bypasses: queryset `update()`/`delete()` now refuse for both `StatusEvent` and `AuditEvent`; the append-only test covers instance and queryset mutation paths.
- Phase 1 checks: `docker compose run --rm checks` — `No changes detected`; `39 passed in 61.03s`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`. Rebuilt current web image and ran `check --deploy` (exit 0; only the already documented HSTS subdomain/preload warnings).
- Full evidence and scope are in [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md). No schema migration was needed. GitHub CI and production deployment were not checked.
- Next: Phase 2 authorization/evidence-security audit. Review every action/evidence endpoint and upload properties, add targeted coverage for gaps, then run the same full local gate.

## 2026-11-21 — Phase 0 runtime verification

- Started Docker Desktop and accessed its Linux engine with approved elevated Docker access. Rebuilt and started current PostGIS/web containers; DB health check passed.
- First `docker compose run --rm checks`: migration consistency passed, pytest found 2 failures and 35 passes. Fixed complaint timeline evidence label and updated login tests for the intentional public landing plus authenticated workspace. Second run: `No changes detected`; `38 passed in 64.17s`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`.
- `check --deploy` exited 0. It reported only the expected `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` warnings; these remain off pending a real stable domain.
- Rebuilt web from the corrected worktree. HTTP smoke returned 200 for `/`, `/ui-showcase/`, one supplied screen, `/workspace/` (the test client verifies the login redirect), and `/accounts/login/`. Browser visibly rendered the supplied CivicOps landing at `http://localhost:8000/` with the hero, report CTA, tracking panel and gallery link.
- Full output recorded in [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md). This is local evidence only; GitHub CI was not checked and complete backend acceptance is not claimed. Next: Phase 1 workflow integrity/data consistency audit per `docs/BACKEND_ROADMAP.md`.

## 2026-11-21 — Backend roadmap Phase 0 attempt

- Reviewed current worktree and recent commits. Preserved the existing uncommitted `/` UI showcase and `ml/DATASETS.md` owner changes; did not reset, stage, or overwrite them.
- Current source inspection confirms the core Django workflow modules, transition service, private evidence service, PostGIS models, existing tests and CI files are present. Existing test counts in older progress entries refer to earlier commits and are not treated as current-HEAD verification.
- Phase 0 runtime gate is blocked: `docker version` reaches the Docker CLI but fails to connect to `npipe:////./pipe/dockerDesktopLinuxEngine` (`permission denied`); `docker compose config --quiet` completes without configuration output. Host `python` previously had no Django installed. Therefore no current-HEAD container build, test suite, `check --deploy`, migration check, or browser smoke is claimed.
- Source review found the uncommitted UI route exposed `/workspace/` without authentication while reading `request.user.role`. Restored `login_required` on that view. The UI landing and screen-gallery routes remain intentionally public and backend-independent.
- Next: make Docker Desktop's Linux engine reachable, then rebuild exact worktree and complete Phase 0 commands. After baseline passes, proceed to Phase 1's transactional lifecycle and data-integrity audit. No pilot geography or production deployment values were invented.

## 2026-11-21 — Backend completion roadmap

- Reviewed the frozen `AGENTS.md`, current project files, recent commits, existing workflow implementation, CI/Compose and deployment runbook. Recorded the distinction between historical owner-confirmed/runtime evidence and verification still needed on current HEAD.
- Added [`docs/BACKEND_ROADMAP.md`](docs/BACKEND_ROADMAP.md): baseline audit, workflow/data integrity, access/evidence security, real ward/routing data, gated optional AI, production operations, and final acceptance; includes gates, test evidence, stop/cut rules and unresolved owner inputs.
- Linked the roadmap from README and recorded the planning decision in `docs/DECISIONS.md`.
- No backend implementation or tests were run in this planning step. Current workspace contains earlier pending `apps/console/urls.py` UI-showcase changes and a pre-existing `ml/DATASETS.md` modification; preserve and review them during Phase 0.
- Next: Phase 0—enable/reach Docker Desktop's Linux engine, inspect and preserve current changes, rebuild exact current source, run checks and smoke the app. Do not proceed based on older test logs alone.

## 2026-11-20 — CivicOps UI integration

- Extracted the uploaded `stitch_civic_operations_platform (1).zip` archive into `docs/ui_reference/` (48 design/reference files). Added `docs/UI_DESIGN.md` to map integrated templates and call out designs that remain reference-only because their screens are outside v1 scope or lack live routes.
- Applied the archive's navy/blue civic palette, compact status badges, responsive layouts, semantic operational colors, keyboard focus states, skip navigation, form controls, empty states and activity timelines to the shared stylesheet and existing Django templates.
- Integrated live layouts for role overview, citizen report/list/detail, triage queue, department inbox, field task list/detail, registration, sign-in and signed-out states. Kept all workflow actions on existing named Django routes and permission-checked views.
- Overview metrics are computed from the signed-in user's `Complaint.objects.visible_to(user)` queryset; no static/demo metrics were added.
- Verification: `git diff --check` completed with only Git's Windows line-ending notices. `python manage.py check` could not run because the host Python is 3.15.0 and Django is not installed (`ModuleNotFoundError: No module named 'django'`). Prior progress records Docker's Linux engine as unavailable; no browser screenshot or app runtime is claimed for this UI change. Tests were not run.
- Next: run the app in the project Python 3.12/PostGIS container when Docker Desktop's Linux engine is available, review the pages in a browser at mobile and desktop widths, then capture screenshots and any visual follow-up.

## 2026-11-19 — Day 2 validation recovery and owner verification

- Owner's Docker output confirms the app image builds and `python manage.py check` reports no issues. Direct `pytest` and `ruff` commands in the `web` service failed because that image installs only `requirements/base.txt`.
- Added a Compose `checks` service that installs the development requirements in its disposable container, then runs pytest, Ruff and pip-audit. Next: owner reruns `docker compose run --rm checks` and returns the output; fix any findings before committing the Day 2 chunks.
- The first two check-service runs used the cached copied source and therefore still executed the earlier login test; bind-mounted the working tree into the service so the same verification command always sees edits.
- The latest full check run reached migration consistency (`No changes detected`) but pip timed out downloading Ruff before tests started. Increased the dev requirements install timeout and retries to match the app image.
- Latest owner-provided Docker evidence: migration consistency reported `No changes detected`; full pytest reported `18 passed`; Ruff reported `All checks passed!`; pip-audit reported `No known vulnerabilities found`.
- The report flow, private evidence endpoint, system transition and seed command are covered by those tests. Local Ruff and compile checks also pass in this workspace.
- The earlier recovery note about missing browser assets was superseded by the later owner-run browser checklist below.

## 2026-11-19 — Day 2 local browser gate: VERIFIED BY OWNER

- Owner confirmed on 2026-11-19 that the localhost browser gate worked: vendor assets loaded, demo ward seeded, registration/login, photo-and-pin report, timeline, outside-ward refusal, and cross-user 404 all worked.
- Existing tag `day-2-local` points to `d0052d71db79724278d03c9da2c7fed4c938ce35`, the Day 2 gate record. Preserve that tag and mark its browser gate as owner verified.
- Automated evidence remains: Docker migration check `No changes detected`; pytest `18 passed`; Ruff clean; pip-audit `No known vulnerabilities found`. These checks do not verify the browser gate.
- GitHub CI has not been confirmed. No green or red result is recorded.

## 2026-11-19 — Day 3 (in progress)

- Planned scope: exhaustive state-transition and role permission tests; triage queue; department inbox; route, acknowledge, reject, transfer and assign actions with reasons where required; status and audit event coverage.
- No deployment or public HTTPS claim. Continue local Docker verification in small chunks and wait for owner-provided output after each chunk.
- Chunk 1 completed: added role- and visibility-scoped transition helpers; tests every defined status pair against each role, including status/audit event writes and information-message audit records. Docker evidence: focused `pytest -q tests/test_workflow_transitions.py` — `3 passed`; full `pytest -q` — `21 passed`; migration check — `No changes detected`; Ruff clean; pip-audit `No known vulnerabilities found`.
- Chunk 2 completed: triage queue, ward/category rule routing and reasoned override, free-text rejection, department acknowledgement/transfer/assignment, same-department worker selection, seeded demo routing rules, and audit entries. Docker evidence: focused console/workflow/seed tests — `11 passed`; `manage.py check` — no issues; full pytest — `28 passed`; migration check — `No changes detected`; Ruff clean; pip-audit — `No known vulnerabilities found`.
- Day 3 gate passed locally: rebuilt and started `web`; container system check found no issues; in-container request to `/accounts/login/` returned HTTP 200. Transition and IDOR tests pass in the full suite. Commits: `c6eda7f` (transition permissions/tests), `c420396` (triage and department consoles). Tagged `day-3`.
- GitHub CI remains unconfirmed; no result inferred.

## 2026-11-19 — Day 4 browser gate: VERIFIED BY OWNER

- Owner confirmed on 2026-11-19 that the four-login browser lifecycle worked. The `day-4` tag is set at the Day 4 implementation endpoint `dadb26f`. GitHub CI is unconfirmed.
- Rejection reasons are mandatory free text, 5–500 characters, approved by the owner on 2026-11-19; see `docs/CLARIFICATIONS.md`.
- Planned scope only: field tasks/evidence/work claim; separate verification/dispute/reopen; citizen cancel and information reply; due badges; timeline evidence; Django admin configuration; full lifecycle, dispute, cancel and permission tests.
- Implemented field-worker task list/detail, start work, private before/after photo uploads, work note and gated mark-done action. The transition service now writes separate Resolution claim and verification fields, validates 5–500 character reasons, checks object visibility, and audits resolution before/after values.
- Added supervisor verification/dispute/reassignment, citizen confirmation/dispute/cancel and info-request reply actions, chronological status/message/evidence timeline, due/overdue badges, status filters, and read-only workflow records plus filtered configuration/user listings in Django admin.
- Added Day 4 end-to-end tests for the four-role lifecycle, dispute/reopen/reassign, citizen cancel, info request/reply, field-worker IDOR and evidence access, cross-department supervisor denial, no-after-photo rejection, and the codebase scan preventing status assignments outside `transition()`.
- Docker gate evidence: `docker compose run --rm checks` — migration check `No changes detected`, `36 passed`, Ruff `All checks passed!`, pip-audit `No known vulnerabilities found`; `docker compose run --rm web python manage.py check` — no issues; `docker compose run --rm web python manage.py migrate` — no migrations to apply; rebuilt web image and container-local `/accounts/login/` smoke returned HTTP 200.
- The four-login browser lifecycle was later confirmed by the owner on 2026-11-19; the Day 4 gate is verified by owner. GitHub CI remains unconfirmed.
- Code commit: `7a64f86` (`feat: add field resolution and verification workflow`).
- Fixed a seed-demo mismatch discovered while preparing the owner browser checklist: all demo category routes now use the demo staff department, and rerunning the seed aligns existing demo staff and routing rules. The categories remain the six defaults and the ward remains generated only from coordinates the owner enters. Regression assertion added to the seed test. Commit: `6a72210` (`fix: align demo routing with seeded staff`).
- Latest complete Docker gate after the seed fix: migration check `No changes detected`; `36 passed`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`. Latest image rebuild started `web`; login HTTP smoke returned 200; Django system check reported no issues.
- The owner has confirmed the manual browser lifecycle. Use the four logins printed by a first seed run (citizen, triage reviewer, department official, field worker); citizen confirmation completes the four-login lifecycle. If their one-time passwords were already printed and lost, change them with `docker compose exec web python manage.py changepassword <role>@example.test`.

## 2026-11-19 — Deployment preparation and AI dataset research (in progress)

- Owner verified the Day 2 localhost browser gate and the Day 4 four-login lifecycle on 2026-11-19. `day-2-local` already existed and points to its Day 2 gate record; `day-4` is tagged at `dadb26f`. GitHub CI remains unconfirmed.
- Prepared production Compose/Caddy configuration, production security settings, a PostgreSQL-backed report rate limiter (5 report POSTs per citizen per hour), an Axes login lockout (5 failed attempts per user/IP per rolling hour), a 300-second HSTS policy, a candidate-health deployment/rollback script, restricted backup and disposable restore-test scripts, and an Ubuntu VM runbook.
- Added the report throttle regression test. Docker build, tests, lint, audit, and production `check --deploy` are **not verified in this run** because Docker Desktop's Linux engine API returned `permission denied` on `docker version`. No remote action or training/data download was performed.
- AI research shortlist is in `ml/DATASETS.md` and is marked candidate/not downloaded. Three provisional image categories are proposed; rights and group-split audits remain required before training. No metrics or model performance claims exist.
- Public deployment remains blocked: no server/domain was supplied. Pilot centre coordinates and hand-drawn ward polygons remain unresolved. GitHub CI result remains blocked on owner report.
- Docker verification completed locally: `docker compose build web` succeeded; `docker compose run --rm checks` reported `No changes detected`, `37 passed in 52.11s`, `All checks passed!`, and `No known vulnerabilities found`; the production-like `check --deploy` exited 0 with the expected HSTS warnings for the deliberate short 300-second policy; production Compose `config --quiet` exited 0. The first stale-image production check reproduced the earlier import failure; rebuilding the image fixed it. A host `bash -n` attempt was blocked by Windows access to `bash.exe`, so script syntax was not independently verified that way.
- No remote action, model training or dataset download was performed. Public deployment remains blocked: no server/domain was supplied. Pilot centre coordinates and hand-drawn ward polygons remain unresolved. GitHub CI result remains unconfirmed and is not inferred from local checks.
- Next: wait for owner-provided server/domain and pilot centre before live deployment; record the GitHub CI result when the owner reports it.

## 2026-11-18 — Day 1 (in progress)

- Read the complete root AGENTS.md and captured owner decisions in `docs/CLARIFICATIONS.md`.
- Created a Django login/home skeleton, custom user and initial domain model definitions, local PostGIS Compose configuration, requirements, minimal CI workflow, and initial tests.
- Evidence: `docker compose config --quiet`, `python -m compileall -q apps config manage.py tests`, and `git diff --check` succeeded. Compose validation checks configuration only; it did not start the app. Host reports Python 3.15.0. `docker info` failed because the Docker Linux engine pipe is absent. `uv python install 3.12` failed after retries because DNS/network access is unavailable; an elevated retry was rejected by the automatic approval review, which requires asking before installing Python into the repository. No git repository existed at task start and was initialized for the requested commit/tag.
- Public HTTPS deploy gate: **blocked** (owner supplied no domain/server).
- Local Compose runtime, generated migrations, pytest, ruff, pip-audit, CI, and `check --deploy`: **not verified** (Docker engine/package downloads unavailable). No Day 1 gate is claimed passed. In particular, migrations remain ungenerated and the login page was not run.
- Pilot area setup: **pending** (centre coordinates and hand-drawn ward polygons are absent); no ward fixture created.
- Next: enable Docker Desktop/Linux engine or provide an accessible Python 3.12/PostGIS environment, then generate migrations, run focused/full checks, fix findings, and report the evidence. Do not invent coordinates or server values.

## 2026-11-18 — Dependency pin correction

- The Python 3.12 Docker pip dry-run confirmed `Django==5.2.20` does not exist; pip listed `5.2.19` as the newest 5.2.x. Updated the base pin and recorded the 5.2.19 security fixes in `docs/DECISIONS.md`.
- Evidence: `docker run --rm -v "${PWD}:/app" -w /app python:3.12.16-slim-trixie pip install --dry-run -r requirements/base.txt` completed with exit code 0 and printed `Would install ...` for the resolved set.
- Evidence: `docker run --rm -v "${PWD}:/app" -w /app python:3.12.16-slim-trixie pip install --dry-run -r requirements/dev.txt` completed with exit code 0 and printed `Would install ...` for base, dev and transitive dependencies.
- No application build, migration, app tests, or launch check was run in this correction task.

## 2026-11-19 — Compose migration and test recovery

- Generated and added the initial migrations for accounts, geography, complaints, AI assist, and audit. Updated the README to reflect the migrations now present.
- Fixed the email-login test to pass the request required by django-axes. Development settings now use ordinary static file storage and omit WhiteNoise middleware, so tests do not require a production `collectstatic` manifest. The CI-only secret is long enough for Django's deployment check.
- Increased pip's Docker install timeout to 120 seconds with 10 retries after the supplied build log showed a transient PyPI socket timeout.
- Evidence already observed before Docker became unavailable in this session: `makemigrations --check --dry-run` reported `No changes detected`; `migrate` completed all migrations; pytest reported `3 passed`; `ruff check .` reported `All checks passed!`; `pip-audit -r requirements/base.txt` reported `No known vulnerabilities found`; the login endpoint returned HTTP 200 inside the container.
- Remaining verification in this session: final rebuild and Docker-based checks are blocked because Buildx lock access is denied and the Docker Desktop Linux engine pipe returns permission denied. The public HTTPS deployment remains blocked because no domain/server was supplied. Day 1 is not claimed complete and no `day-1` tag is created.
# 2026-11-23 — ROADMAP_V2 Phase 0.3

- Rotated the local Django signing key without exposing it; `.env` is untracked. PostgreSQL role password rotation is pending because the local Docker/PostGIS engine is unavailable.
- Removed the specified caches and uploaded ZIP; preserved `private_media/`. Added `*.zip` ignore and full-history Gitleaks v3 CI scan (`fetch-depth: 0`); official action version checked 2026-11-23.
- No local history scan ran: Gitleaks is not installed and no Git remote is configured. See `docs/LIMITS.md` and `docs/TEST_REPORT.md`; 0.3 acceptance remains partial.

## 2026-11-23 — ROADMAP_V2 Phase 0.4

- Confirmed `actions/checkout@v6` and `actions/setup-python@v5` exist in official release histories; added dated evidence and outstanding owner inputs to `docs/DECISIONS_NEEDED.md`.
- `git remote -v` returned no rows. No remote was invented and no push/CI result is claimed; owner must provide an owner-controlled repo URL and authenticated remote setup. See `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V1

- Reproduced missing reset templates/email settings from source; added styled Django password-reset pages, environment-backed SMTP settings, and a focused legacy-staff email test. Files: `config/settings/{base,dev,prod}.py`, `.env.example`, `templates/registration/password_reset_*`, `tests/test_accounts.py`.
- `python -m pytest -q tests/test_accounts.py -k password_reset` exited 2 before assertions (`ModuleNotFoundError: No module named 'django'`); `makemigrations --check --dry-run` has the same environment blocker. Runtime result: not verified.
- New citizen phone-account recovery remains unavailable without an owner-approved phone verification route; see `docs/LIMITS.md` and D4.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V2

- Reproduced the manager's domain-only email normalization and confirmed citizen registration has no email field. Added lowercase normalization for legacy staff email creation, a migration that refuses case-collision groups without changing users, a `LOWER(email)` unique constraint, and a regression test.
- `python -m pytest -q tests/test_accounts.py -k email_accounts` exited 2 during import (`ModuleNotFoundError: No module named 'django'`); migration generation/application is not verified. See `docs/TEST_REPORT.md` and `docs/LIMITS.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V3

- Source check disproved that Bootstrap CSS is entirely unused: the shared base loads it, live templates use its `.card` and `.badge` components, and the base card flex behavior is not replaced by `site.css`. No UI change was warranted; Bootstrap JavaScript is not loaded. Evidence is recorded in `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V4

- Reproduced a plain `ModelAdmin` for a `MultiPolygonField`; switched `WardAdmin` to Django 5.2 `GISModelAdmin` and added an inheritance regression test. Verified the API against official Django 5.2 GeoDjango admin docs.
- `python -m pytest -q tests/test_geography_admin.py` exited 2 before assertions because Django is not installed. Runtime GIS editor behavior is not verified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V5

- Reproduced unordered `.first()` ward selection. Added `active_ward_for_point()` to refuse multi-ward matches and wired it into report submission before image storage; added a duplicate-active-polygon regression test.
- `python -m pytest -q tests/test_day2_reporting.py -k overlapping_active_wards` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). PostGIS behavior is not verified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V6

- Reproduced raw category slug rendering. Added a derived human-readable category label, updated complaint/queue/dashboard/public-update displays and `Category.__str__`, and added label/template-source regression tests.
- `python -m pytest -q tests/test_geography_admin.py -k display_label` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Rendered output is not runtime-verified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V7

- Confirmed no custom error templates existed; added 400/403/404/500 pages and tests that exercise each Django error handler with `DEBUG=False` using a dedicated test URLconf.
- `python -m pytest -q tests/test_error_pages.py` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Error-page rendering remains unverified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V8 (reverted in f071b46)

- Reproduced the unused `Category.default_department`. Routing now prefers active ward/category rules and falls back to that department only when no active rule applies; the audit records source `category_default` and reserved version `0`. Added a routing/audit regression test and documented the fallback.
- `python -m pytest -q tests/test_console_workflow.py -k category_default_department` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Runtime routing is not verified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V9

- Reproduced the per-row department worker lookup; verified the message timeline already selects authors. Precomputed inbox workers and eager-loaded complaint detail relations, resolution actors, messages/authors and evidence. Added query-count growth tests for 1 vs 30 complaints and 0 vs 30 messages.
- `python -m pytest -q tests/test_console_workflow.py -k query_count` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Query counts remain unverified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V10

- Confirmed the state table allows department officials to mark work done while `mark_work_done` requires a field worker. Per roadmap owner-decision rule, made no code change; recorded the question and recommended default in `docs/DECISIONS_NEEDED.md` and `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V11

- Reproduced missing report photo `accept`/`capture` hints; added JPEG/PNG/WebP acceptance and `capture="environment"` to the report input, plus a rendered-page regression test.
- `python -m pytest -q tests/test_day2_reporting.py -k mobile_file_hints` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Rendered HTML is not verified; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V12

- Reproduced missing evidence response headers. Authorized display evidence now returns private 5-minute caching, `nosniff`, and inline disposition; a regression test asserts headers and confirms only the display path is opened.
- `python -m pytest -q tests/test_day2_reporting.py -k evidence_response` exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). HTTP behavior remains unverified; see `docs/TEST_REPORT.md` and `docs/LIMITS.md`.

## 2026-11-23 — ROADMAP_V2 Phase 0.5 V13

- Reproduced homepage's dependency on `docs/ui_reference` mockup HTML. Replaced it with the server-rendered `templates/landing.html`, routed authenticated visitors to their dashboard, and removed temporary showcase endpoints.
- Added a regression test that sets `BASE_DIR` to an empty temporary directory and checks the public homepage renders while `/ui-showcase/` is no longer routed.
- Focused test exited 2 during collection (`ModuleNotFoundError: No module named 'django'`). Python AST parsing and `git diff --check` passed; runtime behavior remains unverified.

## V10 — field-worker-only work completion (on phase1)

- Updated the transition role matrix and SPEC: only field workers may claim work done; the existing endpoint already requires field-worker role and its template exposes the action only in the assigned field task.
- Added a regression covering department-official POST denial and direct transition refusal; role-matrix coverage derives its allowed roles from `TRANSITIONS`.
- Runtime tests not run; unverified until CI.

## 2026-11-23 — ROADMAP_V2 task 1.1

- Added audited reassignment for active assigned/in-progress complaints; status stays unchanged and the citizen timeline shows a neutral entry. Existing reopened-to-assigned flow remains a state transition.
- Added tests for supervisor, department official and admin roles, department/active-worker/reason/status checks, and old-worker task/evidence access.
- `python -m py_compile ...` and `git diff --check` exited 0. `pytest` and `makemigrations --check --dry-run` could not run: local Python has no Django; Docker checks could not connect to Docker Desktop.
- Runtime and concurrent-database behavior remain unverified; details in `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 task 1.2

- Added `expire_info_requests`, with a 14-day default (`INFO_REQUEST_TIMEOUT_DAYS`), latest-event age check, audited transition to triage, and a timed-out marker in the reviewer queue.
- Added tests for expiry, idempotence, no early expiry, audit/status events, and the queue marker.
- `py_compile` and `git diff --check` are run before commit. Django tests and migration checks remain unavailable in this workspace; see `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 task 1.3

- Owner decision D-V10 is pending: whether department officials may mark work done. Kept the existing field-worker-only transition/view/matrix consistent and recorded the question in `docs/DECISIONS_NEEDED.md`.
- No implementation change made while the decision is pending; proceeding with independent roadmap tasks as requested.
- `git diff --check` run before commit. Django migration/test commands remain unavailable as recorded in `docs/TEST_REPORT.md`.

## 2026-11-23 — ROADMAP_V2 task 1.4

- Defined admin recovery actions: reassign active work, route/reject triage items, and cancel any non-terminal complaint with a reason. Admin cancellation is available on complaint detail; audit entries are marked `admin_override`.
- Added matrix and endpoint tests; documented the capability in `SPEC.md` and `DECISIONS.md`.
- Python compilation and diff checks run before commit. Django tests and migration checks remain unverified because Django/Docker are unavailable.

## 2026-11-23 — ROADMAP_V2 task 1.5

- Added a reversible PostgreSQL trigger migration rejecting UPDATE/DELETE on status and audit event tables; added raw SQL mutation tests for both tables.
- Python compilation and diff checks run before commit. Migration application, raw SQL rejection, and Django flush/teardown behavior remain unverified because PostgreSQL/Docker are unavailable.

## 2026-11-23 — ROADMAP_V2 task 1.8

- Added configurable display downscaling, EXIF-free thumbnails, multiple citizen photos, stored thumbnail paths, and report-only `media_reconcile`. Evidence responses remain private and open only display copies.
- Added tests for configured image size, thumbnail EXIF/size, pixel caps, multi-photo limits, deactivated-account evidence denial, and non-destructive reconciliation.
- Settings default to three photos and a 1600-pixel display edge; display-edge production confirmation is recorded in `docs/DECISIONS_NEEDED.md`.
- Python compilation and diff checks run before commit. Image/database behavior remains unverified because Django/Docker are unavailable.

## 2026-11-23 — ROADMAP_V2 task 1.9

- D3 is unresolved: complaint/photo/account retention periods and the deletion process are owner inputs. Recorded the blocker in `docs/DECISIONS_NEEDED.md`; left privacy deletion/purge behavior unimplemented rather than choosing retention periods.
- Proceeding to independent task 1.10 as requested. No code tests were added for this decision-only task.

## 2026-11-23 — ROADMAP_V2 task 1.10

- Added pagination, stable ordering, shared ID/description search, status/ward/category/overdue filters, and the requested complaint indexes across citizen and staff lists.
- Added pagination/filter tests and query plans documentation. EXPLAIN before/after on 5,000 rows is not measured because the PostGIS test service is unavailable; `docs/PERFORMANCE.md` records that limit.
- Python compilation and diff checks run before commit. Django tests and migration checks remain unavailable in this workspace.

## 2026-11-23 — ROADMAP_V2 task 1.11

- Added category display labels, optional icon, and active flag while preserving slugs; seed data now sets labels and active state, and citizen reporting excludes inactive categories.
- Kept `default_department` as a triage suggestion only; routing still follows the active ward/category rule and records overrides.
- Added label, inactive-category, seed-label, and triage-suggestion tests. Python compilation and diff checks run before commit; Django tests/migration checks remain unavailable.

## 2026-11-23 — ROADMAP_V2 task 1.12

- Added `load_wards` with dry-run, source/effective date, idempotent name upsert, Polygon→MultiPolygon normalization, geometry and active-overlap checks; added model overlap validation and an admin routing-gap report.
- Added tests for Polygon/MultiPolygon, empty/invalid/self-intersecting/overlapping input, dry-run/idempotence, model overlap validation, and routing-gap reporting.
- D2 pilot coordinates and authoritative ward source remain pending; no pilot polygon or known-point test was invented. `btree_gist` could not be verified without Docker/PostGIS, so no database exclusion constraint was added.
- Python compilation and diff checks run before commit. Django/PostGIS tests and migrations remain unavailable.

## 2026-11-23 — ROADMAP_V2 task 1.14

- Added JSON stdout logging, generated request IDs, public database-only `/healthz/`, explicit SameSite settings, and changed Compose web/candidate healthchecks to use the endpoint. Production settings continue to force `DEBUG=False`; custom error templates already existed and have regression coverage.
- Session idle age needs owner approval (D14); retained the framework default and recorded the pending input rather than choosing a timeout.
- Added health, request ID, log format, cookie policy, and production DEBUG tests. Python compilation and diff checks run before commit; Django tests/Compose checks remain unavailable.

## 2026-11-23 — ROADMAP_V2 task 2.1

- Reused the existing `public_updates.html` partial on the Django landing page and added direct report/track actions alongside sign-in and account creation.
- Added landing checks for real actions, public updates, no external origins/assets, and `/ui-showcase/` 404 under production settings. Updated stale landing assertions to the current AI Smart City brand and actual protected tracking route.
- Python compilation and diff checks run before commit. Django template/browser tests remain unavailable in this workspace.

### ROADMAP_V2 task 2.2 attempt (2026-11-23)

- Centralized palette, semantic state colors, system typography, spacing, radius and type tokens in `static/css/site.css`; documented the system in `docs/DESIGN_SYSTEM.md`.
- Removed the unused Bootstrap stylesheet from the shared base template after checking live templates for Bootstrap layout/control classes. Kept vendor files intact. Added regression coverage for no Bootstrap request and expected tokens.
- CSS source is 14,782 bytes. Screenshot comparison at 360/768/1280 is not verified: Django and Docker are unavailable.
- `python -m py_compile tests/test_error_pages.py` and `git diff --check` — see task entry in `docs/TEST_REPORT.md`.
### ROADMAP_V2 task 2.3 attempt (2026-11-23)

- Map implementation is held at the D6 owner choice (OSM demo traffic or keyed provider); recorded the dependency in `docs/DECISIONS_NEEDED.md` and proceeded to independent work as instructed.
- No map code or tests changed. `git diff --check` — see task entry in `docs/TEST_REPORT.md`.

### ROADMAP_V2 task 2.4 (2026-11-23)

- Reworked reporting into six progressively enhanced steps; added multiple-photo preview and client size feedback, review summary, double-submit guard, bounded optional landmark, and documented that files must be reselected after server errors.
- Added form/render, landmark persistence and over-limit validation tests; Android/iPhone-class manual run remains not verified because no physical device was available.
- Python compilation, JS syntax, Django tests, and diff-check results are recorded in `docs/TEST_REPORT.md`.
- Commit `6b97f7b` was pushed to `origin/phase1` at the requested two-commit cadence; remote CI has not been checked.

### ROADMAP_V2 task 2.8 blocked (2026-11-23)

- CSP `img-src` depends on D6's tile host. Recorded the exact owner question and recommended OSM demo default; no provider policy was guessed.
- Updated the stale remote-status note: `origin/phase1` accepted `6b97f7b`; no remote CI result was checked.

### ROADMAP_V2 task 2.8 owner decision and implementation (2026-11-23)

- Owner selected OSM demo tiles and strict CSP allow-list; tile URL is now setting-driven, CSP is report-only by default in development and enforced by default in production.
- Recorded D2, D3, D6, D8, D12, D14 and V10 decisions; removed resolved items from `DECISIONS_NEEDED.md`. D3 periods remain provisional pending owner/college confirmation.
- CSP, setting, tile URL, and retention-default tests added. Manual browser click-through/ZAP and Django tests remain unverified in this environment.

### ROADMAP_V2 task 3.1 (2026-11-23)

- Added recipient-scoped notification outbox/inbox, unread badge and mark-read action; status transition and reassignment hooks create deduplicated rows atomically.
- Added bounded `send_notifications` batch with generic error recording, retry cap/backoff and in-app-only handling for missing email; email content is public ID, status and complaint link only.
- Added event-recipient, privacy/IDOR, idempotency, rollback and delivery-failure tests. `py_compile`, Compose and diff-check passed; Django tests/migration check could not run because Django is absent. See `docs/TEST_REPORT.md`.

### ROADMAP_V2 task 3.3 (2026-11-23)

- Added PostgreSQL advisory-lock scheduler, maintenance intervals, scheduler heartbeat, health endpoint visibility, and dev/prod Compose services.
- Jobs are skipped until their commands exist; `check_sla` is now supplied by task 3.2. Scheduler acceptance remains pending for the privacy task 1.9 `purge_expired` prerequisite and PostgreSQL overlap/kill-restart verification.
- Exact static and collection checks are in `docs/TEST_REPORT.md`.

### ROADMAP_V2 task 3.2 (2026-11-23)

- Added reviewer-set priority, an SLA breach timestamp, pause/resume accounting around information requests, and an idempotent `check_sla` command. Breaches are audited and notify supervisors in the complaint's department; no status transition or escalation is performed.
- Tests cover pause/resume, priority authorization/audit, breach idempotency, and paused/terminal exclusions. Runtime tests and migration checks remain unverified because Django is unavailable.

### ROADMAP_V2 task 3.4 decision record (2026-11-23)

- Recorded the missing reminder interval question and recommended default (3 days, once per pending resolution). Reminder scheduling is deferred until owner selection; AI tasks continue independently.

### CI run #25: error-template URL configuration (2026-11-25)

- Added the named `home` route to the test error URLConf; Django's error templates reverse `home` while rendering 400/403/404/500 pages.
- `python -m pytest tests/test_error_pages.py::test_custom_error_templates_render -q` — exit 4 during collection (`ModuleNotFoundError: No module named 'django'`); `python -m py_compile tests/error_urls.py` — exit 0; `git diff --check` — exit 0.
- Error-page behavior remains unverified locally; CI rerun required.
- Marked the two public landing tests as database-enabled because the live landing query reads recent status events. `python -m py_compile tests/test_error_pages.py` — exit 0; `git diff --check` — exit 0; runtime pytest remains unavailable without Django.

### CI pytest: notification attempt counter persistence (2026-11-25)

- The CI retry tests fail because `send_notifications` increments `attempts` but omitted that field from both success and failure `update_fields`, so the database retained zero attempts and retry caps never applied. Persisted the field on both paths.
- Existing tests cover successful delivery, failure isolation, and retry cap. `python -m py_compile apps/notifications/management/commands/send_notifications.py` — exit 0; focused pytest collection exited 2 (`ModuleNotFoundError: No module named 'django'`); `git diff --check` — exit 0.
- Runtime behavior awaits CI verification.

### CI pytest: information-request expiry test fixture (2026-11-25)

- The expiry tests requested `day4_setup`, a fixture defined only inside `test_day4_workflow.py` and therefore unavailable to other test modules. Added a purpose-built local fixture with only the users, category and synthetic ward these tests need.
- `python -m py_compile tests/test_info_request_expiry.py` — exit 0; pytest collection exited 2 because Django is not installed locally; `git diff --check` — exit 0. CI must verify behavior.

### CI pytest: console detail test fixture (2026-11-25)

- Added the department supervisor missing from `console_setup`; the message-history query test uses that role to read an in-department complaint.
- `python -m py_compile tests/test_console_workflow.py` — exit 0; `git diff --check` — exit 0. Runtime pytest is not verified locally because Django is unavailable.

### CI pytest: canonical Axes lockout identifiers (2026-11-25)

- Configured django-axes 9's documented `AXES_USERNAME_CALLABLE` to reuse phone normalization and case-fold legacy email identifiers, preventing spelling variants from splitting one user's failed-login counter. Added the decision record; existing phone/email lockout integration tests cover the behavior.
- `python -m py_compile apps/accounts/backends.py config/settings/base.py` — exit 0; `git diff --check` — exit 0; `python -m pytest tests/test_accounts.py -k axes_locks -q` — exit 2 during collection (`ModuleNotFoundError: No module named 'django'`). CI verification is required.

### CI pytest: in-app-only notification fixture (2026-11-25)

- Corrected the email-less notification test to clear the email on its citizen fixture; the shared fixture otherwise had an email and could not exercise the in-app-only path.
- `python -m py_compile tests/test_notifications.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

### CI pytest: development email backend assertion (2026-11-25)

- The test runner intentionally swaps Django's email backend to `locmem`; changed the assertion to inspect the development settings module directly, which is the configuration the test intends to verify.
- `python -m py_compile tests/test_notifications.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

### CI pytest: idempotent ward import validation (2026-11-25)

- The importer assigned an existing primary key to a new unsaved `Ward` before `full_clean()`, causing unique checks to report the existing ward as a duplicate. Reused the persisted instance for update validation, matching the eventual write path.
- `python -m py_compile apps/geography/management/commands/load_wards.py` — exit 0; focused pytest exited 4 during collection (`ModuleNotFoundError: No module named 'django'`); `git diff --check` — exit 0.

### CI pytest: configurable map tile assertion (2026-11-25)

- Updated the map asset test to assert the tile URL is supplied through the template's `map_tile_url` data attribute and consumed by Leaflet, matching the D6-swappable setting instead of requiring a hardcoded OSM URL in JavaScript.
- `python -m py_compile tests/test_accessibility.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

### CI pytest: reassignment test identifier length (2026-11-25)

- Shortened the parameterized reassignment test's generated complaint IDs; including the full `department_official` role and status exceeded the model's 32-character limit before the behavior under test ran.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0.

### CI pytest: admin reassignment audit expectation (2026-11-25)

- Updated the admin reassignment assertion to include the audited `operation` discriminator emitted with the `admin_override` event; this preserves a clear audit action while checking the full payload.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

### CI pytest: status-filtered triage pagination fixture (2026-11-25)

- The reviewer queue intentionally lists all non-terminal complaints, but the pagination test asserted every reviewer row had the `PAGE-T-` prefix while also creating other active statuses. Added an explicit `in_triage` filter to that case so it tests the target list slice.
- `python -m py_compile tests/test_console_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is unavailable locally; `git diff --check` — exit 0.

### CI pytest: streamed evidence response test transaction (2026-11-25)

- Marked the multi-role streaming evidence test as transactional because `FileResponse.close()` ends a request and closes the request-scoped DB connection; the test then performs more requests. This allows the test to exercise that lifecycle without retaining a closed connection inside pytest-django's outer atomic transaction.
- `python -m py_compile tests/test_day4_workflow.py` — exit 0; focused pytest exited 4 during collection because Django is not installed locally; `git diff --check` — exit 0. CI must confirm the diagnosis.
# 2026-11-23 — 2.8 CSP default correction

- Corrected the blank `.env.example` toggle behavior so production enforces CSP by default while development stays report-only unless explicitly configured.
- Evidence: `python -m py_compile ...` exit 0; `git diff --check` exit 0. Focused pytest collection remains unavailable because Django is not installed (exit 1).
- Follow-on: blank-toggle behavior was corrected in the 2.8 commit immediately before task 3.1.
