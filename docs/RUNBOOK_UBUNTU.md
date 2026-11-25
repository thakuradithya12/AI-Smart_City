# Fresh Ubuntu VM runbook

This runbook prepares a single Ubuntu 24.04 LTS VM. **D1 (server and public domain): owner to supply.** This document does not provision a server, choose a domain, or invent pilot coordinates. Replace every `<...>` placeholder with values supplied by the owner. Do not run public deployment until the domain resolves to the VM, ports 80/443 reach it, and the owner has provided authoritative pilot ward data.

## Server prerequisites

- Ubuntu 24.04 LTS on an `amd64` VM, with a sudo-capable operator account and SSH key access.
- A public DNS name and VM supplied by the owner; inbound TCP 22, 80 and 443; outbound HTTPS for package/image downloads and Caddy certificate issuance.
- Enough disk for the application, PostGIS volume, private uploads, and retained encrypted backups. Monitor free space before each deployment.
- Keep database and media backups outside the VM on an encrypted, access-restricted destination. Do not store `.env`, backup archives, media, or credentials in Git.

## 1. Install Docker Engine and Compose

Run on the VM as a sudo-capable user. These commands use Docker's official Ubuntu apt repository.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git openssl ufw
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run --rm hello-world
sudo docker compose version
```

Lock inbound traffic to SSH, HTTP and HTTPS. Keep SSH key authentication enabled and disable password authentication in `sshd_config` before relying on this host.

Confirm key login works in a second terminal before closing the current SSH session:

```bash
printf 'PasswordAuthentication no\nPermitRootLogin no\n' | sudo tee /etc/ssh/sshd_config.d/60-ai-smart-city.conf
sudo sshd -t
sudo systemctl reload ssh
```

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 2. Clone the repository

```bash
sudo mkdir -p /opt/ai-smart-city
sudo chown "$USER":"$USER" /opt/ai-smart-city
git clone <YOUR_GIT_CLONE_URL> /opt/ai-smart-city
cd /opt/ai-smart-city
```

Use a Git credential helper or a read-only deploy key. Never put a Git token in the clone URL.

## 3. Create the production environment file

```bash
cd /opt/ai-smart-city
cp .env.example .env
chmod 600 .env
openssl rand -base64 48
openssl rand -hex 32
nano .env
```

In the editor, set these entries to real values (do not paste secrets into chat or commit `.env`). The values shown in `.env.example` are development placeholders, not production credentials:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<first-random-output>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-domain>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-domain>
DOMAIN=<your-domain>
APP_IMAGE=ai-smart-city:initial
APP_IMAGE_PREVIOUS=
BACKUP_DIR=/var/backups/ai-smart-city
REPORT_POST_LIMIT=5
REPORT_POST_WINDOW_SECONDS=3600
POSTGRES_DB=smart_city
POSTGRES_USER=smart_city
POSTGRES_PASSWORD=<second-random-output>
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

The complete environment-variable inventory is in `.env.example`; keep it as the template and maintain the real values only in the permission-restricted `.env`. Configure variables by group:

- Django: `DJANGO_SETTINGS_MODULE`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_LOG_LEVEL`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `CSP_REPORT_ONLY`.
- Email and site links: `DJANGO_EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL`, `SITE_BASE_URL`.
- Notifications and scheduler: `NOTIFICATION_BATCH_SIZE`, `NOTIFICATION_MAX_ATTEMPTS`, `SCHEDULER_POLL_SECONDS`, `SCHEDULER_HEARTBEAT_STALE_SECONDS`, `CITIZEN_REMINDER_DAYS`.
- Host/image/backup: `DOMAIN`, `APP_IMAGE`, `APP_IMAGE_PREVIOUS`, `BACKUP_DIR`.
- Request/media/UI limits: `REPORT_POST_LIMIT`, `REPORT_POST_WINDOW_SECONDS`, `REPORT_MAX_PHOTOS`, `EVIDENCE_DISPLAY_MAX_EDGE`, `LIST_PAGE_SIZE`, `MAP_TILE_URL`.
- Privacy retention: `COMPLAINT_RETENTION_DAYS`, `CLOSED_PHOTO_RETENTION_DAYS`, `REJECTED_CANCELLED_RETENTION_DAYS`, `INACTIVE_ACCOUNT_RETENTION_DAYS`, `DELETION_REQUEST_DAYS`, `PRIVACY_NOTICE_VERSION`.
- Database: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.

Production Compose overrides `DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG` and `POSTGRES_HOST` for the web and scheduler containers. The secret key, database password, allowed hosts, CSRF origins, domain, image tags and backup path must be set for this deployment. Email credentials are needed only if production email delivery is configured.

Set DNS `A`/`AAAA` records to the VM first. Caddy obtains certificates automatically when the configured hostname points to this server and the public HTTP/HTTPS ports are reachable. Store backups on a restricted, encrypted disk or copy them to an encrypted restricted-access destination.

The current official `postgis/postgis:17-3.7` tag is published on Debian Trixie. Before using a refreshed database image with any existing Postgres volume, check the exact old and new image digests and follow the PostGIS maintainers' dump-and-restore guidance across OS/base-image changes; never assume a mutable tag points to the same database binary build.

This image tag currently supports `amd64` only; use an Ubuntu VM with an `x86_64`/`amd64` architecture.

## 4. Build and start the first production release

```bash
cd /opt/ai-smart-city
docker build --pull -t ai-smart-city:initial .
docker compose --env-file .env -f docker-compose.prod.yml up -d db
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps web python manage.py check --deploy
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps web python manage.py migrate --noinput
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps web python manage.py createcachetable
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps web python manage.py createsuperuser
docker compose --env-file .env -f docker-compose.prod.yml up -d web caddy
docker compose --env-file .env -f docker-compose.prod.yml up -d scheduler
docker compose --env-file .env -f docker-compose.prod.yml ps
curl --fail --show-error --head https://<your-domain>/accounts/login/
```

Do not create the first admin password as a shared/demo password. Change the login secret and Postgres password if they were ever exposed. The first browser HTTPS request causes Django to emit the initial short HSTS duration (300 seconds); only increase it after confirming stable HTTPS.

The Compose `scheduler` service runs `manage.py run_scheduler`. It invokes `purge_expired` hourly under PostgreSQL advisory locking, alongside the other scheduled maintenance commands. Confirm it stays running with `docker compose --env-file .env -f docker-compose.prod.yml ps` and review its logs with `docker compose --env-file .env -f docker-compose.prod.yml logs --since=1d scheduler`. Do not add a second cron entry for `purge_expired` unless the scheduler service is deliberately disabled.

### Demo data

For a disposable local development database only, start the development Compose services and run:

```bash
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_demo
```

`seed_demo` refuses to run with production `DEBUG=False` unless forced. Do not pass `--force` in production. It prints newly generated passwords once; capture them securely for the rehearsal and rotate/delete the demo accounts afterwards. The command creates a synthetic Hyderabad ward, not pilot geography. See `docs/DEMO_SCRIPT.md` for the rehearsal accounts and login details.

## 5. Deploy an update and roll back

Fetch and review the intended revision, then deploy. `deploy.sh` saves a backup, builds an image tagged with the revision, runs `check --deploy`, applies migrations and the cache table, starts the candidate on loopback port 18001, verifies its health, and only then switches the `web` service. It restores the previously active image if the switched web health check fails. Database migrations are not automatically reversed; use the backup restore procedure if a migration is incompatible with the previous image.

```bash
cd /opt/ai-smart-city
git fetch origin
git checkout <reviewed-branch-or-commit>
git pull --ff-only
scripts/deploy.sh
```

For an operator-initiated image rollback after a successful deploy:

```bash
cd /opt/ai-smart-city
set -a; source .env; set +a
test -n "$APP_IMAGE_PREVIOUS"
old_image="$APP_IMAGE"
sed -i "s|^APP_IMAGE=.*|APP_IMAGE=$APP_IMAGE_PREVIOUS|" .env
sed -i "s|^APP_IMAGE_PREVIOUS=.*|APP_IMAGE_PREVIOUS=$old_image|" .env
docker compose --env-file .env -f docker-compose.prod.yml up -d --no-deps web
curl --fail --show-error --head "https://$DOMAIN/accounts/login/"
```

## 6. Back up

The backup files are created with owner-only permissions under `BACKUP_DIR`. Copy them to an encrypted, restricted-access off-server destination and retain checksums.

```bash
cd /opt/ai-smart-city
sudo mkdir -p /var/backups/ai-smart-city
sudo chown "$USER":"$USER" /var/backups/ai-smart-city
chmod 700 /var/backups/ai-smart-city
scripts/backup.sh
ls -lh /var/backups/ai-smart-city
```

Schedule `scripts/backup.sh` with a systemd timer or cron after checking disk capacity and retention. Do not add backup files to Git.

## 7. Test a restore in disposable containers

This command reads the selected database dump and media archive, restores the database into an isolated temporary PostGIS container, extracts media to a disposable Docker volume, prints row counts, then removes both temporary resources. It does not replace production data.

```bash
cd /opt/ai-smart-city
set -o pipefail
scripts/restore_test.sh /var/backups/ai-smart-city/<db-backup>.dump /var/backups/ai-smart-city/<media-backup>.tar.gz 2>&1 | tee docs/restore-test-<date>.log
```

Inspect the saved log and checksum manifest. Run the restore test after the first real backup and retain its output in `docs/`.

For an actual disaster recovery, first stop writes and restore into a new/clean PostGIS database using `pg_restore`, then restore the media archive into the application's private media volume. Confirm the migration, user and complaint counts and check the application before directing Caddy traffic to it. The script above is a disposable restore rehearsal and intentionally destroys its temporary database and volume; it does not overwrite production data.

## Production-like local deployment check

The repo owner has not supplied a server or domain, so the live deployment gate remains blocked. With Docker Desktop running, this command runs Django's production security checks in the local Compose app container without starting a remote service:

```powershell
docker compose run --rm `
  -e DJANGO_SETTINGS_MODULE=config.settings.prod `
  -e DJANGO_SECRET_KEY='local-check-only-key-6f5d0d8c7f2e4b1b9a1f8e6a4d7c2b9a0f3e1d5c8b7a6f4e2d1c0b9a8f7e6d5c' `
  -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1' `
  -e DJANGO_CSRF_TRUSTED_ORIGINS='https://localhost' `
  web python manage.py check --deploy
```

The check may report the expected HSTS warnings because the deliberately short 300-second duration is not configured with subdomain/preload coverage. Do not suppress those warnings or enable preload/subdomains without a stable domain and owner review.
