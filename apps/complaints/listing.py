from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.complaints.models import Complaint
from apps.geography.models import Category, Ward


FINAL_STATUSES = (
    Complaint.Status.VERIFIED_CLOSED,
    Complaint.Status.REJECTED,
    Complaint.Status.CANCELLED,
)


def filter_and_paginate_complaints(queryset, request, *, allowed_statuses=None):
    """Apply the shared safe filters, then paginate the already role-scoped queryset."""
    params = request.GET
    status = params.get("status", "")
    valid_statuses = {value for value, _label in Complaint.Status.choices}
    if status in valid_statuses:
        if allowed_statuses is not None and status not in allowed_statuses:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(status=status)

    ward_id = params.get("ward", "")
    if ward_id.isdecimal():
        queryset = queryset.filter(ward_id=ward_id)
    category_id = params.get("category", "")
    if category_id.isdecimal():
        queryset = queryset.filter(category_id=category_id)
    query = params.get("q", "").strip()[:120]
    if query:
        queryset = queryset.filter(Q(public_id__icontains=query) | Q(description__icontains=query))
    overdue = params.get("overdue", "") == "1"
    if overdue:
        queryset = queryset.filter(due_at__lt=timezone.now()).exclude(status__in=FINAL_STATUSES)

    page_size = max(1, min(100, int(getattr(settings, "LIST_PAGE_SIZE", 20))))
    page = Paginator(queryset, page_size).get_page(params.get("page"))
    query_params = params.copy()
    query_params.pop("page", None)
    return {
        "complaints": page,
        "statuses": Complaint.Status.choices,
        "wards": Ward.objects.order_by("name"),
        "categories": Category.objects.order_by("name"),
        "selected_status": status,
        "selected_ward": ward_id,
        "selected_category": category_id,
        "selected_overdue": overdue,
        "search_query": query,
        "query_string": query_params.urlencode(),
    }
