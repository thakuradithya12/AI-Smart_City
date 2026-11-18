# Progress

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
