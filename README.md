# AI SMART CITY

A Django website for citizens to report civic issues and follow their resolution. AI, if delivered, only suggests a category to a human reviewer.

## Local development

1. Install Docker Desktop with its Linux engine and Docker Compose.
2. Copy `.env.example` to `.env` and replace the local placeholder values.
3. Build and start the local PostGIS database and web app with `docker compose up --build`.
4. In another terminal run `docker compose exec web python manage.py migrate` and `docker compose exec web python manage.py createsuperuser`.
5. Open `http://localhost:8000/accounts/login/`.

The current scaffold has no generated database migrations yet. Generate and verify migrations before expecting login persistence or demo seeding to work. The public HTTPS deployment is not configured: no domain or server has been supplied. The Day 1 public deployment gate is blocked and is not claimed as passed. Pilot coordinates and hand-drawn ward polygons are also pending; no pilot location or ward is seeded.

## Current status and known limits

Day 1 implementation is in progress. Complaint workflow, evidence upload, ward data, AI training/inference, CI execution, backups, and deployment are not yet delivered. Do not use this skeleton for real complaints.
