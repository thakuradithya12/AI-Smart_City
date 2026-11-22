from django.core.exceptions import ValidationError

from apps.geography.models import Ward


def active_ward_for_point(point, *, day=None):
    matches = list(
        Ward.objects.active_on(day)
        .filter(boundary__covers=point)
        .order_by("pk")[:2]
    )
    # Refuse ambiguous jurisdiction instead of assigning a report by database row order.
    if len(matches) > 1:
        raise ValidationError(
            "This pin is covered by multiple active wards. Please contact support while the service area is reviewed."
        )
    return matches[0] if matches else None
