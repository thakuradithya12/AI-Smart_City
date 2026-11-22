# Binding clarifications to AGENTS.md

## 2026-11-23 — Roadmap V2 scope amendment

The owner requested that the agent execute `ROADMAP_V2.md` completely. This is the owner's confirmation of roadmap decision D11 and amends the frozen v1 exclusions for the roadmap's gated work: in-app/email notifications; public transparency/map views; multilingual UI; SLA monitoring/escalation; and a versioned JSON API. These are authorized scope, not evidence they are implemented. They remain subject to D4, D7–D9, the API-authentication decision, and the roadmap's acceptance gates. SMS, push, and phone integrations remain excluded. The recommended submission cut in roadmap section 4 still determines which authorized work is attempted before delivery; later items must be labelled roadmap/not delivered.

Public transparency uses the roadmap's safe defaults until the owner decides otherwise: counts, categories, wards and statuses only; no photos, text, names, person-linked identifiers or exact pins. The file is located at repository root (`ROADMAP_V2.md`), although the pasted execution brief refers to `docs/ROADMAP_V2.md`.

These decisions were supplied by the project owner on 2026-11-18. They are binding additions to the repository-root `AGENTS.md`. Do not ask these questions again. Where an input remains a placeholder, preserve it as unresolved; do not invent a value.

## Inputs

1. **Server and domain:** none yet. Build and test locally, mark the Day 1 public-deploy gate blocked, and do not claim it.
2. **Pilot area centre:** latitude and longitude were left as `[FILL]`; unresolved. Do not guess or ask again. Ward boundaries are hand-drawn polygons around this area, with `Ward.source` recorded as `hand-drawn, <date>`. The supported area is those polygons. Until the centre coordinates and polygons are supplied, no pilot ward data or location-specific claims can be created.
3. **Categories:** retain all six section 0 defaults: pothole, garbage, drainage, streetlight, water_leakage, other.
4. **College requirements:** none.

## Binding answers and decisions

- Missing ward data or a pin outside every ward fails closed with a clear message. “Registration never depends on maps” means no dependency on third-party tiles or geocoding: the server accepts coordinates and checks local ward polygons.
- A dispute transitions to `reopened` with a required reason; there is no separate dispute state.
- Keep the Day 5 AI slice and all six product categories. Train only on the 3–4 categories with a clearly licensed dataset; the remaining categories show “no suggestion”. Drop the slice only if no licensed data exists.
- Add `ComplaintMessage(complaint, author, body, created_at)` for information requests and citizen replies; write these events to the audit log.
- `submitted -> in_triage` uses `actor=None`, role `system`, in the same transaction. Roll back the report if that transition fails.
- `routed -> in_triage` means transfer back to triage with a reason; a reviewer manually routes it again. Never automatically re-route.
- Admin overrides may use only transitions in AGENTS.md section 8, require a reason, and are flagged in the audit log.
- Create the complaint row, then set `public_id` from its primary key inside the same atomic block; enforce uniqueness.
- Reviewers see complaint facts and citizen name, but not phone number or email.
- Owner request (2026-11-23): new citizen registration and sign-in use a unique Indian phone number instead of email. SMS/OTP verification remains out of scope. Existing staff email-based accounts remain usable until an administrator assigns phone numbers.
- Vendor Bootstrap and Leaflet locally and record licences. Use OSM tiles only within the published usage policy and at demo-level traffic.
- Worker is an optional Compose profile until Day 5: one process, one retry, then mark failed.
- Duplicate candidates use 30 m, last 7 days; “open” means every status except `verified_closed`, `rejected`, and `cancelled`.
- Choose and document conservative rate limits. Start HSTS short, only after HTTPS works.
- Use skills/plugins only if available in this environment; otherwise perform equivalent checks manually. Install nothing without owner approval.
- Error tracking and uptime monitoring are optional; skip services whose terms are unclear.
- A “step” is one coherent change: run its focused tests and smoke check, plus the full suite at each gate.
- Day 1 order: start with a minimal login skeleton (local Compose, then server), then models, then CI.

## Current Day 1 applicability

- Local-only work is authorized. Public deployment is blocked because no domain/server was supplied.
- Centre coordinates and authoritative pilot ward polygons remain absent. Do not create pilot geography or claim real service coverage. The owner later explicitly requested a local demo area in Telangana; `seed_demo` therefore creates a clearly labeled synthetic central-Hyderabad square for local workflow demonstrations only. It is not an authoritative ward or pilot boundary.
- The six default categories and AI policy above supersede any assumption that the user confirmed another category list.

## Rejection reason clarification

- Agent assumption (owner approved 2026-11-19): reasons are required free text, 5 to 500 characters. For triage rejection (`in_triage -> rejected`), this replaces section 8's reason-code requirement; do not add a fixed code list.
