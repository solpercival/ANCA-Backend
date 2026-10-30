#!/bin/bash
# Tailscale Funnel deployment (docker-compose.funnel.yml), run by `make funnel`.
#   scripts/funnel_check.sh preflight   # refuse to go public on unsafe settings
#   scripts/funnel_check.sh             # check the public URL once the stack is up
# Prints PASS / FAIL / SKIP per check and exits non-zero if any check failed.
set -u
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

failed=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; failed=1; }
skip() { echo "SKIP  $1"; }

# --- preflight: the API is about to be reachable by anyone with the URL ------------
if [ "${1:-}" = "preflight" ]; then
  if [ -n "${TS_AUTHKEY:-}" ]; then
    pass "TS_AUTHKEY is set"
  else
    skip "no TS_AUTHKEY: on its first start the container prints a login URL to approve"
  fi
  # APP_ENV other than local makes the orchestrator refuse to start on a placeholder
  # JWT_SECRET or POSTGRES_PASSWORD, or on ALLOWED_HOSTS=*
  if [ "${APP_ENV:-local}" = local ]; then
    fail "APP_ENV is local: set APP_ENV=production so the startup secret checks run"
  else
    pass "APP_ENV=$APP_ENV"
  fi
  secret=${JWT_SECRET:-}
  if [ "${#secret}" -lt 32 ] || [ "$secret" = change-me-in-prod ]; then
    fail "JWT_SECRET is a placeholder or under 32 characters: anyone could sign tokens"
  else
    pass "JWT_SECRET is at least 32 characters"
  fi
  case "${POSTGRES_PASSWORD:-}" in
    ""|rag|change_in_prod) fail "POSTGRES_PASSWORD is a placeholder (see the README to change it)" ;;
    *) pass "POSTGRES_PASSWORD is not a placeholder" ;;
  esac
  if echo "${ALLOWED_HOSTS:-}" | grep -q '\*' || [ -z "${ALLOWED_HOSTS:-}" ]; then
    fail "ALLOWED_HOSTS must list the funnel hostname and localhost (the health check)"
  elif ! echo "$ALLOWED_HOSTS" | grep -q '"localhost"'; then
    fail "ALLOWED_HOSTS has no \"localhost\": the container health check would fail"
  else
    pass "ALLOWED_HOSTS=$ALLOWED_HOSTS"
  fi
  if echo "${CORS_ALLOW_ORIGINS:-}" | grep -q 'https://'; then
    pass "CORS_ALLOW_ORIGINS has an https origin"
  else
    skip "CORS_ALLOW_ORIGINS has no https:// origin yet (needed for login from the Vercel app)"
  fi
  exit $failed
fi

# --- checks against the running stack ------------------------------------------------
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.funnel.yml"
API_PREFIX=$(.venv/bin/python -c 'from rag_engine.config import API_PREFIX; print(API_PREFIX)')

# the Tailscale container's name on the tailnet, once it has logged in
host=""
for _ in $(seq 1 60); do
  host=$($COMPOSE exec -T tailscale tailscale status --json 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)
  [ -n "$host" ] && break
  sleep 2
done
if [ -z "$host" ]; then
  url=$($COMPOSE logs tailscale 2>/dev/null | grep -oE 'https://login\.tailscale\.com/a/[A-Za-z0-9]+' | tail -1)
  if [ -n "$url" ]; then
    echo "WAIT  the tailscale container has not joined the tailnet. Run make funnel-login,"
    echo "      approve the machine at the URL it prints, then run make funnel again"
  else
    echo "FAIL  the tailscale container did not join the tailnet; see: $COMPOSE logs tailscale"
  fi
  exit 1
fi
BASE="https://$host$API_PREFIX"
echo "      public URL: https://$host  (API base $BASE)"

funnel_on=""
for _ in $(seq 1 15); do  # the serve config is applied a few seconds after login
  $COMPOSE exec -T tailscale tailscale funnel status 2>/dev/null | grep -qi "funnel on" && funnel_on=1 && break
  sleep 2
done
if [ -n "$funnel_on" ]; then
  pass "Funnel is on for $host"
else
  fail "Funnel is not on: allow it for tag:anca-api in the admin console (README)"
fi

# 1. public HTTPS; the first call can wait for the certificate and DNS
code=""
for _ in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -D /tmp/funnel_h1 "$BASE/health")
  [ "$code" = 200 ] && break
  sleep 3
done
if [ "$code" = 200 ]; then
  pass "GET $BASE/health -> 200"
else
  fail "GET $BASE/health -> $code"
fi
if grep -qi "^strict-transport-security:" /tmp/funnel_h1 2>/dev/null; then
  pass "HSTS sent (the orchestrator sees the request as https)"
else
  fail "no HSTS header: X-Forwarded-Proto from the tailscale container is not trusted"
fi

# 2. the orchestrator logs the real client, not the Tailscale container
since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -s -o /dev/null "$BASE/health?ip-check=1"
sleep 1
line=$($COMPOSE logs --since "$since" orchestrator 2>/dev/null | grep "ip-check=1" | tail -1)
if [ -z "$line" ]; then
  skip "client IP: no access-log line for the request"
elif echo "$line" | grep -q "172.31.251.10:"; then
  fail "orchestrator sees the tailscale container as the client: $line"
else
  pass "orchestrator sees the client: $(echo "$line" | grep -oE '[0-9a-f.:]+:[0-9]+ -' | head -1)"
fi

# 3. /resolve without a login, as the front end calls it for operators
code=$(curl -s -o /tmp/funnel_resolve.json -w '%{http_code}' -m 120 -X POST "$BASE/resolve" \
  -H 'Content-Type: application/json' -d '{"code": "am.fb.0002"}')
if [ "${ALLOW_ANONYMOUS_OPERATOR:-false}" = true ]; then
  if [ "$code" = 200 ] && grep -q '"tier":"operator"' /tmp/funnel_resolve.json; then
    pass "POST /resolve with no token -> 200 as an operator"
  else
    fail "POST /resolve with no token -> $code (ALLOW_ANONYMOUS_OPERATOR=true)"
  fi
elif [ "$code" = 401 ]; then
  pass "POST /resolve with no token -> 401 (ALLOW_ANONYMOUS_OPERATOR is off)"
else
  fail "POST /resolve with no token -> $code, expected 401 with ALLOW_ANONYMOUS_OPERATOR off"
fi

# 4. a caller on the published port cannot pretend to come through the Funnel
direct=$(curl -s -D - -o /dev/null -H "X-Forwarded-Proto: https" "http://localhost:8080$API_PREFIX/health")
if echo "$direct" | grep -qi "^strict-transport-security:"; then
  fail "X-Forwarded-Proto from a direct caller on :8080 is trusted"
else
  pass "X-Forwarded-Proto from a direct caller on :8080 is ignored"
fi

# 5. only the configured host names are accepted
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: evil.example" "http://localhost:8080$API_PREFIX/health")
[ "$code" = 400 ] && pass "Host: evil.example -> 400" || fail "Host: evil.example -> $code, expected 400"

# 6. on a GPU machine, the model containers have the GPU (a plain `docker compose up`
#    without docker-compose.gpu.yml silently runs them on the CPU: 20+ s per answer)
if command -v nvidia-smi >/dev/null 2>&1; then
  for svc in ollama orchestrator; do
    gpu=$(docker inspect "$($COMPOSE ps -q "$svc")" --format '{{json .HostConfig.DeviceRequests}}' 2>/dev/null)
    if [ -n "$gpu" ] && [ "$gpu" != null ]; then
      pass "$svc has the GPU"
    else
      fail "$svc runs without the GPU: start the stack with make (make funnel), not plain docker compose"
    fi
  done
else
  skip "no nvidia-smi: GPU check skipped"
fi

exit $failed
