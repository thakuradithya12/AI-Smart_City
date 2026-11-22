from apps.complaints.models import Complaint
from apps.workflow.services import TRANSITIONS


def allowed_transition_targets(user, complaint):
    """Return status targets permitted by role and object visibility; default deny."""
    if not user.is_authenticated or not Complaint.objects.visible_to(user).filter(pk=complaint.pk).exists():
        return set()
    role = user.role
    return {
        to_status
        for (from_status, to_status), roles in TRANSITIONS.items()
        if from_status == complaint.status and role in roles
    }


def can_transition(user, complaint, to_status):
    return to_status in allowed_transition_targets(user, complaint)


def can_link_duplicate(user, complaint):
    """Only an active triage reviewer may link a candidate during triage."""
    return bool(
        user.is_authenticated
        and user.is_active
        and user.role == "triage_reviewer"
        and complaint.status == Complaint.Status.IN_TRIAGE
        and Complaint.objects.visible_to(user).filter(pk=complaint.pk).exists()
    )
