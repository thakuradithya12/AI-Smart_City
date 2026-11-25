"""Keep the URL surface explicitly classified by its access policy."""

import inspect

from django.urls import URLPattern, URLResolver, get_resolver


# Anonymous access is limited to these named pages and Django's password-reset flow.
PUBLIC_ROUTE_ALLOWLIST = {
    "healthz",
    "login",
    "home",
    "register",
    "privacy_notice",
    "logout",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
    "admin:login",
}

# Every non-admin private route states the role or object-scope guard its view uses.
# Keeping this inventory explicit makes a newly added route fail until reviewed here.
PRIVATE_ROUTE_GUARDS = {
    "dashboard": "Complaint.objects.visible_to",
    "report": "User.Role.CITIZEN",
    "my_complaints": "User.Role.CITIZEN",
    "complaint_detail": "Complaint.objects.visible_to",
    "evidence_file": "Complaint.objects.visible_to",
    "triage_queue": "_triage_user",
    "route_complaint": "_triage_user",
    "link_duplicate": "can_link_duplicate",
    "reject_complaint": "_triage_user",
    "department_inbox": "_department_user",
    "acknowledge_complaint": "_department_user",
    "transfer_to_triage": "_department_user",
    "assign_complaint": "_department_user",
    "field_tasks": "User.Role.FIELD_WORKER",
    "field_task_detail": "User.Role.FIELD_WORKER",
    "start_work": "User.Role.FIELD_WORKER",
    "upload_field_evidence": "User.Role.FIELD_WORKER",
    "mark_work_done": "User.Role.FIELD_WORKER",
    "audit_workspace": "can_view_audit",
    "audit_export_csv": "can_view_audit",
    "verify_resolution": "can_transition",
    "dispute_resolution": "can_transition",
    "citizen_cancel": "can_transition",
    "admin_cancel_complaint": "User.Role.ADMIN",
    "request_information": "_triage_user",
    "citizen_reply": "User.Role.CITIZEN",
    "supervisor_reassign": "User.Role.SUPERVISOR",
    "privacy_export": "request.user",
    "privacy_delete_request": "User.Role.CITIZEN",
    "notifications_inbox": "Notification.objects.for_user",
    "notification_mark_read": "Notification.objects.for_user",
    "password_change": None,  # Django's built-in view requires an authenticated account.
    "password_change_done": None,
}


def _walk_urlpatterns(patterns, namespace=""):
    for pattern in patterns:
        nested_namespace = namespace
        if isinstance(pattern, URLResolver):
            if pattern.namespace:
                nested_namespace = ":".join(filter(None, (namespace, pattern.namespace)))
            yield from _walk_urlpatterns(pattern.url_patterns, nested_namespace)
        elif isinstance(pattern, URLPattern):
            route_name = ":".join(filter(None, (namespace, pattern.name)))
            yield route_name, pattern.callback


def test_every_url_has_an_explicit_public_or_role_checked_policy():
    routes = list(_walk_urlpatterns(get_resolver().url_patterns))
    route_names = {name for name, _ in routes}
    private_app_routes = set(PRIVATE_ROUTE_GUARDS)
    private_admin_routes = {
        name for name in route_names if name.startswith("admin:") and name not in PUBLIC_ROUTE_ALLOWLIST
    }
    classified_routes = PUBLIC_ROUTE_ALLOWLIST | private_app_routes | private_admin_routes

    assert route_names == classified_routes, (
        f"Classify added or removed routes explicitly. Unclassified: {sorted(route_names - classified_routes)}; "
        f"stale inventory entries: {sorted(classified_routes - route_names)}"
    )

    for name, callback in routes:
        if name in PUBLIC_ROUTE_ALLOWLIST:
            continue
        if name.startswith("admin:"):
            # Django's AdminSite wraps private views with its staff/superuser permission gate.
            assert getattr(callback, "__wrapped__", None) is not None, name
            continue

        # login_required adds this metadata to the wrapped callback.
        assert hasattr(callback, "login_url"), f"{name} must require login"
        expected_guard = PRIVATE_ROUTE_GUARDS[name]
        if expected_guard is not None:
            view_source = inspect.getsource(inspect.unwrap(callback))
            assert expected_guard in view_source, f"{name} is missing its declared role/scope guard"
