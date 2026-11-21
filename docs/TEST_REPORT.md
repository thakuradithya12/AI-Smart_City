# Test report

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
