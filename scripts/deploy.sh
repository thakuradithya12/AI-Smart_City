#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env ]] || { echo "Missing .env; copy .env.example and configure it first." >&2; exit 2; }

# .env is an operator-maintained deployment file; never print it because it contains secrets.
set -a
source .env
set +a
: "${DOMAIN:?Set DOMAIN in .env}"
: "${APP_IMAGE:?Set APP_IMAGE in .env to the currently active image}"
: "${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}"
previous_image="$APP_IMAGE"
previous_previous_image="${APP_IMAGE_PREVIOUS:-}"
candidate_image="ai-smart-city:$(git rev-parse --short HEAD)-$(date -u +%Y%m%d%H%M%S)"
export CANDIDATE_IMAGE="$candidate_image"
compose=(docker compose --env-file .env -f docker-compose.prod.yml)
switched=0

write_images() {
  local value="$1" prior="$2" tmp
  tmp="$(mktemp .env.XXXXXX)"
  awk -v image="$value" -v old="$prior" 'BEGIN { current=0; previous=0 } /^APP_IMAGE=/ { print "APP_IMAGE=" image; current=1; next } /^APP_IMAGE_PREVIOUS=/ { print "APP_IMAGE_PREVIOUS=" old; previous=1; next } { print } END { if (!current || !previous) exit 3 }' .env > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" .env
  APP_IMAGE="$value"
  APP_IMAGE_PREVIOUS="$prior"
  export APP_IMAGE APP_IMAGE_PREVIOUS
}

rollback() {
  local status=$?
  if (( switched )); then
    echo "Deployment health check failed; restoring previous image: $previous_image" >&2
    write_images "$previous_image" "$previous_previous_image"
    "${compose[@]}" up -d --no-deps web || true
  fi
  CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy rm -sf candidate >/dev/null 2>&1 || true
  exit "$status"
}
trap rollback ERR
trap 'CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy rm -sf candidate >/dev/null 2>&1 || true' EXIT

docker build --pull -t "$candidate_image" .
"${compose[@]}" up -d db
"${compose[@]}" exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
scripts/backup.sh

# Run deployment checks and schema updates on the candidate before it receives live traffic.
CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy run --rm --no-deps candidate python manage.py check --deploy
CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy run --rm --no-deps candidate python manage.py migrate --noinput
CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy run --rm --no-deps candidate python manage.py createcachetable
CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy up -d --no-deps candidate

candidate_id="$(CANDIDATE_IMAGE="$candidate_image" "${compose[@]}" --profile deploy ps -q candidate)"
for attempt in $(seq 1 30); do
  state="$(docker inspect -f '{{.State.Health.Status}}' "$candidate_id" 2>/dev/null || true)"
  if [[ "$state" == healthy ]] && curl --fail --silent --show-error \
      -H "Host: $DOMAIN" -H 'X-Forwarded-Proto: https' \
      http://127.0.0.1:18001/accounts/login/ >/dev/null; then
    break
  fi
  if [[ "$state" == unhealthy ]]; then
    echo "Candidate container became unhealthy." >&2
    false
  fi
  sleep 4
done
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$candidate_id")" == healthy ]] || {
  echo "Candidate did not become healthy within 120 seconds." >&2
  false
}

# Only change APP_IMAGE after the new image passes its isolated candidate health check.
write_images "$candidate_image" "$previous_image"
switched=1
"${compose[@]}" up -d --no-deps web
for attempt in $(seq 1 30); do
  web_id="$("${compose[@]}" ps -q web)"
  [[ -n "$web_id" ]] && [[ "$(docker inspect -f '{{.State.Health.Status}}' "$web_id" 2>/dev/null || true)" == healthy ]] && break
  sleep 4
done
web_id="$("${compose[@]}" ps -q web)"
[[ -n "$web_id" && "$(docker inspect -f '{{.State.Health.Status}}' "$web_id")" == healthy ]]
curl --fail --silent --show-error "https://${DOMAIN}/accounts/login/" >/dev/null
switched=0
echo "Deployed $candidate_image; previous image retained for manual rollback."
