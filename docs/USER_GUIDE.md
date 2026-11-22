# User guide

## Open the local site

Start the local app and database, then apply migrations:

```powershell
docker compose up -d db web
docker compose exec web python manage.py migrate
```

Open `http://localhost:8000/`. The public landing page is a supplied UI mockup. `/ui-showcase/` lists 47 static screens for visual review; mockup names, metrics, complaint IDs and locations are sample content. They do not represent live complaint data.

Sign in at `/accounts/login/` or register a citizen account at `/register/`. Staff accounts are provisioned by an administrator. Do not use demo accounts or passwords on a public server.

## Citizen tasks

1. Sign in or register.
2. Open `/complaints/new/`, select a category, attach a photo, and enter a description if useful.
3. Place and confirm the pin. Browser geolocation may require HTTPS and location permission; the pin can be positioned manually.
4. Read and accept the privacy consent, then submit. The platform is not an emergency service.
5. Review `/complaints/` and open a report to see status history, messages and evidence.
6. Before acknowledgement, cancel if appropriate. When a resolution is pending verification, confirm or dispute it with a reason.

Reports are accepted only inside an active configured ward. No owner-supplied pilot coordinates or authoritative ward boundaries are configured here, so local demo ward data is not evidence of a real service area.

## Staff tasks

| Role | Page | Main actions |
| --- | --- | --- |
| Triage reviewer | `/console/triage/` and complaint detail | Review the queue, request information, route to a department, reject with a reason, and review/link nearby duplicate candidates. |
| Department official | `/console/department/` | Acknowledge, transfer with a reason, and assign to a worker in the department. |
| Field worker | `/console/field/` | View assigned work only, start it, upload before/after evidence, and submit a work note. |
| Supervisor | Complaint detail and department screens | Reassign, verify a work claim, dispute/reopen with a reason, and choose an eligible assignee. |
| Admin | `/admin/` | Manage users and configuration. Workflow events remain append-only through the application ORM. |

The sequence is submit → triage → route → acknowledge → assign → work in progress → pending verification → verified or reopened. The department inbox shows reports only after a triage reviewer routes them; dashboards update on page load, so reload after another role changes a report. The work-done claim is not itself a verified closure. The server enforces status and role rules for every action.

## Local demo data

`seed_demo` creates demo-labelled departments, categories, a synthetic square ward centered in Hyderabad, Telangana, and role accounts with random passwords printed once. The location is fixed to keep the demo area in Telangana. This is not an authoritative ward boundary or pilot geography. Use only in a disposable local development database; never run demo seeding against production. The command requires `--force` when Django debug mode is off; do not use that flag to seed a production system.

## Privacy and support

The app stores account email/name, complaint details, locations and evidence photos. Do not submit secrets, identity documents or unrelated personal information. Evidence is private to users authorized for its complaint. No automatic complaint/photo deletion is configured: an owner-approved retention period and deletion process must be set before public deployment. Keep local `.env` values private and rotate any exposed credential.

The project has no municipal system integration and no public-domain deployment. Report outside-area errors indicate that ward data is missing or the chosen pin is unsupported; do not invent or adjust a pin merely to force a submission.

See [`docs/README.md`](README.md) for local flow and vendor assets, and [`RUNBOOK_UBUNTU.md`](RUNBOOK_UBUNTU.md) for deployment, rollback and restore instructions.
