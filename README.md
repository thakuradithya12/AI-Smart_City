# AI Smart City

AI Smart City is a Django website for citizens to report civic problems with a photo and map pin, and for city teams to route, assign, complete, and independently verify the work. Status and audit history support accountability; AI suggestions are disabled and never make decisions.

## Demo

- **Live demo:** TODO — owner to supply the current Render URL. No live URL is claimed until it is tested.
- **Screenshots:** [docs/screenshots/](docs/screenshots/README.md) is an empty placeholder for owner-approved screenshots.

## Complaint workflow

The status labels, outgoing transitions and permitted roles below are generated from [`docs/WORKFLOW.md`](docs/WORKFLOW.md), which is generated from the transition table in `apps/workflow/services.py`. Run `python scripts/sync_readme_workflow.py` after regenerating the workflow reference.

<!-- WORKFLOW_TABLE_START -->

| Status | Allowed transitions |
|---|---|
| `submitted` — Submitted | `in_triage` (System); `cancelled` (Admin, Citizen) |
| `in_triage` — In triage | `info_requested` (Triage reviewer); `routed` (Admin, Triage reviewer); `rejected` (Admin, Triage reviewer); `cancelled` (Admin, Citizen) |
| `info_requested` — Information requested | `in_triage` (Citizen, System); `cancelled` (Admin, Citizen) |
| `routed` — Routed | `acknowledged` (Department official, Supervisor); `in_triage` (Department official, Supervisor); `cancelled` (Admin, Citizen) |
| `acknowledged` — Acknowledged | `assigned` (Department official, Supervisor); `cancelled` (Admin) |
| `assigned` — Assigned | `in_progress` (Field worker); `cancelled` (Admin) |
| `in_progress` — In progress | `resolved_pending_verification` (Field worker); `cancelled` (Admin) |
| `resolved_pending_verification` — Awaiting verification | `verified_closed` (Citizen, Supervisor); `reopened` (Citizen, Supervisor); `cancelled` (Admin) |
| `verified_closed` — Verified closed | None (terminal) |
| `rejected` — Rejected | None (terminal) |
| `cancelled` — Cancelled | None (terminal) |
| `reopened` — Reopened | `assigned` (Supervisor); `cancelled` (Admin) |

<!-- WORKFLOW_TABLE_END -->

## Roles

| Role | Responsibility |
|---|---|
| Citizen | Submit reports, follow their own complaints, and confirm or dispute a claimed fix. |
| Triage reviewer | Review new reports, choose a category and department, request information, or reject with a reason. |
| Department official | Acknowledge department work, transfer with a reason, and assign a field worker. |
| Field worker | See assigned work, add before/after evidence, and record a work-completion claim. |
| Supervisor | Assign department work, verify completion, or reopen disputed work. |
| Admin | Manage users and configuration; administrative overrides are audited. |

Complaint queries are scoped through `Complaint.objects.visible_to(user)`. A completion claim is stored separately from verification.

## Technology

- Django templates and Python 3.12
- PostgreSQL with PostGIS; the Render demo target uses Neon only as its PostgreSQL provider
- Docker Compose for local development; Render Docker for the free demo host
- Gunicorn and WhiteNoise; Caddy is available for a self-managed HTTPS deployment
- Locally vendored Bootstrap and Leaflet; OpenStreetMap tiles with attribution for demo traffic

## Run locally

Requires Docker Desktop with its Linux engine and Docker Compose. These three PowerShell commands copy the example settings, start PostGIS and Django, then migrate and seed synthetic demo data:

```powershell
Copy-Item .env.example .env
docker compose up --build -d db web
docker compose exec web python manage.py migrate; docker compose exec web python manage.py seed_demo
```

Open `http://localhost:8000/`. The seed creates six synthetic role accounts and sample complaints with original illustration photos. It prints random passwords once when creating accounts. Use only a disposable local database; do not seed a production service.

## Run checks

```powershell
docker compose run --rm checks
docker compose exec web python manage.py check --deploy --settings=config.settings.prod
```

The checks service runs migration drift detection, pytest, Ruff, Bandit, and pip-audit. A commit is CI-verified only when the owner-provided Actions evidence shows success on that exact SHA; see [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

## Deploy

The current demo target is Render for the Docker web app and Neon for PostgreSQL only. Follow the [free Render + Neon deployment guide](docs/DEPLOY_FREE.md). The [Ubuntu runbook](docs/RUNBOOK_UBUNTU.md) covers a separately managed VM. Account, domain, and live URL values remain owner-supplied.

## Limits and project status

- AI classification is off. There is no trained model or reviewer suggestion.
- The seeded Hyderabad ward is synthetic demo geography, not an authoritative municipal boundary.
- Development email uses Django's console backend. SMTP delivery is not configured for the free demo.
- Render free storage is ephemeral: uploaded evidence photos can be lost on restart or redeploy. Do not use real complaints or photos on the demo.
- The free Render service does not run the application scheduler; reminders and scheduled retention cleanup are not available there.
- There is no official government integration. Map pins and photos can be imperfect evidence.
- The live demo URL, exact-head CI status, real pilot geography, and physical-device acceptance are not verified here. Check the test report and current `_ci` files before making a release claim.

## Project documents

See [`docs/README.md`](docs/README.md) for the document index. The project code and content are **All rights reserved**; no open-source license is granted. Third-party asset notices remain beside the vendored files.
