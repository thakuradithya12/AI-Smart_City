# Progress

## 2026-11-19 — Day 2 validation recovery (in progress)

- Owner's Docker output confirms the app image builds and `python manage.py check` reports no issues. Direct `pytest` and `ruff` commands in the `web` service failed because that image installs only `requirements/base.txt`.
- Added a Compose `checks` service that installs the development requirements in its disposable container, then runs pytest, Ruff and pip-audit. Next: owner reruns `docker compose run --rm checks` and returns the output; fix any findings before committing the Day 2 chunks.
- The first two check-service runs used the cached copied source and therefore still executed the earlier login test; bind-mounted the working tree into the service so the same verification command always sees edits.
- The latest full check run reached migration consistency (`No changes detected`) but pip timed out downloading Ruff before tests started. Increased the dev requirements install timeout and retries to match the app image.
- Latest owner-provided Docker evidence: migration consistency reported `No changes detected`; full pytest reported `18 passed`; Ruff reported `All checks passed!`; pip-audit reported `No known vulnerabilities found`.
- The report flow, private evidence endpoint, system transition and seed command are covered by those tests. Local Ruff and compile checks also pass in this workspace.
- At the time of this recovery entry, the Day 2 browser gate was still pending: vendor asset files were absent in the workspace and no test coordinates had been supplied. Bootstrap and Leaflet downloads had failed here due to DNS. The implementation commit at that point was `26d5c97`.

## 2026-11-19 — Day 2 local gate status: UNVERIFIED

- The prior message containing the apparent localhost results was template text, not the owner's test report. No manual Day 2 browser result is confirmed.
- The `day-2-local` tag exists, but is UNVERIFIED until the owner reports their own results. Do not cite it as a passed gate.
- Automated evidence remains: Docker migration check `No changes detected`; pytest `18 passed`; Ruff clean; pip-audit `No known vulnerabilities found`. These checks do not verify the browser gate.
- GitHub CI has not been confirmed. No green or red result is recorded.

## 2026-11-19 — Day 3 (in progress)

- Planned scope: exhaustive state-transition and role permission tests; triage queue; department inbox; route, acknowledge, reject, transfer and assign actions with reasons where required; status and audit event coverage.
- No deployment or public HTTPS claim. Continue local Docker verification in small chunks and wait for owner-provided output after each chunk.
- Chunk 1 completed: added role- and visibility-scoped transition helpers; tests every defined status pair against each role, including status/audit event writes and information-message audit records. Docker evidence: focused `pytest -q tests/test_workflow_transitions.py` — `3 passed`; full `pytest -q` — `21 passed`; migration check — `No changes detected`; Ruff clean; pip-audit `No known vulnerabilities found`.
- Chunk 2 completed: triage queue, ward/category rule routing and reasoned override, free-text rejection, department acknowledgement/transfer/assignment, same-department worker selection, seeded demo routing rules, and audit entries. Docker evidence: focused console/workflow/seed tests — `11 passed`; `manage.py check` — no issues; full pytest — `28 passed`; migration check — `No changes detected`; Ruff clean; pip-audit — `No known vulnerabilities found`.
- Day 3 gate passed locally: rebuilt and started `web`; container system check found no issues; in-container request to `/accounts/login/` returned HTTP 200. Transition and IDOR tests pass in the full suite. Commits: `c6eda7f` (transition permissions/tests), `c420396` (triage and department consoles). Tagged `day-3`.
- GitHub CI remains unconfirmed; no result inferred.

## 2026-11-19 — Day 4 (in progress)

- Day 2 localhost browser gate and the existing `day-2-local` tag are marked UNVERIFIED until the owner supplies their own results. GitHub CI is unconfirmed.
- Rejection reasons are mandatory free text, 5–500 characters, approved by the owner on 2026-11-19; see `docs/CLARIFICATIONS.md`.
- Planned scope only: field tasks/evidence/work claim; separate verification/dispute/reopen; citizen cancel and information reply; due badges; timeline evidence; Django admin configuration; full lifecycle, dispute, cancel and permission tests.
- No `day-4` tag until the owner confirms the local four-login browser gate.
- Implemented field-worker task list/detail, start work, private before/after photo uploads, work note and gated mark-done action. The transition service now writes separate Resolution claim and verification fields, validates 5–500 character reasons, checks object visibility, and audits resolution before/after values.
- Added supervisor verification/dispute/reassignment, citizen confirmation/dispute/cancel and info-request reply actions, chronological status/message/evidence timeline, due/overdue badges, status filters, and read-only workflow records plus filtered configuration/user listings in Django admin.
- Added Day 4 end-to-end tests for the four-role lifecycle, dispute/reopen/reassign, citizen cancel, info request/reply, field-worker IDOR and evidence access, cross-department supervisor denial, no-after-photo rejection, and the codebase scan preventing status assignments outside `transition()`.
- Docker gate evidence: `docker compose run --rm checks` — migration check `No changes detected`, `36 passed`, Ruff `All checks passed!`, pip-audit `No known vulnerabilities found`; `docker compose run --rm web python manage.py check` — no issues; `docker compose run --rm web python manage.py migrate` — no migrations to apply; rebuilt web image and container-local `/accounts/login/` smoke returned HTTP 200.
- The required four-login browser lifecycle has not been manually run or claimed by the agent. The Day 4 gate is pending the owner's browser checklist below; no `day-4` tag is created. Day 2 browser gate/tag remain UNVERIFIED and GitHub CI remains unconfirmed.
- Code commit: `7a64f86` (`feat: add field resolution and verification workflow`).

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
