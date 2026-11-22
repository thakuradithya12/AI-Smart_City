# Backend completion roadmap

**Status:** maintained execution record, 2026-11-22. This roadmap follows the frozen v1 requirements in [`../AGENTS.md`](../AGENTS.md). It distinguishes local implementation evidence from release gates that need external inputs.

**Latest execution update:** Local complaint-to-department routing, the human-reviewed lifecycle, Telangana-only synthetic demo geography, duplicate review, and department default-deny scoping pass the Docker gate. The integrated suite reports 67 tests passing; see [`../docs/TEST_REPORT.md`](TEST_REPORT.md). AI training/inference remain blocked on rights-cleared photos and grouping metadata. Production deployment, authoritative pilot geography, remote CI and device acceptance still need owner-controlled inputs; see [`../docs/PARKING_LOT.md`](PARKING_LOT.md).

## Target

Complete and prove the existing Django/PostGIS service from complaint submission through verified closure, with role-scoped access, append-only history, safe evidence storage, production hardening, and an honest local or deployed operations runbook. The optional AI slice and duplicate flag come after the reliable human workflow. No React/API rewrite, autonomous decision-making, public complaint map, notification system, or other scope expansion.

## Repository baseline

The repository contains Django models and migrations, email login and citizen registration, report submission with ward containment and private image storage, role-aware complaint query scoping, triage/routing, department assignment, duplicate review, field evidence, work claims, separate verification/dispute, status/audit events, a local demo seed, Docker Compose, CI configuration, and deployment/backup scripts. Local Docker evidence is current as of 2026-11-22. This does not prove GitHub CI, a production deployment, real pilot ward data, production backups/restore, or full device acceptance.

## Phase 0 — Establish a trustworthy starting point

**Work**

1. Review `git status`, current diff and recent commits; identify and preserve the pending UI work and unrelated edits. Do not reset or overwrite user work.
2. Start Docker Desktop's Linux engine and confirm `docker compose ps` and `docker compose config --quiet`.
3. Rebuild from the current source, start PostGIS and web, apply migrations, then run the existing checks service and production `check --deploy` command documented in `docs/RUNBOOK_UBUNTU.md`.
4. Open the current local site and verify login, report flow and the role dashboards against the running code. Record exact command output and any errors in `PROGRESS.md`.
5. Add missing canonical documents: `docs/LIMITS.md`, `docs/TEST_REPORT.md`, `docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md` (or update their equivalent if created meanwhile). Separate known implementation from verified implementation.

**Gate:** reproducible current-HEAD local build and checks, or a concise blocker log with the exact failing command. Do not call CI green without the run result.

## Phase 1 — Close core workflow and data-integrity gaps

**Work**

1. Compare each model and workflow transition to AGENTS.md sections 6–8. Fix only discrepancies needed for the defined lifecycle; add migrations only when the data model requires them.
2. Ensure complaint creation, initial `submitted → in_triage`, first evidence, audit record, generated public ID and due date commit or roll back atomically. Confirm registration does not call AI, email, geocoding or external map services.
3. Confirm every status mutation uses `transition()` and its transaction/row lock; ensure required fields and actor-role checks cover all allowed and forbidden transitions. Audit overrides and routing rule versions.
4. Confirm resolution claim fields remain separate from verification outcome, and citizen silence never closes a complaint.
5. Test append-only protections for both `StatusEvent` and `AuditEvent`; if practical, enforce database-role UPDATE/DELETE revocation without breaking migrations/admin reads.

**Tests/gate:** exhaustive transition-role matrix; status and audit writes; append-only save/delete; full lifecycle; dispute/reopen; cancel; AI-offline submission; code scan finds no status writes outside the workflow module. Current evidence goes into `docs/TEST_REPORT.md` only after a real run.

## Phase 2 — Close authorization and evidence security

**Status: local checks pass (2026-11-21).** The current focused scope includes active-account visibility, serialized field evidence writes, rollback cleanup, stale-state protection, and Bandit in local checks/CI. See the dated results in `docs/TEST_REPORT.md`; continue broader production review in Phase 5.

**Work**

1. Audit every detail, evidence and action URL against `Complaint.objects.visible_to(user)` and default-deny permission helpers. Unauthorized objects return 404. Verify field workers only see their assigned tasks and staff cannot cross departments.
2. Verify image validation (JPEG/PNG/WebP, byte and pixel limits, Pillow verify/reopen), unchanged private originals, SHA-256, EXIF-free display copies, and authenticated evidence delivery.
3. Check CSRF, safe methods, server-side validation, output escaping, login lockout and report rate limiting. Confirm forwarded-client-IP behavior only trusts proxy headers overwritten by Caddy.
4. Review Django admin for read-only workflow records and no bypass path that directly edits status or mutates append-only events.

**Tests/gate:** IDOR coverage for each route family, evidence URLs, upload rejection/hash/EXIF cases, limiter cases, and admin write protections. Run dependency audit and Bandit; resolve or document findings with concrete evidence.

## Phase 3 — Complete geography and routing setup

**Status: generic logic and local checks pass; real pilot setup is blocked on owner data.** `Ward.objects.active_on()` filters the point-in-ward lookup by effective dates, and a database constraint rejects invalid ward date windows. Routing tests prove ward-specific precedence, future-rule exclusion, rule-version audit, and visible safety-critical notices. Duplicate suggestions use geography distance in metres, same-category/open-state filters and a seven-day window, with reviewer-controlled audited linking. The synthetic central Hyderabad demo area does not establish any real service area.

**Work**

1. Obtain pilot centre coordinates and authoritative ward boundary/source/effective dates from the project owner. The repository clarification explicitly says these are unresolved and must not be guessed.
2. Load or enter the real ward polygons and routing rules; verify point-in-ward with known inside/outside points. GPS accuracy is descriptive only; the confirmed pin and ward polygon determine jurisdiction.
3. Confirm routing rule precedence, effective dating and version audit; show safety-critical category warnings to reviewers.
4. Optional duplicate review is implemented locally with a 30 m geography query, a seven-day open-report window, reviewer-only linking and audit evidence. Its tests use known near/far PostGIS points.

**Gate:** source-documented ward data and tests for inside/outside/routing precedence. If coordinates or authoritative boundary source remain unavailable, keep location-specific reporting blocked and record that limit; never create fictitious pilot geography.

## Phase 4 — Optional AI slice (only after Phases 1–3 core gates)

**Status: model work not started; secure data-intake preflight only.** The user selected `ml/data/<category>/` as the photo location, and empty category folders are ready. The read-only preflight is covered by tests. Its real-data run exits 1 because no photos or `manifest.csv` are present. Do not train, export ONNX, or claim metrics until actual files arrive, groups are verified, and the Phase 3 core gate is satisfied.

The model slice is not being marked complete by the preflight work. `other` remains evaluation-only, and no public dataset was downloaded.

**Work**

1. Re-check current official dataset licenses and model/runtime documentation before selecting dependencies or downloading data. No unclear rights.
2. Confirm 3–5 licensed, product-matching classes and a group/source-based held-out split that prevents near-identical leakage. If qualified data cannot be obtained within the timebox, drop AI and record it in `docs/LIMITS.md`.
3. Implement `classify(image_path)` with ONNX Runtime CPU and a configurable model path; missing model disables the feature.
4. Implement the small polling management command: bounded timeout, one retry maximum, safe failure state, no impact on registration. Persist suggestions and reviewer accept/correction separately.
5. Set the confidence threshold before held-out evaluation. Produce per-class precision/recall/F1 and confusion matrix from actual held-out runs. The reviewer sees “AI suggestion, not a decision”; no automatic routing, status, priority or closure.

**Gate:** model provenance, licenses, split method, threshold, measured metrics and limits all present under `ml/`; worker-off report creation passes. Otherwise record “not delivered” and stop this phase.

## Phase 5 — Production readiness and operations

**Status: local checks and disposable restore rehearsal pass; production deployment remains blocked.** See the dated restore log at [`restore-test-2026-11-21.log`](restore-test-2026-11-21.log). One local private-media volume contains six files with no matching current Evidence records; these were preserved pending ownership/retention review.

**Work**

1. Run current-HEAD `check --deploy`, dependency audit, Bandit, CI and OWASP ZAP baseline against a permitted staging target; review findings, do not merely save raw reports.
2. Validate production settings, secret injection, hosts/CSRF origins, Caddy HTTPS, secure cookies, proxy SSL header, HSTS policy, and report/login limits. Do not enable production until real domain/server values exist.
3. Exercise backup and restore scripts on a disposable environment, save the actual restore log, verify database sanity counts and media availability. Restrict/encrypt off-host copies.
4. Review rollback behavior, especially the fact database migrations are not automatically reversed. Complete the README runbook and environment variable inventory.
5. Configure only reputable uptime/error tracking services whose terms and data handling are clear; otherwise mark optional monitoring as not delivered.

**Gate:** production `check --deploy` output, scan/audit review, successful disposable restore log and documented deploy/rollback/restore instructions. Public HTTPS is a separate gate and needs real owner-provided domain/server access.

## Phase 6 — End-to-end acceptance and handoff

**Status: local regression and documentation gates pass; release acceptance remains incomplete.** Current evidence and the item-by-item remaining checklist are in [`PHASE6_ACCEPTANCE.md`](PHASE6_ACCEPTANCE.md) and [`PARKING_LOT.md`](PARKING_LOT.md). The worktree has no Git remote; each verified local change is committed, but remote CI and public release are not claimed.

1. Run the complete test suite, lint, dependency audit, production checks and CI on the exact final commit. Record counts/results with commit SHA in `docs/TEST_REPORT.md`.
2. Exercise fresh demo accounts for citizen → triage → official → field worker → supervisor/citizen verification; also dispute/reopen/reassign and cancellation. Demo passwords are random, printed once, and must not be committed or posted in chat.
3. Check report and triage UI on two real phones and one desktop; keyboard and contrast checks; record any untested device as unverified.
4. Complete README, architecture, user guide, limits, recovery instructions and demo rehearsal. Review all AGENTS.md definition-of-done items and mark any unsupported item as not done with evidence.
5. Commit the completed phase with a clear message. Apply `day-N` tags only when the corresponding day gate genuinely passed; do not move historical tags.

## Execution order and stop rules

Work in this order: establish baseline → integrity/state machine → authorization/evidence → real geography → optional AI/duplicate → production operations → final acceptance. Each coherent change gets focused tests and a local smoke check; each gate gets the full suite. If a gate fails, fix the cause or cut optional scope per AGENTS.md. Never trade away the human-reviewed lifecycle, audit trail, access controls, backups/restore evidence, or transition tests to make a date.

### Owner inputs still required for specific gates

- Pilot centre latitude/longitude and authoritative ward boundary data/source: required before real ward setup.
- Public domain and server/PaaS details: required before public HTTPS deployment.
- GitHub CI run result: not inferable from local runs.
- Any additional college format/technology constraint: none supplied; locked stack currently applies.
