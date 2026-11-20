# AI SMART CITY

A Django website for citizens to report civic issues and follow their resolution. AI, if delivered, only suggests a category to a human reviewer.

## Local development

1. Install Docker Desktop with its Linux engine and Docker Compose.
2. Copy `.env.example` to `.env` and replace the local placeholder values.
3. Build and start the local PostGIS database and web app with `docker compose up --build`.
4. In another terminal run `docker compose exec web python manage.py migrate` and `docker compose exec web python manage.py createsuperuser`.
5. Open `http://localhost:8000/accounts/login/`.

Initial migrations for the model-bearing apps are included. The public HTTPS deployment is not configured: no domain or server has been supplied. The Day 1 public deployment gate is blocked and is not claimed as passed. Pilot coordinates and hand-drawn ward polygons are also pending; no pilot location or ward is seeded.

## Current status and known limits

The local citizen and staff complaint lifecycle is implemented through report submission, triage/routing, department assignment, field evidence and work claims, and separate verification/reopen actions. The CivicOps UI archive integration is documented in [`docs/UI_DESIGN.md`](docs/UI_DESIGN.md), with the extracted screens in [`docs/ui_reference/`](docs/ui_reference/).

The public HTTPS deployment remains unconfigured because no domain or server has been supplied. Pilot centre coordinates and authoritative ward boundaries are pending. AI training and inference were not delivered; the candidate dataset research is documented in [`ml/DATASETS.md`](ml/DATASETS.md). Latest deployment and verification limits are recorded in [`PROGRESS.md`](PROGRESS.md) and [`docs/LIMITS.md`](docs/LIMITS.md).

Day 2 local routes, demo seeding and the vendor asset download/check command are documented in [`docs/README.md`](docs/README.md).

## Production operations

The detailed fresh Ubuntu VM, deploy, rollback, backup, and restore commands are in [`docs/RUNBOOK_UBUNTU.md`](docs/RUNBOOK_UBUNTU.md). Do not deploy until a real server/domain and pilot location have been supplied and reviewed.
