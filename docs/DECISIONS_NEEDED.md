# Decisions and inputs still needed from the owner

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
| API auth | Authentication choice for `/api/v1/` | 6.1 | Do not build the API before owner choice; session or token auth as selected by owner. |
| V10 | May a `department_official` mark work done (`in_progress` → `resolved_pending_verification`), or is that action reserved for `field_worker`? | 0.5 V10 alignment | **Recommended:** field worker only. The role matrix assigns evidence and the work claim to field workers, while department officials acknowledge/assign; aligning the transition table to the existing view preserves that division. |

## Git remote and CI (Phase 0.4)

No Git remote is configured (`git remote -v` returned no rows). To run remote CI, the owner needs to create or identify the owner-controlled GitHub repository, provide its clone URL, and configure authenticated Git access in this workspace (or configure the remote and push personally). Then push the reviewed commit and provide/record the Actions run URL and SHA. No remote URL, credential or CI result has been invented.

The workflow's `actions/checkout@v6` tag and the existing `actions/setup-python@v5` tag were checked against the official repositories' release pages on 2026-11-23. Sources: [checkout v6.0.0](https://github.com/actions/checkout/releases/tag/v6.0.0), [setup-python v5.6.0](https://github.com/actions/setup-python/releases/tag/v5.6.0).



