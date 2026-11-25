from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from apps.complaints.views import complaint_detail, evidence_file, my_complaints, register, report
from apps.accounts.models import User
from apps.complaints.models import Complaint, StatusEvent
from . import views as workflow_views

def home(request):
    if request.user.is_authenticated:
        return dashboard(request)
    status_labels = dict(Complaint.Status.choices)
    activity = StatusEvent.objects.select_related("complaint__category", "complaint__ward").order_by("-created_at")[:3]
    updates = [
        {
            "category": event.complaint.category.display_label,
            "ward": event.complaint.ward.name if event.complaint.ward_id else "Service area",
            "status": status_labels.get(event.to_status, event.to_status.replace("_", " ").title()),
            "created_at": event.created_at,
        }
        for event in activity
    ]
    return render(request, "landing.html", {"updates": updates})

@login_required
def dashboard(request):
    visible = Complaint.objects.visible_to(request.user).select_related("category", "ward", "department")
    active = visible.exclude(status__in=[Complaint.Status.VERIFIED_CLOSED, Complaint.Status.REJECTED, Complaint.Status.CANCELLED])
    context = {
        "total_count": visible.count(),
        "active_count": active.count(),
        "closed_count": visible.filter(status=Complaint.Status.VERIFIED_CLOSED).count(),
        "attention_count": visible.filter(status__in=[Complaint.Status.IN_TRIAGE, Complaint.Status.ROUTED, Complaint.Status.RESOLVED_PENDING_VERIFICATION]).count(),
        "recent_complaints": visible.order_by("-created_at")[:5],
    }
    if request.user.role in {User.Role.TRIAGE_REVIEWER, User.Role.ADMIN}:
        context["queue_url_name"] = "triage_queue"
    elif request.user.role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR}:
        context["queue_url_name"] = "department_inbox"
    elif request.user.role == User.Role.FIELD_WORKER:
        context["queue_url_name"] = "field_tasks"

    role = request.user.role
    context["dashboard_title"] = "Overview"
    context["dashboard_intro"] = "Review civic reports and follow the work happening across your service area."
    context["dashboard_metrics"] = [
        {"label": "All complaints", "value": context["total_count"], "help": "Visible to your account"},
        {"label": "Active", "value": context["active_count"], "help": "Still moving through the workflow"},
        {"label": "Verified closed", "value": context["closed_count"], "help": "Fixes independently confirmed"},
        {"label": "Needs attention", "value": context["attention_count"], "help": "Triage, routing or verification"},
    ]
    if role == User.Role.CITIZEN:
        context.update(
            dashboard_title="Your reports",
            dashboard_intro="Track reports you submitted and review fixes when they are ready.",
            dashboard_metrics=[
                {"label": "My reports", "value": context["total_count"], "help": "Reports linked to your account"},
                {"label": "In progress", "value": context["active_count"], "help": "Open reports"},
                {"label": "Review the fix", "value": visible.filter(status=Complaint.Status.RESOLVED_PENDING_VERIFICATION).count(), "help": "Confirm or dispute the work"},
                {"label": "Verified", "value": context["closed_count"], "help": "Fixes confirmed by a person"},
            ],
        )
        context["dashboard_actions"] = [
            ("Report an issue", "report"), ("My complaints", "my_complaints"),
            ("Notifications", "notifications_inbox"), ("Privacy and data", "privacy_notice"),
        ]
    elif role == User.Role.FIELD_WORKER:
        assigned = visible.filter(status__in=[Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS])
        context.update(
            dashboard_title="My field work",
            dashboard_intro="Open your assigned tasks to check the location, record evidence and report completion.",
            dashboard_metrics=[
                {"label": "Assigned tasks", "value": assigned.count(), "help": "Work assigned to you"},
                {"label": "In progress", "value": assigned.filter(status=Complaint.Status.IN_PROGRESS).count(), "help": "Work you have started"},
                {"label": "Overdue", "value": assigned.filter(due_at__lt=timezone.now()).count(), "help": "Tasks past their due date"},
                {"label": "Completed and verified", "value": visible.filter(status=Complaint.Status.VERIFIED_CLOSED).count(), "help": "Work confirmed after your claim"},
            ],
            dashboard_actions=[("My assigned tasks", "field_tasks"), ("Notifications", "notifications_inbox")],
        )
    elif role == User.Role.DEPARTMENT_OFFICIAL:
        context.update(
            dashboard_title="Department overview",
            dashboard_intro="Acknowledge routed reports and assign work to an active field worker in your department.",
            dashboard_metrics=[
                {"label": "Routed to us", "value": visible.filter(status=Complaint.Status.ROUTED).count(), "help": "Waiting for acknowledgement"},
                {"label": "Ready to assign", "value": visible.filter(status=Complaint.Status.ACKNOWLEDGED).count(), "help": "Acknowledged and awaiting a worker"},
                {"label": "Active field work", "value": visible.filter(status__in=[Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS]).count(), "help": "Assigned or underway"},
                {"label": "Awaiting verification", "value": visible.filter(status=Complaint.Status.RESOLVED_PENDING_VERIFICATION).count(), "help": "A supervisor or citizen reviews the claim"},
            ],
            dashboard_actions=[("Department inbox", "department_inbox"), ("Notifications", "notifications_inbox")],
        )
    elif role == User.Role.SUPERVISOR:
        team_count = User.objects.filter(
            department_id=request.user.department_id, role=User.Role.FIELD_WORKER, is_active=True
        ).count() if request.user.department_id else 0
        context.update(
            dashboard_title="Supervisor overview",
            dashboard_intro="Review work in your department, monitor due dates and verify completion claims.",
            dashboard_metrics=[
                {"label": "Awaiting verification", "value": visible.filter(status=Complaint.Status.RESOLVED_PENDING_VERIFICATION).count(), "help": "Review or dispute a completion claim"},
                {"label": "Overdue", "value": active.filter(due_at__lt=timezone.now()).count(), "help": "Open reports past their due date"},
                {"label": "Active field work", "value": visible.filter(status__in=[Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS]).count(), "help": "Assigned or underway"},
                {"label": "Field workers", "value": team_count, "help": "Active workers in your department"},
            ],
            dashboard_actions=[("Department work queue", "department_inbox"), ("Notifications", "notifications_inbox")],
        )
    elif role == User.Role.ADMIN:
        context.update(
            dashboard_title="City operations",
            dashboard_intro="Monitor incoming reports, open the review queue and manage service configuration.",
            dashboard_metrics=[
                {"label": "In triage", "value": visible.filter(status=Complaint.Status.IN_TRIAGE).count(), "help": "Waiting for reviewer action"},
                {"label": "Open complaints", "value": context["active_count"], "help": "Not yet in a final state"},
                {"label": "Overdue", "value": active.filter(due_at__lt=timezone.now()).count(), "help": "Open reports past their due date"},
                {"label": "Verified closed", "value": context["closed_count"], "help": "Fixes independently confirmed"},
            ],
            dashboard_actions=[("Triage queue", "triage_queue"), ("Notifications", "notifications_inbox")],
            admin_configuration_url="/admin/",
        )
    return render(request, "home.html", context)

urlpatterns = [
    path("", home, name="home"),
    path("workspace/", dashboard, name="dashboard"),
    path("register/", register, name="register"),
    path("complaints/new/", report, name="report"),
    path("complaints/", my_complaints, name="my_complaints"),
    path("complaints/<int:pk>/", complaint_detail, name="complaint_detail"),
    path("evidence/<int:pk>/", evidence_file, name="evidence_file"),
    path("console/triage/", workflow_views.triage_queue, name="triage_queue"),
    path("console/triage/<int:pk>/route/", workflow_views.route_complaint, name="route_complaint"),
    path("console/triage/<int:pk>/duplicate/", workflow_views.link_duplicate, name="link_duplicate"),
    path("console/triage/<int:pk>/reject/", workflow_views.reject_complaint, name="reject_complaint"),
    path("console/department/", workflow_views.department_inbox, name="department_inbox"),
    path("console/department/<int:pk>/acknowledge/", workflow_views.acknowledge_complaint, name="acknowledge_complaint"),
    path("console/department/<int:pk>/transfer/", workflow_views.transfer_to_triage, name="transfer_to_triage"),
    path("console/department/<int:pk>/assign/", workflow_views.assign_complaint, name="assign_complaint"),
    path("console/field/", workflow_views.field_tasks, name="field_tasks"),
    path("console/field/<int:pk>/", workflow_views.field_task_detail, name="field_task_detail"),
    path("console/field/<int:pk>/start/", workflow_views.start_work, name="start_work"),
    path("console/field/<int:pk>/evidence/", workflow_views.upload_field_evidence, name="upload_field_evidence"),
    path("console/field/<int:pk>/done/", workflow_views.mark_work_done, name="mark_work_done"),
    path("complaints/<int:pk>/verify/", workflow_views.verify_resolution, name="verify_resolution"),
    path("complaints/<int:pk>/dispute/", workflow_views.dispute_resolution, name="dispute_resolution"),
    path("complaints/<int:pk>/cancel/", workflow_views.citizen_cancel, name="citizen_cancel"),
    path("complaints/<int:pk>/admin-cancel/", workflow_views.admin_cancel_complaint, name="admin_cancel_complaint"),
    path("complaints/<int:pk>/request-information/", workflow_views.request_information, name="request_information"),
    path("complaints/<int:pk>/reply/", workflow_views.citizen_reply, name="citizen_reply"),
    path("complaints/<int:pk>/reassign/", workflow_views.supervisor_reassign, name="supervisor_reassign"),
]
