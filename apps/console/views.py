from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint
from apps.geography.models import Department, RoutingRule, Ward
from apps.workflow.permissions import can_transition
from apps.workflow.services import transition

from .forms import AssignComplaintForm, RejectComplaintForm, RouteComplaintForm, TransferComplaintForm


def _triage_user(user):
    return user.is_authenticated and user.role in {User.Role.TRIAGE_REVIEWER, User.Role.ADMIN}


def _department_user(user):
    return user.is_authenticated and user.role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR}


def _active_routing_rule(complaint):
    # A ward-specific current rule takes precedence over a current all-wards rule.
    rules = RoutingRule.objects.filter(category=complaint.category, effective_from__lte=timezone.now()).order_by("-version")
    rule = rules.filter(ward_id=complaint.ward_id).first() if complaint.ward_id else None
    return rule or rules.filter(ward__isnull=True).first()


@login_required
def triage_queue(request):
    if not _triage_user(request.user):
        raise Http404
    complaints = Complaint.objects.visible_to(request.user).select_related(
        "citizen", "category", "ward", "department"
    ).exclude(status__in=[Complaint.Status.VERIFIED_CLOSED, Complaint.Status.REJECTED, Complaint.Status.CANCELLED])
    status = request.GET.get("status")
    ward_id = request.GET.get("ward")
    valid_statuses = {value for value, _label in Complaint.Status.choices}
    if status in valid_statuses:
        complaints = complaints.filter(status=status)
    if ward_id and ward_id.isdecimal():
        complaints = complaints.filter(ward_id=ward_id)
    return render(request, "console/triage_queue.html", {
        "complaints": complaints.order_by("due_at", "created_at"),
        "statuses": Complaint.Status.choices,
        "wards": Ward.objects.order_by("name"),
        "selected_status": status or "",
        "selected_ward": ward_id or "",
        "departments": Department.objects.order_by("name"),
    })


@login_required
def route_complaint(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if not _triage_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.ROUTED):
        raise Http404
    if request.method != "POST":
        raise Http404
    form = RouteComplaintForm(request.POST)
    if form.is_valid():
        rule = _active_routing_rule(complaint)
        if not rule:
            messages.error(request, "No active ward or category routing rule is configured for this complaint.")
        else:
            department = form.cleaned_data["department"] or rule.department
            reason = form.cleaned_data["reason"].strip()
            overridden = department.pk != rule.department_id
            if overridden and not reason:
                messages.error(request, "Give a reason when overriding the routing rule.")
            elif request.user.role == User.Role.ADMIN and not reason:
                messages.error(request, "An administrator override requires a reason.")
            else:
                transition(complaint, Complaint.Status.ROUTED, actor=request.user,
                    reason=reason if overridden or request.user.role == User.Role.ADMIN else None,
                    department=department, rule_version=rule.version)
                AuditEvent.objects.create(actor=request.user, role=request.user.role, action="complaint_routed",
                    object_type="Complaint", object_id=str(complaint.pk),
                    after={"department_id": department.pk, "routing_rule_version": rule.version, "overridden": overridden},
                    reason=reason if overridden else "")
                messages.success(request, "Complaint routed to the department.")
                return redirect("triage_queue")
    else:
        messages.error(request, "Choose a valid department and provide any required override reason.")
    return redirect("triage_queue")


@login_required
def reject_complaint(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if not _triage_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.REJECTED):
        raise Http404
    if request.method != "POST":
        raise Http404
    form = RejectComplaintForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a rejection reason (at least three characters).")
        return redirect("triage_queue")
    transition(complaint, Complaint.Status.REJECTED, actor=request.user, reason=form.cleaned_data["reason"].strip())
    messages.success(request, "Complaint rejected with the recorded reason.")
    return redirect("triage_queue")


@login_required
def department_inbox(request):
    if not _department_user(request.user):
        raise Http404
    complaints = Complaint.objects.visible_to(request.user).filter(
        status__in=[Complaint.Status.ROUTED, Complaint.Status.ACKNOWLEDGED]
    ).select_related("citizen", "category", "ward", "department", "assignee").order_by("due_at", "created_at")
    return render(request, "console/department_inbox.html", {"complaints": complaints})


@login_required
def acknowledge_complaint(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not _department_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.ACKNOWLEDGED):
        raise Http404
    transition(complaint, Complaint.Status.ACKNOWLEDGED, actor=request.user)
    messages.success(request, "Complaint acknowledged.")
    return redirect("department_inbox")


@login_required
def transfer_to_triage(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not _department_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.IN_TRIAGE):
        raise Http404
    form = TransferComplaintForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a transfer or rejected-responsibility reason.")
        return redirect("department_inbox")
    transition(complaint, Complaint.Status.IN_TRIAGE, actor=request.user, reason=form.cleaned_data["reason"].strip())
    messages.success(request, "Complaint returned to triage for manual review and routing.")
    return redirect("department_inbox")


@login_required
def assign_complaint(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not _department_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.ASSIGNED):
        raise Http404
    form = AssignComplaintForm(request.POST, department=complaint.department)
    if not form.is_valid():
        messages.error(request, "Choose an active field worker from this department.")
        return redirect("department_inbox")
    transition(complaint, Complaint.Status.ASSIGNED, actor=request.user,
        department=complaint.department, assignee=form.cleaned_data["assignee"])
    messages.success(request, "Complaint assigned to the field worker.")
    return redirect("department_inbox")
