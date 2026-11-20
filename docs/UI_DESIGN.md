# UI design integration

The supplied `stitch_civic_operations_platform` archive is extracted in [`ui_reference/`](ui_reference/). Its design-system file defines the CivicOps navy/blue palette, light operational surfaces, compact semantic status labels, responsive layouts, and restrained borders. The original HTML screens are retained as visual references.

## Integrated live routes

The reference system is adapted to the existing Django templates and server-side workflow; the static mockups are not served as application pages.

- Shared shell, role-aware links, keyboard skip link and sign-in: `templates/base.html`, `templates/registration/login.html`
- Citizen overview, report form, complaint list and complaint timeline: `templates/home.html`, `templates/complaints/`
- Reviewer triage, department inbox, and field task list/detail: `templates/console/`
- Shared palette, responsive components, status badges, form controls, empty states and timelines: `static/css/site.css`

The UI uses Django-rendered data and existing named routes. Dashboard counts use `Complaint.objects.visible_to(request.user)`, so they reflect only records that the current role may view. Workflow permissions and state changes remain enforced by the existing server-side services.

## Intentionally reference-only screens

The archive also contains designs outside the frozen v1 website scope or for routes that do not exist in this project, including a public issue map/dashboard, notifications, SLA/escalation centers, analytics reports, and expanded personnel management. Those remain references and are not represented as working functionality.
