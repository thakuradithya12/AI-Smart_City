# Progress

## 2026-11-19 — Day 2 validation recovery (in progress)

- Owner's Docker output confirms the app image builds and `python manage.py check` reports no issues. Direct `pytest` and `ruff` commands in the `web` service failed because that image installs only `requirements/base.txt`.
- Added a Compose `checks` service that installs the development requirements in its disposable container, then runs pytest, Ruff and pip-audit. Next: owner reruns `docker compose run --rm checks` and returns the output; fix any findings before committing the Day 2 chunks.
- The first two check-service runs used the cached copied source and therefore still executed the earlier login test; bind-mounted the working tree into the service so the same verification command always sees edits.
- The latest full check run reached migration consistency (`No changes detected`) but pip timed out downloading Ruff before tests started. Increased the dev requirements install timeout and retries to match the app image.
- Latest owner-provided Docker evidence: migration consistency reported `No changes detected`; full pytest reported `18 passed`; Ruff reported `All checks passed!`; pip-audit reported `No known vulnerabilities found`.
- The report flow, private evidence endpoint, system transition and seed command are covered by those tests. Local Ruff and compile checks also pass in this workspace.
- Day 2 browser gate remains pending: vendor asset files are absent (network DNS prevented fetching them here; a hash-verifying PowerShell script is ready), and no test coordinates were provided for a manually seeded demo ward. No browser smoke result or `day-2-local` tag is claimed. Tested implementation committed as `26d5c97` while awaiting those gate inputs.
- Bootstrap and Leaflet downloads were attempted but DNS resolution failed in this workspace; vendor assets are not yet present.

## 2026-11-19 — Day 2 local gate completed

- Owner reported that the localhost browser flow passed: vendor assets downloaded, demo ward seeded, registration and login, photo and pin report, My complaints timeline, outside-ward refusal, and cross-user detail/evidence 404.
- Automated Docker evidence: migration consistency `No changes detected`; pytest `18 passed`; Ruff clean; pip-audit `No known vulnerabilities found`.
- Tagged `day-2-local` after the browser gate report. The owner supplied the GitHub CI field as an unresolved `[green / red: paste error]` placeholder; CI status is pending and not inferred.
- Note: the vendor files described as downloaded were not visible in this shared worktree when checked. The report records the owner's localhost test; ensure those files are present in the versioned project checkout before another environment deploys it.

## 2026-11-19 — Day 3 (in progress)

- Planned scope: exhaustive state-transition and role permission tests; triage queue; department inbox; route, acknowledge, reject, transfer and assign actions with reasons where required; status and audit event coverage.
- No deployment or public HTTPS claim. Continue local Docker verification in small chunks and wait for owner-provided output after each chunk.
- Chunk 1 completed: added role- and visibility-scoped transition helpers; tests every defined status pair against each role, including status/audit event writes and information-message audit records. Docker evidence: focused `pytest -q tests/test_workflow_transitions.py` — `3 passed`; full `pytest -q` — `21 passed`; migration check — `No changes detected`; Ruff clean; pip-audit `No known vulnerabilities found`.

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
