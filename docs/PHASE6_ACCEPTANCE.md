# Phase 6 acceptance and handoff

Date: 2026-11-21 (Asia/Kolkata)

This is a dated snapshot from 2026-11-21. Later remote and CI changes are documented in [`TEST_REPORT.md`](TEST_REPORT.md); the historical statements below describe only the state on this snapshot date.

## Verification record

| Gate | Result | Evidence and limits |
| --- | --- | --- |
| Full automated regression | Passed on committed code | Post-commit Docker Compose checks on `e806d63799ebb374d644b1746465d2ae858769b7`: migrations `No changes detected`; 58 tests passed in 57.76s; Ruff passed; Bandit 0 findings across 1,453 lines; `pip-audit` found no known vulnerabilities. See [`TEST_REPORT.md`](TEST_REPORT.md). |
| Production settings | Passed locally with warnings | `check --deploy` exited 0 with the actual protected local Compose key. `security.W005` and `security.W021` remain because no stable owner domain was supplied. |
| Route smoke test | Passed locally | `/`, `/ui-showcase/`, `/ui-showcase/citizen_dashboard_mobile/`, `/accounts/login/` returned 200. `/workspace/` redirected unauthenticated users to login (200 after redirect). |
| Browser and accessibility review | Partial | Browser DOM and screenshot showed the public CivicOps landing page. The showcase index reports all 47 screens, and the citizen dashboard mockup rendered with the expected content. Added tests verify labelled report/triage controls, report validation error announcements and links, plus focus-indicator contrast ≥3:1 on white/canvas. The in-app viewport was narrow; no full desktop keyboard walkthrough or physical-device check is claimed. |
| Lifecycle and dispute paths | Covered by automated tests | `test_four_user_full_lifecycle_separates_claim_and_verification`, `test_dispute_reopens_and_supervisor_reassigns`, cancellation and access tests in `tests/test_day4_workflow.py`; state/role matrix and direct-assignment guard in `tests/test_workflow_transitions.py`. These are automated fixtures, not a live fresh-account rehearsal. |
| Backup/restore | Passed locally | Disposable PostGIS and media restore log: [`restore-test-2026-11-21.log`](restore-test-2026-11-21.log). Production schedule/off-host backup remains unverified. |
| Passive web scan | Passed with reviewed warnings | Final local ZAP report: 0 FAIL, 5 WARN categories, 57 PASS across 128 URLs. Not a production scan or active penetration test. |
| GitHub CI | Unverified | No repository remote is configured. No remote Actions run was obtained. |
| Public HTTPS deployment | Not delivered | Domain/server/PaaS inputs are absent; only the local Caddy proxy behavior was exercised. |
| Two-phone and full accessibility acceptance | Partial / not run | Automated template and focus contrast checks pass. No two physical phones, full desktop keyboard walkthrough, screen-reader test, or pilot trial evidence is available. |
| AI and real pilot geography | Not delivered | Owner photo set/group manifest and authoritative ward data/coordinates remain absent; see [`LIMITS.md`](LIMITS.md). |
| Exact code commit | Created and verified locally | Commit `e806d63799ebb374d644b1746465d2ae858769b7` contains the tested application, regression tests and phase artifacts; post-commit full suite passed. The uploaded ZIP remains untracked and was excluded. No Git remote exists, so no push/CI run was possible. |
| Day tag | Not created | Phase 6 still has external acceptance gates; no `day-N` tag is claimed. |

## Handoff checklist

- [x] Architecture and role-based user guide written.
- [x] Current limitations and test results documented.
- [x] Local run, deploy, rollback and restore steps linked from the README.
- [x] Local disposable restore evidence retained.
- [ ] Owner supplies a public domain/server and authoritative pilot ward input.
- [ ] Owner runs or provides GitHub Actions result after changes are pushed.
- [ ] Run the fresh-account demo twice against an agreed environment; do not store or publish passwords.
- [ ] Test report and triage at two real phones plus a desktop; complete keyboard and contrast review.
- [ ] Configure production backups, retention, uptime/error monitoring, and perform a production restore rehearsal.
- [ ] Review remaining showcase CSP/SRI/CDN alerts before public release.
- [x] Create a local code commit and rerun the full gate against it.
- [ ] Push that commit and verify remote CI after a Git remote is configured.

Phase 6 is **locally verified but not release-complete**. No unsupported gate is marked done.

## 2026-11-22 local backlog follow-up

The later local backlog pass added a specification and deferred-work register, completed the duplicate-review feature with reviewer-only audited linking, added citizen-to-department visibility regression coverage, and fixed a department-null access-control gap. The Compose gate recorded at the time of this 2026-11-22 follow-up is documented in [`TEST_REPORT.md`](TEST_REPORT.md): 67 tests, Ruff, Bandit, and pip-audit passed; production configuration check exited 0 with the documented HSTS warnings. The web image was rebuilt and local routes smoke-tested. This does not satisfy the still-open public deployment, pilot geography, remote CI, production operations, licensed AI-data, or physical-device gates listed in [`internal/PARKING_LOT.md`](internal/PARKING_LOT.md).
