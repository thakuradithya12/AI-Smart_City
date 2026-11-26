# Free demo deployment: Render web + Neon PostGIS

This is a short-lived demo setup, not a production launch. **D1 (Render account, Neon project, and service URL): owner to supply.** Do not publish real complaints or personal photos on this setup: Render free web services have an ephemeral filesystem, so uploaded evidence can disappear on restart, redeploy, or sleep. The seeded illustrations can be restored from this repository; citizen-uploaded files cannot.

No `render.yaml` is included. The owner can create the services through the Render and Neon dashboards, and there is no need to maintain a second deployment configuration until those account settings are known. Render's official Docker documentation covers connecting a repository, selecting Docker, and setting a start command in the dashboard: [Docker on Render](https://render.com/docs/docker) and [Web Services](https://render.com/docs/web-services).

## 1. Create the Neon database

1. In the Neon dashboard, create a PostgreSQL project. Choose a region close to the Render service region; the owner supplies that choice.
2. Open the project's SQL Editor and enable PostGIS:

   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

   Neon documents that PostGIS can be enabled with this statement: [Neon's PostGIS extension guide](https://neon.com/docs/extensions/postgis). The first Django geography migration also runs the same idempotent statement before creating geometry columns. If the migration role lacks permission, it exits with an actionable error. Wait for the owner's Neon permission check before relying on this deployment.
3. In the Neon connection details, copy the connection URI for the target database. Keep it private. Use the SSL-enabled URI (`sslmode=require`) and enter it only in Render's secret environment-variable UI.

Neon is separate from the Render service, so a Render restart does not clear the database or Django's `django_migrations` table. Do not manually delete or reset `django_migrations`: the rest of the schema migrations are not replay-safe, so that action is a deployment blocker. The initial extension operation and schema migration are atomic; an interrupted migration rolls back its schema work and migration record together.

## 2. Create the Render web service

1. In Render, choose **New → Web Service**, connect the repository, and select branch `phase1` after reviewing its current head. Select **Docker** as the runtime and the **Free** instance plan.
2. Use the repository root as the service root. Leave the Dockerfile/build command at its detected defaults.
3. Set the start command to:

   ```sh
   sh scripts/start_render.sh
   ```

   This command runs `migrate --noinput`, ensures the six standard report categories exist, runs `collectstatic --noinput`, optionally creates demo accounts and sample complaints only when `DEMO_SEED=1`, then starts Gunicorn. It binds to Render's `PORT`, defaulting to 10000. The process defaults are one worker (`WEB_CONCURRENCY`) and two threads (`GUNICORN_THREADS`).
4. Set the health check path to `/healthz/`. The route is public and tests database connectivity without returning complaint data.
5. Add environment variables in the Render service's **Environment** page. Names and purposes only:

   | Name | Purpose |
   |---|---|
   | `DATABASE_URL` | Neon PostgreSQL URI, including its SSL requirement |
   | `SECRET_KEY` | Django signing secret |
   | `DEBUG` | Set production debug behavior to off (`0`) |
   | `ALLOWED_HOSTS` | Render-assigned host name |
   | `CSRF_TRUSTED_ORIGINS` | HTTPS origin for the Render-assigned host |
   | `DEMO_SEED` | Leave off by default; standard report categories are initialized regardless; set to `1` only for an intentional demo seed |
   | `WEB_CONCURRENCY` | Gunicorn worker count; default `1` for the 512 MB free instance |
   | `GUNICORN_THREADS` | Gunicorn thread count; default `2` |
   | `PORT` | Render-provided web-service port; do not hard-code a different port |
   | `MAP_TILE_URL` | Optional tile endpoint; default is OSM's canonical demo endpoint |
   | `DJANGO_LOG_LEVEL` | Optional application log level |
   | `EMAIL_HOST` | SMTP host, if a compatible external mail provider is configured later |
   | `EMAIL_PORT` | SMTP port, if a compatible external mail provider is configured later |
   | `EMAIL_HOST_USER` | SMTP account name, if configured |
   | `EMAIL_HOST_PASSWORD` | SMTP credential, if configured |
   | `EMAIL_USE_TLS` | SMTP TLS setting, if configured |
   | `EMAIL_USE_SSL` | SMTP SSL setting, if configured |
   | `DEFAULT_FROM_EMAIL` | Sender address, if email delivery is configured |

   Set secret values only in Render's environment interface. Do not commit them, put them in `render.yaml`, or include them in screenshots or logs. `DATABASE_URL` takes precedence over the Compose-style `POSTGRES_*` variables. `SECRET_KEY`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` take precedence over the legacy `DJANGO_*` aliases.
6. Save and deploy. Inspect the deploy logs for successful PostGIS setup, migrations and static collection. Open `/healthz/`; then open the service URL and check the login page.
7. Keep `DEMO_SEED=0` until the owner has confirmed Neon extension permissions and chosen to expose demo accounts. Standard report categories are initialized without demo accounts, reports, departments, or ward geometry. If enabling the full demo seed, set `DEMO_SEED=1` and redeploy. It creates synthetic demo accounts, two sample complaints and repository-created illustration images. It prints newly created random passwords in the deploy log; capture them securely and rotate/disable the accounts after the demo. The phone numbers are synthetic login identifiers, not verified or contactable numbers.

Render's free plan spins down a web service after 15 minutes without inbound requests and may take about a minute to wake. Its filesystem is ephemeral and free instances can restart at any time. Free instances do not support persistent disks or background workers; free Postgres services on Render are not used here. See [Render's free instance limits](https://render.com/docs/free). This deployment therefore does not run the application scheduler: reminders, notification delivery, SLA jobs and automatic `purge_expired` scheduling are not available on the free demo. Render free also blocks outbound SMTP ports 25, 465 and 587; email delivery is not part of this demo. In local development, email uses Django's console backend.

## 3. Warm the site before a demo

1. Open the Render service URL 2–3 minutes before the walkthrough, especially if it has been idle for 15 minutes.
2. Wait for the Render loading page to finish. Open `/healthz/`, then the login page, and sign in to verify the database and static assets are available.
3. Keep the walkthrough moving. A short demo fits inside the idle window; if the service sleeps, allow about a minute for the next request to wake it.
4. Keep seeded illustration evidence for the demo. Any real photo uploaded to the free service may be lost when the service sleeps, restarts or redeploys.

## 4. Move to a durable platform later

Before using real complaints, select a platform with durable private evidence storage, scheduled/background process support, backups and a restore path. Then:

1. Provision a managed PostGIS database with documented backups and verify the application's connection role can use PostGIS.
2. Move private evidence to durable private object storage or a persistent private disk; migrate existing evidence and test authorization on every evidence URL.
3. Run the scheduler as a separately monitored process or managed scheduled job so reminders and `purge_expired` execute reliably.
4. Configure a supported transactional email service if email notifications are required; do not assume the free Render SMTP path works.
5. Set production secrets and HTTPS host/origin values in the platform's secret manager, keep `DEBUG=0`, and set `DEMO_SEED=0`.
6. Take a backup, test a restore, run the production `check --deploy`, review the workflow, and rehearse rollback before receiving real data.
7. Remove or anonymise demo records and rotate their generated passwords. Do not transfer the synthetic ward as authoritative pilot geography.

## Verification status

This document is a browser checklist only. No Neon project, Render service, PostGIS privilege check, TLS endpoint, free-tier sleep/wake, or live database migration has been run. Deployment remains blocked on the owner's Neon extension/permission test and provisioned account/service inputs.
