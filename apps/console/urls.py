from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
from django.http import HttpResponse
from pathlib import Path
from django.conf import settings
from apps.complaints.views import complaint_detail, evidence_file, my_complaints, register, report
from apps.accounts.models import User
from apps.complaints.models import Complaint
from . import views as workflow_views

def home(request):
    return ui_showcase(request, "public_landing_civicops")

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

def ui_showcase(request, screen=""):
    # Serve supplied static mockups directly so every design is viewable without backend data.
    root = Path(settings.BASE_DIR) / "docs" / "ui_reference"
    screens = sorted(path.parent.name for path in root.glob("*/code.html"))
    if screen:
        if screen not in screens:
            from django.http import Http404
            raise Http404
        html = (root / screen / "code.html").read_text(encoding="utf-8")
        # Keep every supplied design reachable from within each standalone mockup.
        nav = '<nav style="position:fixed;z-index:99999;right:12px;top:12px;background:#172b4d;padding:10px 14px;border-radius:8px;font:14px system-ui"><a style="color:white;text-decoration:none" href="/ui-showcase/">← All screens</a></nav>'
        html = html.replace("</body>", nav + "</body>")
        return HttpResponse(html)
    links = "".join(f'<li><a href="{screen}/">{screen.replace("_", " ")}</a></li>' for screen in screens)
    return HttpResponse(f'<!doctype html><meta name="viewport" content="width=device-width"><title>UI Showcase</title><style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;background:#f5f7fa;color:#172b4d}}ul{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;padding:0;list-style:none}}a{{display:block;padding:16px;background:white;border:1px solid #e2e8f0;border-radius:8px;color:#3d6fb6;text-decoration:none;text-transform:capitalize}}</style><h1>CivicOps UI Showcase</h1><p>All {len(screens)} supplied screen designs</p><ul>{links}</ul>')

urlpatterns = [
    path("ui-showcase/", ui_showcase, name="ui_showcase"),
    path("ui-showcase/<str:screen>/", ui_showcase, name="ui_showcase_screen"),
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
