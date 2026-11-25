from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import PrivacyDeletionRequest, User
from apps.complaints.forms import PhoneAuthenticationForm
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint


class WorkspaceLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True


def privacy_notice(request):
    pending_deletion = False
    if request.user.is_authenticated:
        pending_deletion = PrivacyDeletionRequest.objects.filter(
            user=request.user, processed_at__isnull=True
        ).exists()
    return render(request, "privacy.html", {
        "pending_deletion": pending_deletion,
        "privacy_notice_version": settings.PRIVACY_NOTICE_VERSION,
        "deletion_request_days": settings.DELETION_REQUEST_DAYS,
    })


@login_required
def export_my_data(request):
    user = request.user
    # Scope all complaint data to the authenticated user's visible complaints before selecting their records.
    complaints = Complaint.objects.visible_to(user).filter(
        Q(citizen=user) | Q(assignee=user)
    ).select_related("category", "ward", "department").order_by("created_at", "pk")
    complaint_rows = []
    for complaint in complaints:
        complaint_rows.append({
            "public_id": complaint.public_id,
            "category": complaint.category.name,
            "description": complaint.description,
            "landmark": complaint.landmark,
            "location": (
                {"latitude": complaint.location.y, "longitude": complaint.location.x}
                if complaint.location else None
            ),
            "gps_accuracy_m": complaint.gps_accuracy_m,
            "ward": complaint.ward.name if complaint.ward_id else None,
            "status": complaint.status,
            "created_at": complaint.created_at.isoformat(),
            "consent_at": complaint.consent_at.isoformat(),
            "consent_version": complaint.consent_version,
            "status_history": [
                {
                    "from": event.from_status,
                    "to": event.to_status,
                    "role": event.role,
                    "reason": event.reason,
                    "created_at": event.created_at.isoformat(),
                }
                for event in complaint.status_events.order_by("created_at", "pk")
            ],
            "messages": [
                {"body": message.body, "created_at": message.created_at.isoformat()}
                for message in complaint.messages.filter(author=user).order_by("created_at", "pk")
            ],
            "evidence": [
                {
                    "kind": evidence.kind,
                    "sha256": evidence.sha256,
                    "uploaded_at": evidence.uploaded_at.isoformat(),
                }
                for evidence in complaint.evidence.filter(uploaded_by=user).order_by("uploaded_at", "pk")
            ],
        })

    payload = {
        "exported_at": timezone.now().isoformat(),
        "account": {
            "name": user.name,
            "phone_number": user.phone_number,
            "email": user.email,
            "role": user.role,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "complaints": complaint_rows,
        "audit_actions": list(
            AuditEvent.objects.filter(actor=user).order_by("created_at", "pk").values(
                "action", "object_type", "created_at"
            )
        ),
    }
    for row in payload["audit_actions"]:
        row["created_at"] = row["created_at"].isoformat()
    response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    response["Content-Disposition"] = 'attachment; filename="ai-smart-city-data.json"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def request_account_deletion(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    if request.user.role != User.Role.CITIZEN:
        raise Http404
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=request.user.pk)
        pending, created = PrivacyDeletionRequest.objects.get_or_create(
            user=locked_user, processed_at__isnull=True
        )
    if created:
        messages.success(
            request,
            f"Your deletion request is queued. We will anonymise your account within {settings.DELETION_REQUEST_DAYS} days.",
        )
    else:
        messages.info(request, "A deletion request for your account is already pending.")
    return redirect("privacy_notice")
