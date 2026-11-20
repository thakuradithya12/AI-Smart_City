# Progress

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
