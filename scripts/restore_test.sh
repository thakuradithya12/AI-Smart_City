#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 2 || ! -f "$1" || ! -f "$2" ]]; then
  echo "Usage: scripts/restore_test.sh /path/to/db.dump /path/to/media.tar.gz" >&2
  exit 2
fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env ]] || { echo "Missing .env." >&2; exit 2; }
set -a
source .env
set +a
: "${APP_IMAGE:?Set APP_IMAGE in .env to an image containing the app runtime}"
db_backup="$(realpath "$1")"
media_backup="$(realpath "$2")"
container="ai-smart-city-restore-test-$$"
volume="ai-smart-city-restore-media-$$"
password="$(openssl rand -hex 24)"
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Isolate the restore in a disposable PostGIS container with no published ports or persistent database volume.
docker run -d --name "$container" \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=1g \
  -e POSTGRES_USER=restoretest -e POSTGRES_PASSWORD="$password" -e POSTGRES_DB=postgres \
  postgis/postgis:17-3.7 >/dev/null
ready=0
for attempt in $(seq 1 30); do
  if docker exec "$container" pg_isready -U restoretest -d postgres >/dev/null 2>&1; then ready=1; break; fi
  sleep 2
done
[[ "$ready" == 1 ]] || { echo "Disposable PostGIS did not become ready." >&2; exit 1; }
docker exec "$container" createdb -U restoretest ai_smart_city_restore
docker exec -i "$container" pg_restore -U restoretest --no-owner --no-acl \
  -d ai_smart_city_restore < "$db_backup"
docker exec "$container" psql -U restoretest -d ai_smart_city_restore -v ON_ERROR_STOP=1 -c \
  "SELECT current_database() AS database, (SELECT count(*) FROM django_migrations) AS migrations, (SELECT count(*) FROM accounts_user) AS users, (SELECT count(*) FROM complaints_complaint) AS complaints;"

docker volume create "$volume" >/dev/null
docker run --rm --mount "source=$volume,target=/restore" \
  --mount "type=bind,source=$media_backup,target=/tmp/media.tar.gz,readonly" \
  "$APP_IMAGE" python -c \
  'import pathlib,tarfile; root=pathlib.Path("/restore"); tf=tarfile.open("/tmp/media.tar.gz", "r:gz"); members=tf.getmembers(); tf.extractall(root, filter="data"); print(f"Media restore extracted {sum(m.isfile() for m in members)} files into disposable volume")'
echo "Restore smoke check passed. The disposable database and media volume will now be removed."
