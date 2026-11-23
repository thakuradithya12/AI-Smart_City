from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.utils import timezone

from apps.scheduler.models import SchedulerHeartbeat


def _health_response(status, http_status=200, **extra):
    response = JsonResponse({"status": status, **extra}, status=http_status)
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def healthz(request):
    """Check database connectivity without exposing application data or exception details."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                return _health_response("unavailable", 503)
        heartbeat = SchedulerHeartbeat.objects.filter(singleton=1).first()
        if heartbeat is None:
            scheduler = "unknown"
        elif (timezone.now() - heartbeat.last_seen_at).total_seconds() > settings.SCHEDULER_HEARTBEAT_STALE_SECONDS:
            scheduler = "stale"
        else:
            scheduler = "ok"
    except DatabaseError:
        return _health_response("unavailable", 503)
    status = "unavailable" if scheduler == "stale" else "ok"
    return _health_response(
        status,
        http_status=503 if status == "unavailable" else 200,
        scheduler=scheduler,
    )
