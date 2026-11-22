# Current limits and unverified deliverables

This list distinguishes implemented local behavior from missing project inputs and acceptance evidence.

- **Pilot geography is not configured.** The project owner has not provided centre coordinates or authoritative ward boundaries. The local database contains a synthetic central-Hyderabad demo square only; it is not an administrative ward boundary, pilot geography, or evidence of service availability.
- **AI category suggestion is not delivered.** The requested owner-photo directory has been prepared at `ml/data/<category>/`, but no image files or grouping manifest are present yet. A read-only dataset preflight exists; there is no trained model, ONNX export, worker, measured evaluation, or AI suggestion in the reviewer UI. No performance metrics are claimed. Public datasets were not downloaded or used.
- **No live push updates are configured.** The server-rendered dashboard reads current database state on each page load. Users must refresh after a reviewer routes a complaint; no websocket, background notification, or auto-refresh feature is part of v1.
- **Production deployment is not delivered.** No public domain/server was supplied. Local production-setting checks do not constitute HTTPS deployment.
- **GitHub CI status is unverified.** Local Compose checks pass, but no remote Actions result was obtained.
- **Uptime and error tracking are not configured.** No provider was chosen or connected; live monitoring cannot be verified without a deployed environment and owner-approved service/account.
- **Production backup operations are unverified.** A local disposable restore passed and has a saved log. Scheduled production backups, restricted off-host retention, and a production restore remain untested.
- **Production security acceptance is incomplete.** The final local ZAP baseline reported 0 FAIL and 5 WARN categories. The remaining CSP/SRI/CDN warnings are tied to the supplied showcase's inline resources and external Tailwind/Lucide assets; those need bundling/refactoring before a strict CSP. The scan used local HTTP and Django's development server. Caddy HTTPS was exercised internally and stripped the upstream `Server` header, but the public production edge has not been deployed or scanned. See `docs/TEST_REPORT.md` and the final JSON/HTML reports.
- **Secret handling is local only.** The workspace `.env` ACL is restricted and the file is gitignored/untracked. No repository remote is configured, so remote secret-history scanning and GitHub Actions status are unavailable.
- **Phase 0.3 secret rotation is partial.** The local `DJANGO_SECRET_KEY` was regenerated without displaying it. The local PostgreSQL role password was not rotated because Docker/PostgreSQL is unreachable; changing only `.env` would desynchronize it from the existing database volume. Gitleaks v3 is configured to scan full history in CI, but no scanner executable or remote is available here, so the history scan is not verified.
- **Local media reconciliation is pending.** The development volume has six files with no current `Evidence` references. They were preserved because ownership and retention are uncertain; production cleanup/retention is not yet established.
- **Live-device acceptance is unverified.** Two physical phones, a desktop accessibility review, and a pilot user trial have not been evidenced here.
- **No official service integration exists.** The site is not connected to a municipal system.
- **Pilot data will be small until collected.** GPS pins and photos are imperfect evidence and may be inaccurate or incomplete.
- **AI, if later delivered, will assist a human reviewer only.** It must not route, prioritize, or close complaints automatically.
