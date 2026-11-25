from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.forms import CitizenRegistrationForm, ReportForm
from apps.complaints.models import Complaint, ComplaintMessage, Evidence
from apps.complaints.listing import filter_and_paginate_complaints
from apps.complaints.services import delete_private_files, private_storage, store_citizen_image
from apps.geography.services import active_ward_for_point
from apps.workflow.services import potential_duplicates, transition
from apps.workflow.permissions import can_transition
from apps.console.forms import AssignComplaintForm, MessageForm, ReasonForm, VerifyForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = CitizenRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="apps.accounts.backends.PhoneOrLegacyEmailBackend")
        return redirect("dashboard")
    return render(request, "complaints/register.html", {"form": form})


@login_required
def report(request):
    if request.user.role != User.Role.CITIZEN:
        raise Http404
    # Limit every authenticated report POST before parsing or storing its uploaded image.
    if request.method == "POST":
        limit = getattr(settings, "REPORT_POST_LIMIT", 5)
        window = getattr(settings, "REPORT_POST_WINDOW_SECONDS", 3600)
        key = f"report-post:{request.user.pk}"
        try:
            if not cache.add(key, 1, timeout=window):
                try:
                    count = cache.incr(key)
                except ValueError:
                    count = 1 if cache.add(key, 1, timeout=window) else limit + 1
                if count > limit:
                    return HttpResponse("Report limit reached. Please try again later.", status=429)
        except Exception:
            # Fail closed if the shared limiter is unavailable; report creation must not bypass the limit.
            return HttpResponse("Reporting is temporarily unavailable. Please try again later.", status=503)
    form = ReportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        longitude = float(form.cleaned_data["longitude"])
        latitude = float(form.cleaned_data["latitude"])
        point = Point(longitude, latitude, srid=4326)
        # Only one active local ward may claim the confirmed pin; ambiguous jurisdiction fails closed.
        try:
            ward = active_ward_for_point(point)
        except ValidationError as exc:
            form.add_error(None, " ".join(exc.messages))
            ward = None
        if form.errors:
            return render(request, "complaints/report.html", {
                "form": form,
                "max_photos": getattr(settings, "REPORT_MAX_PHOTOS", 3),
                "map_tile_url": settings.MAP_TILE_URL,
            })
        if ward is None:
            form.add_error(None, "That pin is outside the supported area. Please choose a location inside a supported ward.")
        else:
            paths = []
            try:
                with transaction.atomic():
                    category = form.cleaned_data["category"]
                    complaint = Complaint.objects.create(
                        citizen=request.user, category=category,
                        description=form.cleaned_data["description"], landmark=form.cleaned_data["landmark"], location=point,
                        gps_accuracy_m=form.cleaned_data["gps_accuracy_m"],
                        ward=ward, due_at=timezone.now() + timedelta(hours=category.default_due_hours),
                        consent_at=timezone.now(),
                        consent_version=settings.PRIVACY_NOTICE_VERSION,
                    )
                    complaint.public_id = f"ASC-{timezone.localdate():%Y}-{complaint.pk:06d}"
                    complaint.save(update_fields=["public_id"])
                    for photo in form.cleaned_data["photo"]:
                        original_path, display_path, thumbnail_path, image_hash = store_citizen_image(photo)
                        paths.extend((original_path, display_path, thumbnail_path))
                        Evidence.objects.create(
                            complaint=complaint,
                            kind=Evidence.Kind.CITIZEN,
                            original_path=original_path,
                            display_path=display_path,
                            thumbnail_path=thumbnail_path,
                            sha256=image_hash,
                            uploaded_by=request.user,
                        )
                    AuditEvent.objects.create(actor=request.user, role=request.user.role, action="complaint_submitted",
                        object_type="Complaint", object_id=str(complaint.pk), after={"status": "submitted", "ward": ward.pk})
                    transition(complaint, Complaint.Status.IN_TRIAGE, actor=None)
            except ValidationError as exc:
                delete_private_files(paths)
                for error in exc.messages:
                    form.add_error(None, error)
            except Exception:
                delete_private_files(paths)
                raise
            else:
                return redirect("complaint_detail", pk=complaint.pk)
    return render(request, "complaints/report.html", {
        "form": form,
        "max_photos": getattr(settings, "REPORT_MAX_PHOTOS", 3),
        "map_tile_url": settings.MAP_TILE_URL,
    })


@login_required
def my_complaints(request):
    if request.user.role != User.Role.CITIZEN:
        raise Http404
    complaints = Complaint.objects.visible_to(request.user).select_related("category", "ward").order_by("-created_at", "-pk")
    context = filter_and_paginate_complaints(complaints, request)
    return render(request, "complaints/my_complaints.html", context)


@login_required
def complaint_detail(request, pk):
    # Eager-load timeline actors and resolution users so a longer history adds no per-row queries.
    complaints = Complaint.objects.visible_to(request.user).select_related(
        "category", "ward", "department", "citizen", "assignee", "duplicate_of",
        "resolution__claimed_by", "resolution__verified_by",
    ).prefetch_related(
        "status_events",
        "evidence",
        Prefetch("messages", queryset=ComplaintMessage.objects.select_related("author")),
    )
    complaint = get_object_or_404(complaints, pk=pk)
    can_review_duplicates = request.user.role == User.Role.TRIAGE_REVIEWER and complaint.status == Complaint.Status.IN_TRIAGE
    status_labels = dict(Complaint.Status.choices)
    timeline = [
        {"kind": "status", "created_at": event.created_at, "label": status_labels.get(event.to_status, event.to_status), "reason": event.reason}
        for event in complaint.status_events.all()
    ]
    timeline.extend(
        {"kind": "message", "created_at": message.created_at, "label": message.author.name, "body": message.body}
        for message in complaint.messages.all()
    )
    timeline.extend(
        {"kind": "evidence", "created_at": evidence.uploaded_at, "label": evidence.get_kind_display(), "evidence": evidence}
        for evidence in complaint.evidence.all()
    )
    timeline.extend(
        {"kind": "assignment", "created_at": event.created_at}
        for event in AuditEvent.objects.filter(
            Q(action="complaint_reassigned") | Q(action="admin_override", after__operation="complaint_reassigned"),
            object_type="Complaint", object_id=str(complaint.pk),
        )
    )
    timeline.sort(key=lambda item: item["created_at"])
    can_reassign = (
        (complaint.status in {Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS}
         and request.user.role in {User.Role.SUPERVISOR, User.Role.DEPARTMENT_OFFICIAL, User.Role.ADMIN}
         and (request.user.role == User.Role.ADMIN or request.user.department_id == complaint.department_id))
        or (complaint.status == Complaint.Status.REOPENED and request.user.role == User.Role.SUPERVISOR)
    )
    field_workers = User.objects.none()
    if can_reassign and complaint.department_id:
        field_workers = User.objects.filter(
            department_id=complaint.department_id,
            role=User.Role.FIELD_WORKER,
            is_active=True,
        ).order_by("name")
    return render(request, "complaints/detail.html", {
        "complaint": complaint,
        "can_review_duplicates": can_review_duplicates,
        "duplicate_candidates": potential_duplicates(complaint) if can_review_duplicates else (),
        "timeline": timeline,
        "can_cancel": can_transition(request.user, complaint, Complaint.Status.CANCELLED),
        "can_reply": can_transition(request.user, complaint, Complaint.Status.IN_TRIAGE) and complaint.status == Complaint.Status.INFO_REQUESTED,
        "can_verify": can_transition(request.user, complaint, Complaint.Status.VERIFIED_CLOSED),
        "can_dispute": can_transition(request.user, complaint, Complaint.Status.REOPENED),
        "can_request_info": can_transition(request.user, complaint, Complaint.Status.INFO_REQUESTED),
        "can_reassign": can_reassign,
        "field_workers": field_workers,
        "verify_form": VerifyForm(), "reason_form": ReasonForm(), "message_form": MessageForm(),
        "assign_form": AssignComplaintForm(department=complaint.department) if can_reassign else None,
    })


@login_required
def evidence_file(request, pk):
    evidence = get_object_or_404(Evidence.objects.select_related("complaint"), pk=pk)
    if not Complaint.objects.visible_to(request.user).filter(pk=evidence.complaint_id).exists():
        raise Http404
    response = FileResponse(private_storage.open(evidence.display_path, "rb"), content_type="image/jpeg")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response
