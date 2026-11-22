# Test report

## 2026-11-22 — Citizen-to-department routing visibility

| Check | Result | Evidence |
| --- | --- | --- |
| Live complaint state | Confirmed | `ASC-2026-000001` is `in_triage`, has no department yet, belongs to Demo Ward, and has an active pothole rule targeting Demo Department — Roads. The department dashboard's zero is correct until a triage reviewer routes it. |
| Cross-role routing visibility | Passed | Regression test verifies a department official cannot see an untriaged report, then sees it on both dashboard and inbox immediately after the triage reviewer routes it. |
| Full Docker checks | Passed | `No changes detected`; `61 passed in 75.34s`; Ruff passed; Bandit reported no issues; pip-audit found no known vulnerabilities. |
| Dashboard guidance | Updated | Empty states now explain triage routing, assignment and role-specific visibility. |

## 2026-11-22 — Landing, auth, map and interaction regression

| Check | Result | Evidence |
| --- | --- | --- |
| Full Compose gate | Passed | Migration check `No changes detected`; `61 passed in 100.44s`; Ruff passed; Bandit 0 findings across 1,457 scanned lines; `pip-audit` found no known vulnerabilities. |
| Production static manifest build | Passed | `docker compose up -d --build web`; `collectstatic` copied 152 files and post-processed 446. |
| Login/navigation browser walkthrough | Passed | Landing sign-in reaches login when signed out; sign-in after authentication goes to `/workspace/`; valid local test login reaches the workspace; Sign out returns to the login page. |
| Report map browser walkthrough | Passed locally | Leaflet controls and basemap render; clicking the map changes the coordinate fields. No report was submitted. Geolocation permission was not requested. |
| OpenStreetMap response policy | Passed locally | The prior browser showed 403 blocked tiles. Switched to the canonical tile host and verified the running response header is `strict-origin-when-cross-origin`; map tiles then rendered. This is local browser evidence, not production traffic acceptance. |
| Scope | Partial manual interaction coverage | Landing/auth/citizen navigation and report-map interactions were exercised in-browser. Role-specific complaint actions remain covered by the automated lifecycle tests rather than manual clicks in this walkthrough. |

## 2026-11-21 — Phase 6 local acceptance

**Verified code commit:** `e806d63799ebb374d644b1746465d2ae858769b7` (the uploaded ZIP was untracked and excluded; tracked source was clean).

| Check | Result | Evidence |
| --- | --- | --- |
| Full Compose gate | Passed after commit | `No changes detected`; post-commit rerun on the verified code SHA: `58 passed in 57.76s`; Ruff passed; Bandit: 0 findings across 1,453 lines; pip-audit: no known vulnerabilities. |
| Django production check | Passed with known warnings | Exit 0 using the actual protected Compose key; only `security.W005` and `security.W021` remain for the short HSTS configuration without owner-confirmed domain/subdomain policy. |
| Local route smoke | Passed | `/`, `/ui-showcase/`, `/ui-showcase/citizen_dashboard_mobile/`, `/accounts/login/` returned 200; `/workspace/` redirected to login and then returned 200. |
| Browser/accessibility acceptance | Partial | Local browser showed the landing page, 47-screen showcase index and citizen dashboard mockup. Four new tests cover labelled report/triage controls, error announcements/field links and focus-indicator contrast ≥3:1. Viewport was narrow; no full desktop keyboard, screen-reader or real-device result is claimed. |
| Workflow rehearsal | Automated paths passed | Existing tests cover the four-role lifecycle, separate work claim/verification, dispute/reopen/reassign, cancellation, permissions and transition matrix. No live fresh-account rehearsal was performed. |
| Local code commit | Passed | `e806d63799ebb374d644b1746465d2ae858769b7`; full Compose gate rerun after commit. The uploaded UI ZIP was excluded and remains untracked. |
| Remote CI and push | Not verified | No Git remote is configured, so no remote Actions result or push is claimed. |

The fresh-account rehearsal twice, two-phone and full desktop keyboard/screen-reader checks, public deployment, and production restore/monitoring remain open. See [`PHASE6_ACCEPTANCE.md`](PHASE6_ACCEPTANCE.md) and [`LIMITS.md`](LIMITS.md).

## 2026-11-21 — Phase 5 local operations and security gate

| Check | Result | Evidence |
| --- | --- | --- |
| Integrated Compose suite | Passed | `No changes detected`; final rerun: `54 passed in 64.78s`; Ruff passed; Bandit found no issues across 1,453 lines; pip-audit found no known vulnerabilities. |
| Production settings | Passed with warnings | `check --deploy` using the actual Compose key exited 0. Only `security.W005` and `security.W021` remain for the deliberately short HSTS policy. |
| Production Compose parsing | Passed | Production Compose validation passed with temporary process-only image/domain placeholders. No production deployment was attempted. |
| Caddy config | Passed | `caddy fmt` and `caddy validate` succeeded using `DOMAIN=localhost`; upstream `Server` response header is removed. |
| Browser policy and caching headers | Passed | Main routes returned `Permissions-Policy`, same-origin CORP, and HTML `Cache-Control: no-store`. |
| ZAP passive baseline | Passed with reviewed warnings | Final local HTTP scan, rerun after the Phase 6 accessibility changes: 128 URLs, 0 FAIL, 5 WARN categories, 57 PASS. Reports: [`JSON`](zap-baseline-2026-11-21-final.json) and [`HTML`](zap-baseline-2026-11-21-final.html). This is passive, not an active penetration test or production scan. |
| Caddy proxy behavior | Passed locally | Disposable internal Caddy HTTPS request returned 200, stripped upstream `Server`, and retained `Cache-Control: no-store`. The upstream was the local development server, not production Gunicorn. |
| Secret file ACL and key | Passed locally | `.env` is ignored/untracked with inheritance disabled; only the current user, SYSTEM, and Administrators have Full Control. The weak local key was rotated to a random 64-byte key, never displayed. |
| Git whitespace check | Passed | `git diff --check` returned no whitespace errors. |

The five remaining ZAP warning categories are third-party JavaScript without SRI, cross-domain JavaScript inclusion, inline design-page comments, the development runserver banner, and missing CSP on showcase/error responses. The runserver banner occurs in the local test target; the Caddy proxy check proved that the configured reverse proxy removes the upstream `Server` header. CSP/SRI require bundling and auditing the supplied UI's inline and third-party resources; a permissive policy or guessed integrity hashes would be unsound. The cache-control warning was resolved by setting `no-store` on HTML, and the final scan no longer reports cacheable content or COEP. No finding was confirmed exploitable by this passive scan. `tests/test_day2_reporting.py` covers report throttling; django-axes provides login lockout. Public HTTPS and production-edge enforcement remain unverified.

## 2026-11-21 — Local Docker verification

**Code under test:** current worktree after commit `97433e4`, including the public CivicOps landing/gallery route and local fixes to its tests/template. This is not a GitHub Actions result and no final release commit is claimed.

| Check | Result | Evidence |
| --- | --- | --- |
| Docker build/start | Passed | `docker compose up -d --build db web`; PostGIS healthy and web started. |
| Migration consistency | Passed | Checks container: `No changes detected`. |
| pytest | Passed | `38 passed in 64.17s`. |
| Ruff | Passed | `All checks passed!`. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Django production deploy check | Passed with documented warnings | Exit 0; warnings `security.W005` (HSTS subdomains) and `security.W021` (HSTS preload) remain intentionally unset pending a confirmed stable domain. |
| HTTP smoke | Passed | `/`, `/ui-showcase/`, `/ui-showcase/citizen_dashboard_mobile/`, `/workspace/` (login redirect followed), `/accounts/login/` returned HTTP 200. Login protection for `/workspace/` is also asserted by pytest. |
| Browser visual check | Passed | Local browser rendered the supplied CivicOps landing at `http://localhost:8000/`; title and landing content observed. |

### Initial test findings and fixes

The first suite run produced `2 failed, 35 passed`: the complaint timeline template had dropped the expected `Evidence:` label, and the old login test expected the home route to be private after the product was changed to expose the supplied public landing page. Restored the evidence label and updated login tests to assert the intended public landing and authenticated `/workspace/`. The rerun passed with 38 tests.

### Limits

- No GitHub Actions run was checked or inferred.
- The `check --deploy` HSTS warnings are recorded above; public deployment remains unconfigured.
- This report covers local Docker tests on the worktree state identified above, not the final completion of every backend roadmap phase.

## 2026-11-21 — Backend Phase 1: workflow integrity

**Code under test:** Phase 1 worktree after `7a4038e`, including workflow-service routing transaction and ORM append-only guards. The Phase 0 public landing/login tests remain included.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | `docker compose run --rm checks`: `No changes detected`. |
| pytest | Passed | `39 passed in 61.03s`. Includes route-audit failure rollback and instance/queryset append-only tests. |
| Ruff | Passed | `All checks passed!`. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Django production deploy check | Passed with same documented warnings | Exit 0 on rebuilt container; only HSTS subdomain/preload warnings remain. |
| Fresh web image | Passed | `docker compose up -d --build db web`; PostGIS healthy and web started. |

### Phase 1 changes

- Ward/category routing rule selection, override validation, transition and routing audit now execute inside a single transaction in `apps/workflow/services.py`. Injected routing-audit failure rolls the status and event writes back.
- `StatusEvent` and `AuditEvent` now reject instance save/delete updates and queryset update/delete operations. Tests cover all four bypass paths.
- No schema changes were needed. Existing complaint creation transaction and state-machine-only status assignment were rechecked by the passing suite/code scan.

Phase 1 gate passed locally. GitHub CI was not checked; no production deployment or pilot ward data is claimed.

### Independent rerun on committed Phase 1

Reran the gate on **2026-11-21** with `HEAD=fac743d` after rebuilding the image from that commit. Results: migration check `No changes detected`; `39 passed in 92.20s`; Ruff `All checks passed!`; pip-audit `No known vulnerabilities found`. `check --deploy` exited successfully with only the same two intentional HSTS warnings. Requests to `/`, `/ui-showcase/` and `/workspace/` returned HTTP 200 (workspace response includes the login redirect, covered by its test). Docker Desktop Linux engine access was granted for these commands. This independently confirms the Phase 1 report above.

## 2026-11-21 — Phase 2 security and Phase 3 generic geography checks

**Code under test:** worktree changes following `fac743d`; this report is local Docker evidence, not CI or a release verification.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | Latest Compose checks: `No changes detected`. |
| pytest | Passed | Latest Compose checks: `45 passed in 77.18s`. Added inactive-user visibility, stale field upload state, atomic evidence/audit rollback cleanup, and effective ward dates. |
| Ruff | Passed | Latest Compose checks: `All checks passed!`. |
| Bandit | Passed | Latest Compose checks: no issues in 1,431 scanned lines. |
| pip-audit | Passed on Phase 2 run | The preceding Phase 2 check reported no known vulnerabilities; dependency pins were unchanged for the subsequent effective-date tests. |
| Production `check --deploy` and rebuilt web smoke | Not rerun for this worktree | Prior Phase 1 result is historical. The attempted fresh build was blocked when the environment approval service hit its usage limit; no bypass attempted. |

### Scope and limits

- Field evidence writes now lock and validate the current complaint state in the same transaction as evidence and audit writes. Failure rolls database changes back and removes newly stored private files. Regression tests cover stale model state and audit failure cleanup.
- Complaint visibility denies inactive accounts. Active ward lookup requires the pin date to fall within the ward's effective dates; tests cover future and expired boundaries.
- The Phase 3 code path is implemented generically, but real jurisdiction is not configured: pilot centre coordinates and authoritative ward boundary/source data remain owner inputs. Do not treat generic tests as proof of a real pilot ward.
- GitHub CI, public deployment, backup/restore, and full acceptance remain unverified.

## 2026-11-21 — Phase 4 secure data-intake preparation

No model or inference feature was built. The user selected `ml/data/<category>/` for the five owner photo folders. Created the local intake structure and a read-only preflight requiring image/group manifest consistency; `other` is counted for evaluation only and is not a model output. Added tests for valid grouped samples, missing manifest, traversal, corrupt images, and duplicate-image split leakage.

| Check | Result | Evidence |
| --- | --- | --- |
| Integrated Compose suite | Passed | `No changes detected`; `54 passed in 57.91s`; Ruff passed; Bandit no findings; pip-audit no known vulnerabilities. |
| Dataset preflight against selected path | Correctly blocked | Exit 1; all five folders contained 0 images and `manifest.csv` was missing. It explicitly reported that no training/evaluation was run. |
| Docker build context | Passed | Rebuilt image context was 97.49 kB. Bare-image inspection confirmed `.env`, `.git`, `ml/data`, `/app/private_media`, `/app/backups`, and the uploaded ZIP are absent. |

The actual photo dataset is not in the workspace. No model, split, evaluation metrics, ONNX output, or worker is claimed. Phase 4 model work remains gated on the files, group manifest, and earlier core prerequisites.

The owner-selected path was checked directly: the five category folders were empty and `manifest.csv` was absent, so `python ml/dataset_preflight.py` exited 1 as designed and reported that training/evaluation had not run. The bare rebuilt app image does not contain `.env`, `.git`, `ml/data`, `private_media`, `backups`, or the uploaded UI ZIP. The Compose image build context was 97.49 kB after exclusions.

### Independent integrated rerun

On **2026-11-21**, reran Compose checks for Phase 4 intake plus Phases 0–3: `No changes detected`; `54 passed in 60.80s`; Ruff passed; Bandit found no issues across 1,453 lines; pip-audit found no known vulnerabilities. The real-data preflight again exited 1 as designed: zero images in the five folders and no manifest. `migrate --check` and production `check --deploy` exited 0; only the documented HSTS warnings remain. Container-local landing, showcase, login and workspace requests all returned HTTP 200. This verifies the existing backend and intake preflight, not classifier quality or model behavior.

## 2026-11-21 — Phase 5 local backup and restore rehearsal

| Check | Result | Evidence |
| --- | --- | --- |
| Bash script syntax | Passed | `bash -n` succeeded for `backup.sh`, `restore_test.sh`, and `deploy.sh` in the project image. |
| Database backup and restore | Passed | A local custom-format dump restored into a disposable PostGIS container; sanity query found 35 migration records, 6 users, and 0 complaints. |
| Private-media backup and restore | Passed | Archive extracted into an isolated temporary volume; 6 files restored. |
| Temporary resource cleanup | Passed | Disposable containers/volume and restricted temporary backup directory were removed after verification. |
| Saved evidence | Passed | [`restore-test-2026-11-21.log`](restore-test-2026-11-21.log) contains counts and SHA-256 checksums only. |

### Finding

The local development private-media volume has six files with zero matching `Evidence` rows (six unreferenced files). They were not deleted because their ownership and retention are uncertain. The restored media archive preserves them. Production backups and off-host retention have not been tested.

### Integrated Phase 2 regression rerun

Reran the complete check service on **2026-11-21** against the Phase 2 worktree together with Phases 0 and 1: migration check `No changes detected`; `45 passed in 49.17s`; Ruff passed; Bandit reported no findings across 1,431 lines; pip-audit reported `No known vulnerabilities found`. Rebuilt and restarted `web` from the same worktree. Production `check --deploy` exited 0 with only the two documented HSTS warnings (`security.W005`, `security.W021`). Container-local HTTP requests to `/`, `/ui-showcase/`, `/accounts/login/` and `/workspace/` all returned HTTP 200; the workspace request followed its login redirect. This confirms the local integrated regression gate, not GitHub CI or production deployment.

## 2026-11-21 — Phase 3 geography and routing

**Code under test:** current worktree after adding effective-date validation, rule-precedence tests, and the ward date-window migration. This is local Docker evidence; GitHub CI and a live pilot area are not covered.

| Check | Result | Evidence |
| --- | --- | --- |
| Migration consistency | Passed | Compose checks: `No changes detected`. |
| pytest | Passed | `49 passed in 69.33s`, including all Phase 0–2 coverage plus ward date-window validation, future/expired ward rejection, routing precedence, future rule exclusion, rule-version audit, and safety-critical triage warning. |
| Ruff | Passed | `All checks passed!`. |
| Bandit | Passed | No findings in 1,453 scanned lines. |
| pip-audit | Passed | `No known vulnerabilities found`. |
| Database migration | Passed | Rebuilt web container and applied `geography.0002_ward_ward_effective_window_valid` successfully. |
| Production check | Passed with known warnings | Exit 0; only `security.W005`/`security.W021` remain for HSTS subdomains/preload. |
| HTTP smoke | Passed | Container-local `/`, `/ui-showcase/`, `/accounts/login/`, and `/workspace/` returned HTTP 200; workspace followed its login redirect. |

The first run produced one failed **test expectation** because its shared fixture still contained a valid older ward rule. The service correctly chose that ward-specific rule. The fixture was corrected to make every ward-specific rule future-dated; the rerun passed all 49 tests. No routing service defect was found.

### Independent integrated rerun

On **2026-11-21**, reran the Compose checks on the resulting Phase 3 worktree: `No changes detected`; `49 passed in 62.49s`; Ruff passed; Bandit found no issues in 1,453 lines; pip-audit found no known vulnerabilities. `migrate --check` exited 0. Repeated `check --deploy` exited 0 with only the two documented HSTS warnings, and the four container-local HTTP smoke requests each returned 200. This rerun includes the prior workflow, authorization, evidence, and UI-route regression coverage.

### Phase 3 limits

- Centre coordinates and authoritative ward boundary/source data remain unavailable. Test polygons are synthetic fixtures only; no real pilot ward, routing data, or location-specific availability is claimed.
- GitHub CI, public deployment, backup/restore, and full acceptance remain unverified.
