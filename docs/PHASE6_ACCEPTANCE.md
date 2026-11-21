# Phase 6 acceptance and handoff

Date: 2026-11-21 (Asia/Kolkata)

## Verification record

| Gate | Result | Evidence and limits |
| --- | --- | --- |
| Full automated regression | Passed locally | Final Docker Compose checks: migrations `No changes detected`; 58 tests passed in 62.03s; Ruff passed; Bandit 0 findings across 1,453 lines; `pip-audit` found no known vulnerabilities. See [`TEST_REPORT.md`](TEST_REPORT.md). |
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
| Exact final commit and tag | Not produced | Tests were run on a dirty working tree based on `ada8fa5813d98b962a6f09f8b7361983661bfe9d`. Git metadata is read-only in this workspace, so no Phase 6 commit or day tag could be created. This is not evidence for an exact final commit. |

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
- [ ] Commit the exact verified release and rerun gates against that commit.

Phase 6 is **locally verified but not release-complete**. No unsupported gate is marked done.
