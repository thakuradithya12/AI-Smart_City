# Decisions and inputs still needed from the owner

## Phone login provenance

- `git log -S` results: `61c37fa` introduced both `PhoneOrLegacyEmailBackend` and `PhoneAuthenticationForm`; phone-related history also includes `9066970` and `e806d63`.
- The introducing commit adds `User.phone_number` as nullable and unique through migration `0002`; phone number is stored on each citizen account.
- Citizen registration collects phone number (not email); the report form does not collect it, while report consent says the account phone number is stored with report data.
- Templates/docs mention phone-based registration and login; tests include `test_user_can_authenticate_with_normalized_phone_number`, but legacy email case login and Axes case-normalization coverage are not confirmed.
- `docs/SPEC.md` and `docs/PRIVACY.md` must describe what phone data is stored; SPEC now does, and PRIVACY should state account phone is retained for sign-in and complaint contact association, with no SMS verification.

These questions block only the roadmap tasks that depend on them. Defaults are proposals from `docs/ROADMAP_V2.md`, not decisions made on the owner's behalf.

| ID | Needed input | Blocks | Recommended default |
| --- | --- | --- | --- |
| D1 | Owner-controlled deployment target (domain and VPS/PaaS) and access method | 8.1 | Single VPS with Docker Compose and Caddy, only after the owner supplies the host and credentials. |
| D2 | Pilot centre coordinates and authoritative ward polygon source/effective dates | 1.12, 8.1 | Owner names an open municipal GeoJSON source; keep the local synthetic demo ward clearly labelled. |
| D3 | Retention periods for complaints, photos and accounts, and deletion process | 1.9 | Propose periods in `docs/PRIVACY.md`; obtain owner approval before production. |
| D4 | Email/SMTP provider and owner-controlled delivery credentials | 3.1 | Console backend in development; SMTP from environment in production. |
| D5 | Rights-cleared AI data source and evidence; owner images or an explicitly approved model/data source | 4.x | Owner images in `ml/data/<category>/`, subject to the existing preflight and sufficient grouped examples. |
| D6 | Map tile provider for intended traffic | 2.3, 8.1 | OSM with attribution for demo traffic only; decide again before real traffic. |
| D7 | Exact public fields and location coarsening/suppression policy | 5.2 | Counts and statuses only; no photos, text, names, person-linked identifiers or exact pins. |
| D8 | SLA values by category and escalation levels | 3.2, 3.4 | Keep `default_due_hours`; no escalation until values are supplied. |
| D9 | Native Telugu and Hindi translation reviewers | 7 | English only until reviewers are available. |
| D10 | Submission deadline date and cut line | Scheduling | Owner supplies the actual date; do not infer it from the roadmap's “deadline is close” wording. |
| Evidence derivative setting | Confirm the proposed 1600-pixel display-image long edge before production | 1.8 / production | Configured as `EVIDENCE_DISPLAY_MAX_EDGE=1600`; original bytes remain private and unchanged. |
| D14 | Approve maximum session age/idle timeout | 1.14 | Pending owner input. SameSite is explicitly `Lax`; session age remains Django's current default until an idle timeout is approved. |

### D3 status — task 1.9

The owner has not supplied retention periods or an approved deletion process. Task 1.9 includes deletion/anonymisation and a purge command, so its implementation is paused rather than inventing retention values. `docs/PRIVACY.md` currently states that retention is unset and production data collection is not authorized until approval.

### D2 status — task 1.12

The owner has not supplied a pilot centre or authoritative boundary source/effective dates. Generic GeoJSON loading and synthetic-geometry validation are implemented, but no real pilot ward or inside/outside pilot point test is included. A database exclusion constraint is also not added because the PostGIS extension availability could not be checked without the database container; Python model validation and the import command check polygon interiors.
| API auth | Authentication choice for `/api/v1/` | 6.1 | Do not build the API before owner choice; session or token auth as selected by owner. |
| V10 | May a `department_official` mark work done (`in_progress` → `resolved_pending_verification`), or is that action reserved for `field_worker`? | 0.5 V10 alignment | **Recommended:** field worker only. The role matrix assigns evidence and the work claim to field workers, while department officials acknowledge/assign; aligning the transition table to the existing view preserves that division. |
| 1.3 / V10 | Confirm whether `department_official` may mark work done | 1.3 | **Pending owner decision.** Current behavior and transition matrix keep this action field-worker-only; no role expansion made. |

## Operational default selected during roadmap execution

- Task 1.2 unanswered information request timeout: 14 days, configurable with `INFO_REQUEST_TIMEOUT_DAYS`. This is an implementation default, not a retention policy or owner-approved SLA.

## Git remote and CI (Phase 0.4)

No Git remote is configured (`git remote -v` returned no rows). To run remote CI, the owner needs to create or identify the owner-controlled GitHub repository, provide its clone URL, and configure authenticated Git access in this workspace (or configure the remote and push personally). Then push the reviewed commit and provide/record the Actions run URL and SHA. No remote URL, credential or CI result has been invented.

The workflow's `actions/checkout@v6` tag and the existing `actions/setup-python@v5` tag were checked against the official repositories' release pages on 2026-11-23. Sources: [checkout v6.0.0](https://github.com/actions/checkout/releases/tag/v6.0.0), [setup-python v5.6.0](https://github.com/actions/setup-python/releases/tag/v5.6.0).



`Category.default_department` is retained as a triage-form suggestion only; it does not replace the active ward/category routing rule. The reviewer must submit the route, and a selected department different from that active rule requires a reason. The earlier fallback that routed with `rule_version=0` was reverted because 0 is not a real rule version and cannot appear in the audit trail.
