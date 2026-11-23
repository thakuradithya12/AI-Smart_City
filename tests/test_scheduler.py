from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.scheduler.models import SchedulerHeartbeat


@pytest.mark.django_db
def test_scheduler_reports_fresh_and_stale_heartbeat(client):
    heartbeat = SchedulerHeartbeat.objects.create(singleton=1, last_seen_at=timezone.now())
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scheduler": "ok"}

    heartbeat.last_seen_at = timezone.now() - timedelta(minutes=10)
    heartbeat.save(update_fields=["last_seen_at"])
    response = client.get("/healthz/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "scheduler": "stale"}


def test_scheduler_once_runs_all_known_jobs_and_releases_lock(monkeypatch):
    import apps.scheduler.management.commands.run_scheduler as scheduler

    calls = []
    heartbeats = []
    monkeypatch.setattr(scheduler, "connection", SimpleNamespace(vendor="postgresql", ensure_connection=lambda: None))
    monkeypatch.setattr(scheduler.Command, "_try_lock", lambda self: True)
    monkeypatch.setattr(scheduler.Command, "_unlock", lambda self: calls.append("unlock"))
    monkeypatch.setattr(scheduler, "get_commands", lambda: set(scheduler.JOBS))
    monkeypatch.setattr(scheduler, "call_command", lambda name: calls.append(name))
    monkeypatch.setattr(
        SchedulerHeartbeat.objects,
        "update_or_create",
        lambda **kwargs: heartbeats.append(kwargs),
    )

    call_command("run_scheduler", once=True)

    assert set(calls[:-1]) == set(scheduler.JOBS)
    assert calls[-1] == "unlock"
    assert len(heartbeats) == 1


def test_second_scheduler_exits_when_advisory_lock_is_held(monkeypatch):
    import apps.scheduler.management.commands.run_scheduler as scheduler

    calls = []
    monkeypatch.setattr(scheduler, "connection", SimpleNamespace(vendor="postgresql", ensure_connection=lambda: None))
    monkeypatch.setattr(scheduler.Command, "_try_lock", lambda self: False)
    monkeypatch.setattr(scheduler, "call_command", lambda name: calls.append(name))

    call_command("run_scheduler", once=True)

    assert calls == []
