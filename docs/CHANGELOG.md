# Changelog

## 2026-11-25

- Fixed one route-inventory CI failure by classifying the unnamespaced Django admin index alongside the namespaced admin routes, retaining the staff-wrapper assertion.
- Corrected the legacy demo seed test to assert the current six phone-based roles and one-time password output, preserving all ward/category/routing checks.

## 2026-11-25

- Added environment aliases for deployment settings and a standard-library `DATABASE_URL` parser that always selects Django's PostGIS backend (deployment item 1).
- Added a Render startup command and atomic, idempotent PostGIS extension creation to the first geography migration; migration-ledger deletion is explicitly a deploy blocker (deployment item 2).
- Confirmed the public database health endpoint and route allow-list meet deployment item 3; existing tests cover its public response and generic DB failure.
- Standardized Gunicorn resource defaults at one worker and two threads, with Render/Compose ports supplied through environment (deployment item 4).
- Added two original, clearly labeled sample illustrations and idempotent demo complaints that restore missing private evidence files after restart (deployment item 5).
- Added a focused regression test for D6's configurable OSM tile URL, visible attribution, and exact CSP image-host allow-list (deployment item 6).
- Added the Render + Neon free-demo browser guide, with provider limits and the Neon permission gate recorded (deployment item 7).
- Attempted production `check --deploy`; host lacks Django and Docker engine access is denied, so item 8 is documented as not verified rather than reported green.
- Added privacy export, account deletion/anonymisation, retention cleanup and the rolling 12-hour session test (E.1–E.2).
- Added the first three-day citizen verification reminder, reduced role dashboards, and the scoped audit viewer with formula-safe CSV (E.3–E.5).
- Corrected the dashboard authorization test fixture. CI run 45601898000 passed on `6de99703e478dea3f5defbda3c2bc5e7965071ce`; `master` was fast-forwarded and `verified-phase1-2` was tagged at that exact SHA.
- Added a route authorization inventory test, completed the Ubuntu operations runbook, rewrote the README with the generated workflow table, and replaced this file with a concise changelog.
- Added a 10-minute lifecycle demo script and phone-based local demo accounts for all six roles; passwords remain random and are printed only on account creation.
- AI remains off and Playwright remains out of scope. The route inventory and documentation commits after the green run have not yet been CI-verified.

## 2026-11-23

- Started the Django/PostGIS civic complaint workflow with phone-based citizen accounts, server-side role permissions, an append-only status/audit history, and CI checks.
- Recorded scope decisions, design references, privacy/retention limits, and deployment prerequisites in `docs/`.
