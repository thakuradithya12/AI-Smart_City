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
| D4 | Production SMTP host and owner-controlled delivery credentials | 3.1 production delivery | Use the configured SMTP backend from environment variables; do not invent credentials. |
| D5 | Rights-cleared AI data source and evidence; owner images or an explicitly approved model/data source | 4.x | Owner images in `ml/data/<category>/`, subject to the existing preflight and sufficient grouped examples. |
| D7 | Exact public fields and location coarsening/suppression policy | 5.2 | Counts and statuses only; no photos, text, names, person-linked identifiers or exact pins. |
| D9 | Native Telugu and Hindi translation reviewers | 7 | English only until reviewers are available. |
| D10 | Submission deadline date and cut line | Scheduling | Owner supplies the actual date; do not infer it from the roadmap's “deadline is close” wording. |
| Evidence derivative setting | Confirm the proposed 1600-pixel display-image long edge before production | 1.8 / production | Configured as `EVIDENCE_DISPLAY_MAX_EDGE=1600`; original bytes remain private and unchanged. |
| API auth | Authentication choice for `/api/v1/` | 6.1 | Do not build the API before owner choice; session or token auth as selected by owner. |

## Operational default selected during roadmap execution

- Task 1.2 unanswered information request timeout: 14 days, configurable with `INFO_REQUEST_TIMEOUT_DAYS`. This is an implementation default, not a retention policy or owner-approved SLA.

## Git remote and CI (Phase 0.4)

As of 2026-11-23, `origin` points to the owner-controlled GitHub repository `https://github.com/thakuradithya12/AI-Smart_City`; commit `6b97f7b5bd154654566946e1481e59d047d3a7a5` was pushed to `origin/phase1`. A remote CI run for that SHA has not been verified; record the Actions result when available.

The workflow's `actions/checkout@v6` tag and the existing `actions/setup-python@v5` tag were checked against the official repositories' release pages on 2026-11-23. Sources: [checkout v6.0.0](https://github.com/actions/checkout/releases/tag/v6.0.0), [setup-python v5.6.0](https://github.com/actions/setup-python/releases/tag/v5.6.0).



`Category.default_department` is retained as a triage-form suggestion only; it does not replace the active ward/category routing rule. The reviewer must submit the route, and a selected department different from that active rule requires a reason. The earlier fallback that routed with `rule_version=0` was reverted because 0 is not a real rule version and cannot appear in the audit trail.
