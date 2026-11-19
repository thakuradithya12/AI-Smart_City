# Day 2 local citizen flow

## Routes

- `/accounts/login/` — sign in with email and password.
- `/register/` — create and sign in to a citizen account.
- `/` — signed-in home. Citizens can start a report or open their complaints.
- `/complaints/new/` — submit category, optional description, required photo, confirmed coordinates, and consent.
- `/complaints/` — the signed-in citizen's own reports.
- `/complaints/<id>/` — report detail, evidence image, and status timeline. Other users receive 404.
- `/evidence/<id>/` — authenticated display image, scoped by the same complaint visibility query.
- `/console/triage/` — reviewer queue with route, reject and information-request actions.
- `/console/department/` — department inbox for acknowledgement, transfer and assignment.
- `/console/field/` and `/console/field/<id>/` — assigned field tasks, start work, before/after evidence uploads and work claim.
- Complaint detail — chronological status, message and evidence timeline; citizen cancel/reply/confirm/dispute, supervisor verify/dispute/reassign actions when allowed by the state machine.

Run the local stack, apply migrations, and seed a demo square ward centered at coordinates you choose:

```powershell
docker compose up -d db web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo --lat <latitude> --lon <longitude>
```

The seed command creates a small demo ward, the six default categories, demo-labelled departments, and five demo roles with random passwords. The demo category routes use the same demo department as the seeded staff so a single set of demo logins can complete a lifecycle. It prints each new account's password once. With `DEBUG=False`, it refuses unless `--force` is supplied. Use test polygons for automated geography tests; do not treat the demo ward as pilot data.

## Local vendor assets

Bootstrap 5.3.8 (MIT) and Leaflet 1.9.4 (BSD-2-Clause) are loaded from `static/vendor/`; there are no runtime library CDN references. Fetch the official pinned files, verify the published hashes and PNG signatures, and save their licence notices in PowerShell:

```powershell
.\scripts\fetch_vendor_assets.ps1
```

The hashes above are from the official [Bootstrap 5.3 documentation](https://getbootstrap.com/docs/5.3/) and [Leaflet installation guide](https://leafletjs.com/install.html). Keep library notices with the vendored assets when packaging or redistributing them.
