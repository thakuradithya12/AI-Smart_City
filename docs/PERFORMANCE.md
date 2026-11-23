# List performance evidence

## 2026-11-23 — ROADMAP_V2 task 1.10

Complaint lists now use stable ordering, configurable pagination (`LIST_PAGE_SIZE`, default 20), search by public ID or description, and status/ward/category/overdue filters. Complaint indexes cover status plus due date, department plus status, ward plus status, and creation time.

### EXPLAIN evidence

The required before/after plans on 5,000 seeded rows have **not been measured**. The local Django/PostGIS service is unavailable in this workspace, so no seed set or query plan is claimed. Capture actual plans before relying on these indexes in production:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM complaints_complaint
WHERE status = 'in_triage' AND due_at < CURRENT_TIMESTAMP
ORDER BY due_at, created_at, id LIMIT 20;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM complaints_complaint
WHERE department_id = (SELECT MIN(id) FROM geography_department) AND status = 'acknowledged'
ORDER BY due_at, created_at, id LIMIT 20;
```

| Plan | Rows | Result |
| --- | --- | --- |
| Before indexes | 5,000 seeded rows required | Not measured |
| After indexes | Same database and queries | Not measured |

