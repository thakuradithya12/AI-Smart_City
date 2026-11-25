# AI Smart City

AI Smart City is a Django website for reporting civic problems and tracking the response. A citizen submits a complaint with a category, description, map pin and photo. Reviewers route it to a department; department staff assign a field worker; a supervisor or the citizen checks the work before the complaint is closed. Status changes and audit records are kept for accountability.

## Complaint workflow

The status labels, outgoing transitions and permitted roles below are generated from [`docs/WORKFLOW.md`](docs/WORKFLOW.md), which in turn is generated from the transition table in `apps/workflow/services.py`. Run `python scripts/sync_readme_workflow.py` after regenerating the workflow reference.

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

| Role | Main responsibility |
|---|---|
| Citizen | Submit reports, follow their own complaints, and confirm or dispute a claimed fix. |
| Triage reviewer | Review incoming reports, select a department, request information, or reject with a reason. |
| Department official | Acknowledge department work, transfer with a reason, and assign a field worker. |
| Field worker | See assigned tasks, add before/after evidence, and record a work-completion claim. |
| Supervisor | Assign or reassign department work and verify or reopen claimed fixes. |
| Admin | Manage application configuration and users; administrative overrides are audited. |

Complaint access is scoped on the server by `Complaint.objects.visible_to(user)`. A work-completion claim and the verification outcome are separate records; a claim never closes a complaint by itself.

## Run locally

The local setup needs Docker Desktop with the Linux engine and Docker Compose. It starts Django with PostGIS and uses private local media storage.

```powershell
Copy-Item .env.example .env
docker compose up --build -d db web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

Open `http://localhost:8000/`. The seed command creates a synthetic Hyderabad demo ward, six demo role accounts, and two sample complaints with repository-created illustration photos. The images are explicitly marked as illustrations, not real evidence. It generates random passwords and prints each new password once; store them securely for the session. The demo seed is for a disposable development database only.

## Run checks

```powershell
docker compose run --rm checks
docker compose run --rm -e DJANGO_SETTINGS_MODULE=config.settings.prod -e DJANGO_SECRET_KEY=local-check-only-change-before-use -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 -e DJANGO_CSRF_TRUSTED_ORIGINS=https://localhost web python manage.py check --deploy
```

The checks service runs the migration drift check, pytest, Ruff, Bandit and pip-audit. The second command runs Django's production configuration check; its HSTS warnings should be reviewed against the configured production host. GitHub Actions runs the checks on pushes and pull requests. A change is CI-verified only when the run evidence names that exact commit SHA.

## Limits and current operating status

- **AI is off.** No classifier model or inference is delivered. AI may not route, prioritize or close complaints; E.6 and browser automation are outside the current delivery cut.
- **Geography is demo-only.** The seed ward is a synthetic area around Hyderabad and is not an authoritative municipal boundary. Pilot coordinates and ward data are still required.
- **Email is console-only in local development.** Local email is printed by Django's console backend. Production delivery needs owner-supplied SMTP settings; SMS/OTP is not implemented.
- **D1 deployment inputs are owner to supply.** No public server/domain values are assumed. Do not treat the local deployment as a live HTTPS pilot.
- **This is not an emergency service.** Location pins and photos can be imperfect evidence, and the project has no official government integration.

## Project documents

- [Local and production operations runbook](docs/RUNBOOK_UBUNTU.md)
- [Free Render + Neon demo deployment](docs/DEPLOY_FREE.md)
- [10-minute lifecycle demo](docs/DEMO_SCRIPT.md)
- [Workflow reference](docs/WORKFLOW.md)
- [User guide](docs/USER_GUIDE.md)
- [Privacy and retention notice](docs/PRIVACY.md)
- [Limits](docs/LIMITS.md)
- [Test report](docs/TEST_REPORT.md)
- [Changelog](PROGRESS.md)
