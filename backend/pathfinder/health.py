from django.db import connection
from django.http import JsonResponse


def livez(request):
    """Process is up and routing requests. No dependency checks.

    Liveness probe target: if this doesn't respond, the pod itself is
    broken and k8s should restart it.
    """
    return JsonResponse({"status": "ok"})


def healthz(request):
    """Process is up AND its database dependency is reachable.

    Readiness probe target: if the DB is down, this returns 503 so the
    Load Balancer stops routing to this pod instead of serving 500s.
    The DB has no standby (see the ADR's accepted single-point-of-failure
    tradeoff), so every pod goes not-ready together during a DB outage,
    that's expected, not a bug in this check.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
