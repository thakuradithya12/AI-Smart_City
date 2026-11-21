from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence
from apps.complaints.services import delete_private_files, store_citizen_image
from apps.geography.models import Department, Ward
from apps.workflow.permissions import can_transition
from apps.workflow.services import route_complaint as route_complaint_service, transition

from .forms import (AssignComplaintForm, FieldEvidenceForm, MessageForm, ReasonForm, RejectComplaintForm,
                    RouteComplaintForm, TransferComplaintForm, VerifyForm, WorkDoneForm)


def _triage_user(user):
    return user.is_authenticated and user.role in {User.Role.TRIAGE_REVIEWER, User.Role.ADMIN}


def _department_user(user):
    return user.is_authenticated and user.role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR}


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
        try:
            route_complaint_service(
                complaint,
                actor=request.user,
                department_override=form.cleaned_data["department"],
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
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
        messages.error(request, "Enter a rejection reason of 5 to 500 characters.")
        return redirect("triage_queue")
    transition(complaint, Complaint.Status.REJECTED, actor=request.user, reason=form.cleaned_data["reason"].strip())
    messages.success(request, "Complaint rejected with the recorded reason.")
    return redirect("triage_queue")


@login_required
def department_inbox(request):
    if not _department_user(request.user):
        raise Http404
    complaints = Complaint.objects.visible_to(request.user).filter(
        status__in=[Complaint.Status.ROUTED, Complaint.Status.ACKNOWLEDGED, Complaint.Status.RESOLVED_PENDING_VERIFICATION, Complaint.Status.REOPENED]
    ).select_related("citizen", "category", "ward", "department", "assignee").order_by("due_at", "created_at")
    status = request.GET.get("status")
    if status in {value for value, _ in Complaint.Status.choices}:
        complaints = complaints.filter(status=status)
    return render(request, "console/department_inbox.html", {"complaints": complaints, "statuses": Complaint.Status.choices, "selected_status": status or ""})


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


@login_required
def field_tasks(request):
    if request.user.role != User.Role.FIELD_WORKER:
        raise Http404
    complaints = Complaint.objects.visible_to(request.user).filter(
        status__in=[Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS]
    ).select_related("category", "ward", "department").order_by("due_at", "created_at")
    return render(request, "console/field_tasks.html", {"complaints": complaints})


@login_required
def field_task_detail(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.user.role != User.Role.FIELD_WORKER:
        raise Http404
    return render(request, "console/field_task_detail.html", {"complaint": complaint, "evidence_form": FieldEvidenceForm(), "done_form": WorkDoneForm()})


@login_required
def start_work(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or request.user.role != User.Role.FIELD_WORKER or not can_transition(request.user, complaint, Complaint.Status.IN_PROGRESS):
        raise Http404
    transition(complaint, Complaint.Status.IN_PROGRESS, actor=request.user)
    return redirect("field_task_detail", pk=pk)


@login_required
def upload_field_evidence(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or request.user.role != User.Role.FIELD_WORKER or complaint.status != Complaint.Status.IN_PROGRESS:
        raise Http404
    form = FieldEvidenceForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Choose a valid before or after photo.")
        return redirect("field_task_detail", pk=pk)
    paths = []
    try:
        original, display, digest = store_citizen_image(form.cleaned_data["photo"])
        paths.extend((original, display))
        with transaction.atomic():
            evidence = Evidence.objects.create(complaint=complaint, kind=form.cleaned_data["kind"], original_path=original,
                display_path=display, sha256=digest, uploaded_by=request.user)
            AuditEvent.objects.create(actor=request.user, role=request.user.role, action="evidence_uploaded", object_type="Evidence",
                object_id=str(evidence.pk), after={"complaint_id": complaint.pk, "kind": evidence.kind, "sha256": digest})
    except ValidationError as exc:
        delete_private_files(paths)
        messages.error(request, " ".join(exc.messages))
        return redirect("field_task_detail", pk=pk)
    except Exception:
        delete_private_files(paths)
        raise
    messages.success(request, "Photo added to the complaint timeline.")
    return redirect("field_task_detail", pk=pk)


@login_required
def mark_work_done(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or request.user.role != User.Role.FIELD_WORKER or not can_transition(request.user, complaint, Complaint.Status.RESOLVED_PENDING_VERIFICATION):
        raise Http404
    form = WorkDoneForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a work note of at least five characters.")
        return redirect("field_task_detail", pk=pk)
    try:
        transition(complaint, Complaint.Status.RESOLVED_PENDING_VERIFICATION, actor=request.user, note=form.cleaned_data["note"])
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("field_task_detail", pk=pk)
    return redirect("complaint_detail", pk=pk)


@login_required
def verify_resolution(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not can_transition(request.user, complaint, Complaint.Status.VERIFIED_CLOSED):
        raise Http404
    form = VerifyForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choose a verification method.")
        return redirect("complaint_detail", pk=pk)
    method = form.cleaned_data["method"]
    if request.user.role == User.Role.CITIZEN:
        method = "citizen_confirmation"
    elif method != "site_review":
        messages.error(request, "A supervisor verification must use the site review method.")
        return redirect("complaint_detail", pk=pk)
    transition(complaint, Complaint.Status.VERIFIED_CLOSED, actor=request.user, method=method)
    return redirect("complaint_detail", pk=pk)


@login_required
def dispute_resolution(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not can_transition(request.user, complaint, Complaint.Status.REOPENED):
        raise Http404
    form = ReasonForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a dispute reason of 5 to 500 characters.")
        return redirect("complaint_detail", pk=pk)
    transition(complaint, Complaint.Status.REOPENED, actor=request.user, reason=form.cleaned_data["reason"].strip())
    return redirect("complaint_detail", pk=pk)


@login_required
def citizen_cancel(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not can_transition(request.user, complaint, Complaint.Status.CANCELLED):
        raise Http404
    transition(complaint, Complaint.Status.CANCELLED, actor=request.user)
    return redirect("complaint_detail", pk=pk)


@login_required
def request_information(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or not _triage_user(request.user) or not can_transition(request.user, complaint, Complaint.Status.INFO_REQUESTED):
        raise Http404
    form = MessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter an information request message.")
        return redirect("triage_queue")
    transition(complaint, Complaint.Status.INFO_REQUESTED, actor=request.user, message=form.cleaned_data["message"])
    return redirect("triage_queue")


@login_required
def citizen_reply(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or request.user.role != User.Role.CITIZEN or not can_transition(request.user, complaint, Complaint.Status.IN_TRIAGE):
        raise Http404
    form = MessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a reply of at least five characters.")
        return redirect("complaint_detail", pk=pk)
    transition(complaint, Complaint.Status.IN_TRIAGE, actor=request.user, reply=form.cleaned_data["message"])
    return redirect("complaint_detail", pk=pk)


@login_required
def supervisor_reassign(request, pk):
    complaint = get_object_or_404(Complaint.objects.visible_to(request.user), pk=pk)
    if request.method != "POST" or request.user.role != User.Role.SUPERVISOR or not can_transition(request.user, complaint, Complaint.Status.ASSIGNED):
        raise Http404
    form = AssignComplaintForm(request.POST, department=complaint.department)
    if not form.is_valid():
        messages.error(request, "Choose an active field worker from this department.")
        return redirect("complaint_detail", pk=pk)
    transition(complaint, Complaint.Status.ASSIGNED, actor=request.user, assignee=form.cleaned_data["assignee"])
    return redirect("complaint_detail", pk=pk)
