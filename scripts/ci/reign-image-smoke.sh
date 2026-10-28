#!/usr/bin/env bash
# Rook-authored. Start a Reign image the way Rook's servers run it (reign-deploy per-user:
# `dashboard` on 9119 behind a basic-auth login, Reign home on a volume) and check it serves.
#
#   scripts/ci/reign-image-smoke.sh <image>
#
# Passes when /api/health answers ok with auth required, the web portal loads, and an
# unauthenticated API call is refused. Prints the container log on failure.
set -euo pipefail

image="${1:?usage: reign-image-smoke.sh <image>}"
name="reign-smoke-$$"
port="${REIGN_SMOKE_PORT:-19119}"
home="$(mktemp -d)"; chmod 777 "$home"   # the container runs as 10000:10000
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; sudo rm -rf "$home" 2>/dev/null || rm -rf "$home"; }
trap cleanup EXIT
fail() { echo "::error::$*"; echo "--- container log ---"; docker logs "$name" 2>&1 | tail -80; exit 1; }

hash="$(docker run --rm --entrypoint /opt/reign/.venv/bin/python -w /opt/reign "$image" -c \
  'from plugins.dashboard_auth.basic import hash_password; print(hash_password("smoke-test"))')"

docker run -d --name "$name" \
  -e REIGN_UID=10000 -e REIGN_GID=10000 \
  -e REIGN_DASHBOARD_BASIC_AUTH_USERNAME=smoke \
  -e REIGN_DASHBOARD_BASIC_AUTH_PASSWORD_HASH="$hash" \
  -e REIGN_DASHBOARD_BASIC_AUTH_SECRET="$(openssl rand -hex 32)" \
  -v "$home:/opt/data" \
  -p "127.0.0.1:$port:9119" \
  "$image" dashboard --host 0.0.0.0 --port 9119 --no-open >/dev/null

health=""
for _ in $(seq 1 90); do
  [ "$(docker inspect -f '{{.State.Running}}' "$name")" = true ] || fail "container exited"
  if health="$(curl -fsS "http://127.0.0.1:$port/api/health" 2>/dev/null)"; then break; fi
  health=""; sleep 2
done
[ -n "$health" ] || fail "/api/health did not answer within 180s"
echo "health: $health"
echo "$health" | grep -q '"ok": *true' || fail "/api/health is not ok"
echo "$health" | grep -q '"auth_required": *true' || fail "dashboard is running without a login"

code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/")"
case "$code" in 200|302|303|307) ;; *) fail "web portal answered HTTP $code" ;; esac

code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/api/sessions?limit=1")"
case "$code" in 401|403) ;; *) fail "unauthenticated /api/sessions answered HTTP $code (want 401)" ;; esac

echo "smoke test passed: $image"
