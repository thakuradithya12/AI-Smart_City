from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
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
    path("complaints/<int:pk>/request-information/", workflow_views.request_information, name="request_information"),
    path("complaints/<int:pk>/reply/", workflow_views.citizen_reply, name="citizen_reply"),
    path("complaints/<int:pk>/reassign/", workflow_views.supervisor_reassign, name="supervisor_reassign"),
]
