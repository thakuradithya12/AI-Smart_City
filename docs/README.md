# Documentation index

This index links the maintained project documents. Historical reports retain the facts and command results recorded at the time; check their dates and SHAs before treating them as current.

## Product and operations

- [Architecture](ARCHITECTURE.md) — application components, complaint lifecycle, and privacy boundaries.
- [User guide](USER_GUIDE.md) — citizen and staff task instructions.
- [Demo script](DEMO_SCRIPT.md) — timed role-by-role demo walkthrough.
- [Free Render + Neon deployment](DEPLOY_FREE.md) — browser setup for Render web hosting and Neon PostgreSQL.
- [Ubuntu runbook](RUNBOOK_UBUNTU.md) — operations for a separately managed Ubuntu VM.
- [Privacy](PRIVACY.md) — consent, export, deletion, and retention rules.
- [Limits](LIMITS.md) — current feature, deployment, and evidence limitations.
- [Changelog](CHANGELOG.md) — dated project changes.

## Design and decisions

- [Specification](SPEC.md) — product scope and core requirements.
- [Owner clarifications](CLARIFICATIONS.md) — binding project decisions supplied by the owner.
- [Technical decisions](DECISIONS.md) — recorded implementation choices and reasons.
- [Design system](DESIGN_SYSTEM.md) — visual tokens and reusable UI rules.
- [UI design](UI_DESIGN.md) — interface direction and screen planning.
- [UI reference archive](ui_reference/README.md) — mockups for reference only; not served by the app.
- [Screenshots placeholder](screenshots/README.md) — TODO for owner-approved, non-sensitive screenshots.

## Workflow and verification

- [Workflow](WORKFLOW.md) — generated status and role transition reference.
- [Test report](TEST_REPORT.md) — dated command results, CI run IDs, SHAs, and verification limits.
- [Phase 6 acceptance snapshot](PHASE6_ACCEPTANCE.md) — historical acceptance evidence and remaining gates.
- [Performance notes](PERFORMANCE.md) — local performance observations and follow-up checks.
- [Cleanup report](CLEANUP_REPORT.md) — tracked/untracked inventory, reference checks, and cleanup actions.
- [ZAP configuration](zap.yaml) — baseline scan configuration.
- [ZAP baseline, initial HTML](zap-baseline-2026-11-21.html) — saved local scan output.
- [ZAP baseline, initial JSON](zap-baseline-2026-11-21.json) — machine-readable local scan output.
- [ZAP baseline, final HTML](zap-baseline-2026-11-21-final.html) — reviewed local scan output.
- [ZAP baseline, final JSON](zap-baseline-2026-11-21-final.json) — machine-readable reviewed scan output.
- [Restore test log](restore-test-2026-11-21.log) — evidence from the local disposable restore rehearsal.

## Internal working notes

- [Internal notes index](internal/README.md) — explains the purpose and handling of working notes.
- [Agent instructions](internal/AGENTS.md) — frozen scope, architecture, security and test requirements.
- [Repository understanding](internal/UNDERSTANDING.md) — implementation observations and validation checklist.
- [Parking lot](internal/PARKING_LOT.md) — deferred work and unresolved external gates.
- [Decisions needed](internal/DECISIONS_NEEDED.md) — owner inputs that block specific tasks.
- [Backend roadmap](BACKEND_ROADMAP.md) — implementation phases and acceptance work.
- [Roadmap V2](ROADMAP_V2.md) — owner-amended roadmap and phase gates.

## AI data planning

- [`ml/DATASETS.md`](../ml/DATASETS.md) — dataset rights and suitability review; no training data is included.
- [`ml/DATA_INTAKE.md`](../ml/DATA_INTAKE.md) — owner-data intake and preflight constraints.
