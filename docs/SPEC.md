# AI SMART CITY v1 product specification

## Goal

Citizens submit civic reports with a category, optional description, photo, and confirmed map pin. A human reviewer triages and routes each report. A department acknowledges and assigns the work; a field worker records evidence and claims completion; a supervisor or citizen verifies or disputes the result. Status history and audit records preserve the decisions.

## Roles and access

- **Citizen:** create reports; view and act on their own reports only; cancel before acknowledgement; reply to information requests; confirm or dispute a resolution.
- **Triage reviewer:** view the triage queue, request information, route or reject with a reason, and link a report to a potential duplicate after review.
- **Department official:** act on reports routed to their department; acknowledge, transfer with a reason, and assign a worker in the same department.
- **Field worker:** view assigned work only; add before/after evidence and a work note; claim work complete.
- **Supervisor:** manage their department's work and workers; verify, dispute/reopen, assign or reassign.
- **Admin:** manage configuration and accounts. Workflow status changes remain subject to the central transition service and audited reasons.

## Workflow rules

1. Submission creates the citizen report and photo evidence, confirms consent, checks the pin against an active local ward, and enters `in_triage`. Registration does not depend on AI, email, geocoding, or map tiles.
2. A reviewer routes using an active category/ward rule or records a reason for an override. The routing rule version is audited. The department sees the complaint only after routing.
3. Department acknowledgement and assignment precede field work. Field completion is a claim; verification is a separate outcome.
4. A citizen or supervisor may verify or dispute the fix. Disputes reopen the work with a reason. Citizen silence never closes a report.
5. Only the workflow service writes statuses. Status events and audit events are append-only through application operations.
6. Duplicate suggestions are advisory: same category, open state, 30 m, last 7 days. A triage reviewer may link a candidate; this does not delete, hide, or close either report.

## Geography and demo data

The project stores WGS84 points and uses an effective ward boundary to decide jurisdiction. GPS coordinates alone do not determine the responsible department. The local seeded Hyderabad square is synthetic demo coverage only. It is not an authoritative municipal ward or pilot area. Pilot geography stays unconfigured until the owner supplies coordinates and a source-documented boundary.

## Privacy and safety

Complaint photos are private and served only after the same complaint visibility check. The platform is not an emergency service. Collect account email/name and complaint information only; do not collect phone numbers or government IDs. AI, when delivered, may suggest a category to a human reviewer only.

## v1 exclusions

No mobile app/PWA, public complaint map/dashboard, messaging or phone integrations, autonomous AI decisions, municipal system integration, multi-city tenant screens, payment, or social login.

## Delivery state

The local Django/PostGIS workflow and automated suite are implemented. External release gates and undelivered AI inputs are itemized in [`LIMITS.md`](LIMITS.md) and [`PARKING_LOT.md`](PARKING_LOT.md). Local test results are recorded in [`TEST_REPORT.md`](TEST_REPORT.md); local passing checks do not claim public deployment or pilot acceptance.
