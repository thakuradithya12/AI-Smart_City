#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env ]] || { echo "Missing .env." >&2; exit 2; }
set -a
source .env
set +a
: "${BACKUP_DIR:?Set BACKUP_DIR in .env}"
umask 077
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
db_tmp="$BACKUP_DIR/db-$stamp.dump.tmp"
media_tmp="$BACKUP_DIR/media-$stamp.tar.gz.tmp"
db_file="${db_tmp%.tmp}"
media_file="${media_tmp%.tmp}"
trap 'rm -f "$db_tmp" "$media_tmp"' EXIT

docker compose --env-file .env -f docker-compose.prod.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$db_tmp"
docker compose --env-file .env -f docker-compose.prod.yml exec -T web python -c \
  'import sys,tarfile; archive=tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz"); archive.add("/app/private_media", arcname="."); archive.close()' > "$media_tmp"
[[ -s "$db_tmp" && -s "$media_tmp" ]]
mv "$db_tmp" "$db_file"
mv "$media_tmp" "$media_file"
chmod 600 "$db_file" "$media_file"
sha256sum "$db_file" "$media_file" > "$BACKUP_DIR/sha256-$stamp.txt"
chmod 600 "$BACKUP_DIR/sha256-$stamp.txt"
trap - EXIT
printf 'Database backup: %s\nMedia backup: %s\nChecksums: %s\n' \
  "$db_file" "$media_file" "$BACKUP_DIR/sha256-$stamp.txt"
