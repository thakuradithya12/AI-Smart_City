from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
from apps.complaints.views import complaint_detail, evidence_file, my_complaints, register, report
from . import views as workflow_views

@login_required
def home(request):
    return render(request, "home.html")

urlpatterns = [
    path("", home, name="home"),
    path("register/", register, name="register"),
    path("complaints/new/", report, name="report"),
    path("complaints/", my_complaints, name="my_complaints"),
    path("complaints/<int:pk>/", complaint_detail, name="complaint_detail"),
    path("evidence/<int:pk>/", evidence_file, name="evidence_file"),
    path("console/triage/", workflow_views.triage_queue, name="triage_queue"),
    path("console/triage/<int:pk>/route/", workflow_views.route_complaint, name="route_complaint"),
    path("console/triage/<int:pk>/reject/", workflow_views.reject_complaint, name="reject_complaint"),
    path("console/department/", workflow_views.department_inbox, name="department_inbox"),
    path("console/department/<int:pk>/acknowledge/", workflow_views.acknowledge_complaint, name="acknowledge_complaint"),
    path("console/department/<int:pk>/transfer/", workflow_views.transfer_to_triage, name="transfer_to_triage"),
    path("console/department/<int:pk>/assign/", workflow_views.assign_complaint, name="assign_complaint"),
]
