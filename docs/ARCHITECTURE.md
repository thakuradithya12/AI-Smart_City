# Architecture

## System shape

AI SMART CITY is a server-rendered Django website backed by PostgreSQL with PostGIS. Django templates render the public landing, citizen report and operations pages. The landing shows real public update data from recent status events; the 47 supplied CivicOps screens remain design references only, and their sample names, counts, locations and complaint IDs are not database records.

```text
Browser
  └─ Caddy (production HTTPS) ── Gunicorn / Django
                                  ├─ accounts
                                  ├─ complaints ── workflow services
                                  ├─ console ────── permissions/query scoping
                                  ├─ geography ─── PostGIS ward polygons
                                  ├─ audit
                                  └─ PostgreSQL + private media volume
```

Local development uses the `db` and `web` Compose services. The `checks` profile runs migrations consistency, pytest, Ruff, Bandit and `pip-audit`. Production Compose adds Gunicorn and Caddy. The AI worker is an optional profile; no trained model, worker inference or AI suggestion is currently delivered.

## Responsibilities

- `apps/accounts` defines the email-login user and roles: citizen, triage reviewer, department official, supervisor, field worker and admin.
- `apps/geography` stores departments, categories, wards and versioned routing rules. Complaint locations are WGS84 points. Ward lookup uses the confirmed pin and effective ward geometry; GPS accuracy is metadata, not jurisdiction.
- `apps/complaints` owns complaint reporting, private image evidence, messages and the citizen-facing timeline. Evidence originals stay in private storage; authenticated views check complaint visibility.
- `apps/workflow` owns transition rules, permission helpers and business services. Status updates are atomic and create status history plus audit events. Views should call these services instead of assigning status directly.
- `apps/console` provides the role-scoped triage, department, field and supervisor actions.
- `apps/audit` stores append-only audit events. Status history and audit ORM writes reject updates and deletes.

## Complaint lifecycle

```text
submitted → in_triage → routed → acknowledged → assigned → in_progress
                                                       ↓
verified_closed ← resolved_pending_verification
                         ├─ supervisor/citizen dispute → reopened → assigned
                         └─ supervisor/citizen verify → verified_closed
```

Cancellation is available only before acknowledgement. Transfers return a complaint to triage with a reason. A department's work claim and the separate verification outcome are stored independently. Any transition not allowed by the state machine is refused.

## Reliability and privacy boundaries

- Complaint reporting does not wait for AI inference, email, geocoding or third-party map tiles. The report pin is checked against local ward data; without supported ward data, a report outside every configured ward is refused.
- Authorization defaults to deny. Complaint queries use `Complaint.objects.visible_to(user)` and unauthorized details are hidden with 404 responses.
- Complaint photos are private and delivered through authenticated evidence routes. HTML responses use `Cache-Control: no-store`.
- AI must only suggest a category to a human reviewer. AI output must not route, prioritize or close complaints. AI data/model inputs are absent, so the feature is disabled/not delivered.
- Production deployment, actual pilot geography, scheduled off-host backups, remote CI and live-device acceptance require external inputs or environments and are not proven by local tests.

See [`BACKEND_ROADMAP.md`](BACKEND_ROADMAP.md), [`RUNBOOK_UBUNTU.md`](RUNBOOK_UBUNTU.md), and [`LIMITS.md`](LIMITS.md) for current phase status and operations.
