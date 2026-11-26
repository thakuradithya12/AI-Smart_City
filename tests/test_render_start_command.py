from pathlib import Path


START_COMMAND = Path(__file__).resolve().parents[1] / "scripts" / "start_render.sh"


def test_render_start_migrates_and_collects_static_before_serving():
    script = START_COMMAND.read_text(encoding="utf-8")

    migrate = script.index("python manage.py migrate --noinput")
    seed_categories = script.index("python manage.py seed_categories")
    collectstatic = script.index("python manage.py collectstatic --noinput")
    seed_flag = script.index('"${DEMO_SEED:-0}"')
    seed_command = script.index("python manage.py seed_demo --force")
    server = script.index("exec gunicorn")

    assert migrate < seed_categories < collectstatic < seed_flag < seed_command < server
    assert '0) ;;' in script
    assert '1) python manage.py seed_demo --force ;;' in script
    assert '*) echo "DEMO_SEED must be 0 or 1."' in script
    assert '"${WEB_CONCURRENCY:-1}"' in script
    assert '"${GUNICORN_THREADS:-2}"' in script
    assert '"0.0.0.0:${PORT:-10000}"' in script
