# Technical decisions

| Date | Choice | Reason | Alternative rejected |
|---|---|---|---|
| 2026-11-18 | Python 3.12.16 slim Trixie image | Locked Python 3.12 stack; official Python image publishes this patch/tag. | Host Python 3.15 is outside the specified runtime. |
| 2026-11-18 | Django 5.2.19 LTS | `pip install --dry-run` confirmed 5.2.19 is the newest published 5.2.x; it supports Python 3.12 and is the current available 5.2 LTS patch. Release notes report four low and one moderate security fixes, including GeoJSON CRS and `SpatialReference` SSRF protections. | Django 5.2.20 does not exist on PyPI; Django 6.2 LTS is not released yet. |
| 2026-11-18 | PostGIS image `postgis/postgis:17-3.7` | Current stable PostGIS 3.7 Debian image compatible with PostgreSQL 17; keeps the PostgreSQL 18 volume-path migration out of this short build. | Floating `latest` and master tags are not reproducible; PostgreSQL 18 changes the volume path. |
| 2026-11-18 | Psycopg 3.3.9 binary extra | Current Psycopg 3 release and Django PostgreSQL driver path; binary wheel avoids system compilation in the app image. | Psycopg 2 is the older driver line. |
| 2026-11-18 | Pillow 13.0.0; WhiteNoise 6.11.0; Gunicorn 27.0.1; django-axes 9.0.0 | Current releases verified on PyPI; Axes 9 explicitly supports Django 5.2. | Older versions were pinned before current-release review and were replaced. |
| 2026-11-18 | pytest 9.2.0; pytest-django 4.14.0; factory_boy 3.3.3; Ruff 0.16.8; pip-audit 2.10.1; Bandit 1.9.4 | Current documented/PyPI releases selected for test, lint, dependency and static security checks. | Unpinned dependency ranges. |
| 2026-11-18 | `django.contrib.gis` with PostGIS, geometry SRID 4326 | Required by frozen stack and location/ward requirements. | SQLite or planar geometry distances do not meet the requirement. |
| 2026-11-18 | No public deployment in Day 1 | Owner supplied “none yet” for server/domain; local work only and public deploy gate explicitly blocked. | Invented host or deployment account. |
| 2026-11-18 | No pilot ward fixtures | Centre coordinates and hand-drawn polygons were left as placeholders. | Invented pilot coordinates or boundaries. |
| 2026-11-18 | Docker pip install uses 120-second timeout and 10 retries | The pasted first build failed while downloading Django due a socket read timeout; pip documents a 15-second default timeout and configurable retry count. | Relying on a short default timeout after a transient slow PyPI response. |
| 2026-11-18 | Generate initial migrations by explicit app labels for accounts, geography, complaints, and ai_assist | Bare `makemigrations` initially generated only the already-migrated audit app; explicit labels generated the remaining model migrations. | Assuming the first bare command will generate initial migrations for apps without migration packages. |
| 2026-11-18 | Development uses regular static storage and omits WhiteNoise middleware | Test/dev runs do not collect a production manifest; source static files are served by Django's development server. Production retains WhiteNoise manifest storage. | Requiring `collectstatic` just to render the local login template. |
| 2026-11-19 | Compose `checks` service installs `requirements/dev.txt` before pytest, Ruff and pip-audit | The production `web` image intentionally installs only `requirements/base.txt`; running pytest or Ruff directly in it fails because those commands are absent. | Adding development-only tools to the production web image. |
| 2026-11-19 | Dev checks pip install uses a 120-second timeout and 10 retries | The check container hit a transient read timeout while downloading Ruff from files.pythonhosted.org. | The pip 15-second default timeout and default retry count. |
| 2026-11-19 | Compose `checks` service bind-mounts the working tree at `/app` | Compose reused the prior check image after a source-only test edit; a source mount keeps each Docker verification run aligned with current files without a rebuild. | Testing an old copied source snapshot from the cached image. |
| 2026-11-19 | Bootstrap 5.3.8 (MIT) and Leaflet 1.9.4 (BSD-2-Clause), locally vendored | Bootstrap's official 5.3 docs show 5.3.8 assets and integrity hashes; Leaflet's installation guide recommends 1.9.4 for the stable 1.x classic-script API. Workspace DNS prevented fetching; use the documented PowerShell download and hash check before browser testing. | Remote runtime CDNs and unpinned latest versions. |
| 2026-11-19 | GPS accuracy stored to two decimal places | Browser geolocation reports accuracy as a measurement that may include fractions; retain that value instead of truncating it to an integer. | Integer truncation. |
| 2026-11-19 | Pin confirmation is a required server-validated form field | Client-side checks can be bypassed; server validation ensures the citizen confirms the submitted pin. | JavaScript-only confirmation. |
| 2026-11-19 | Transition targets are derived from the section 8 table and role visibility in `apps/workflow/permissions.py` | Console actions and tests need one server-side permission helper; the transition service remains the only writer of complaint status. | Repeating role and status checks in each view. |
| 2026-11-19 | Information request and citizen reply messages are created inside `transition()` and receive a separate audit event | Message content is part of the workflow record and must commit or roll back with the status change. | Saving messages independently in console views. |

## Verification sources

- [Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/) and [GeoDjango installation](https://docs.djangoproject.com/en/5.2/ref/contrib/gis/install/).
- [PostGIS official image overview and tag guidance](https://hub.docker.com/r/postgis/postgis/).
- [Python official image tags](https://hub.docker.com/_/python/tags).
- [Psycopg on PyPI](https://pypi.org/project/psycopg/), [Pillow on PyPI](https://pypi.org/project/pillow/), [WhiteNoise on PyPI](https://pypi.org/project/whitenoise/), [Gunicorn on PyPI](https://pypi.org/project/gunicorn/), and [django-axes 9 release notes](https://pypi.org/project/django-axes/9.0.0/).
- [pytest on PyPI](https://pypi.org/project/pytest/), [pytest-django on PyPI](https://pypi.org/project/pytest-django/), [factory_boy on PyPI](https://pypi.org/project/factory-boy/), [Ruff on PyPI](https://pypi.org/project/ruff/), [pip-audit on PyPI](https://pypi.org/project/pip-audit/), and [Bandit on PyPI](https://pypi.org/project/bandit/).
- [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/) and [Caddy image tags](https://hub.docker.com/_/caddy/tags).
- [GitHub Actions Python workflow guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
- [pip timeout and retry options](https://pip.pypa.io/en/stable/cli/pip/).

## Version pin verification rule

Never pin a version unless pip's configured package index confirms it exists. Record the date of the check in this file. Before committing requirements changes, run `pip install --dry-run -r requirements/base.txt` and `pip install --dry-run -r requirements/dev.txt` in the Python 3.12 project image so the resolver checks both exact releases and their dependency compatibility. Last checked: 2026-11-18.

## Remaining Day 1 verification

The package index check found `Django==5.2.20` did not resolve; it has been corrected to 5.2.19. The exact `pip install --dry-run` results for both requirement sets are recorded in `PROGRESS.md`. This validates dependency resolution, not application build, generated migrations, app tests, local smoke test, CI, or `check --deploy`.
