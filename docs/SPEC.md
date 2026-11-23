# AI SMART CITY v1 product specification

## Goal

Citizens submit civic reports with a category, optional description, photo, and confirmed map pin. A human reviewer triages and routes each report. A department acknowledges and assigns the work; a field worker records evidence and claims completion; a supervisor or citizen verifies or disputes the result. Status history and audit records preserve the decisions.

## Roles and access

- **Citizen:** create reports; view and act on their own reports only; cancel before acknowledgement; reply to information requests; confirm or dispute a resolution.
- **Triage reviewer:** view the triage queue, request information, route or reject with a reason, and link a report to a potential duplicate after review.
- **Department official:** act on reports routed to their department; acknowledge, transfer with a reason, and assign a worker in the same department.
- **Field worker:** view assigned work only; add before/after evidence and a work note; claim work complete. Department officials cannot submit the work-done claim.
- **Supervisor:** manage their department's work and workers; verify, dispute/reopen, assign or reassign.
- **Admin:** manage configuration and accounts; reassign active field work; route or reject in-triage complaints; cancel a stuck complaint in any active state with a reason. These workflow overrides pass through the central transition/service layer and are recorded as `admin_override` audit events.

## Workflow rules

1. Submission creates the citizen report and photo evidence, confirms consent, checks the pin against an active local ward, and enters `in_triage`. Registration does not depend on AI, SMS, email, geocoding, or map tiles.
2. A reviewer routes using an active category/ward rule or records a reason for an override. The routing rule version is audited. The department sees the complaint only after routing.
3. Department acknowledgement and assignment precede field work. Field completion is a claim; verification is a separate outcome.
4. A citizen or supervisor may verify or dispute the fix. Disputes reopen the work with a reason. Citizen silence never closes a report.
5. Only the workflow service writes statuses. Status events and audit events are append-only through application operations.
6. Duplicate suggestions are advisory: same category, open state, 30 m, last 7 days. A triage reviewer may link a candidate; this does not delete, hide, or close either report.

Category slugs remain stable in `Category.name`; the editable display label is shown to citizens and staff. Inactive categories cannot be selected for new reports. `default_department` is only preselected as a suggestion for triage; active routing rules remain authoritative.

## Geography and demo data

The project stores WGS84 points and uses an effective ward boundary to decide jurisdiction. GPS coordinates alone do not determine the responsible department. The local seeded Hyderabad square is synthetic demo coverage only. It is not an authoritative municipal ward or pilot area. Pilot geography stays unconfigured until the owner supplies coordinates and a source-documented boundary.

## Privacy and safety

Complaint originals are private, unchanged, and never served; display copies and thumbnails are re-encoded without EXIF and served only after the same complaint visibility check. The report flow accepts up to the configured photo limit (default three), 8 MB per image. The display copy long edge defaults to 1600 pixels and remains configurable. The platform is not an emergency service. New citizen accounts store a unique Indian mobile number and name for sign-in and association of reports with the citizen; the number is not SMS-verified. No citizen email or government ID is collected. Existing staff email identifiers remain available only until an administrator assigns those accounts a phone number. AI, when delivered, may suggest a category to a human reviewer only.

## v1 exclusions

The owner authorized roadmap scope on 2026-11-23, lifting the v1 exclusions for in-app/email notifications, public transparency views, SLA monitoring/escalation, multilingual UI, and a versioned JSON API. These are gated roadmap work, not claims of delivery; each retains its roadmap decision and acceptance requirements. Public data defaults to category, ward, status and counts only, with no photos, text, names, person-linked IDs or exact pins unless the owner approves otherwise.

Mobile app/PWA, SMS/WhatsApp/phone integrations, push notifications, autonomous AI decisions, municipal system integration, multi-city tenant screens, payment, social login, and other work outside the recommended submission cut remain excluded from this delivery. See [`ROADMAP_V2.md`](ROADMAP_V2.md) for sequencing and later-phase boundaries.

## Delivery state

The local Django/PostGIS workflow and automated suite are implemented. External release gates and undelivered AI inputs are itemized in [`LIMITS.md`](LIMITS.md) and [`PARKING_LOT.md`](PARKING_LOT.md). Local test results are recorded in [`TEST_REPORT.md`](TEST_REPORT.md); local passing checks do not claim public deployment or pilot acceptance.



