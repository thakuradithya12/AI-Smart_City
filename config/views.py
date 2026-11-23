from django.db import DatabaseError, connection
from django.http import JsonResponse


def _health_response(status, http_status=200):
    response = JsonResponse({"status": status}, status=http_status)
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
    except DatabaseError:
        return _health_response("unavailable", 503)
    return _health_response("ok")
