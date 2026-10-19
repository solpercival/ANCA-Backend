#!/bin/bash
# Join the tailnet without an auth key (run by `make funnel-login`). The compose
# tailscale container gives an interactive login only 60 s and then restarts with a new
# URL, so this runs a one-off container on the same state volume that waits 15 min.
# Afterwards the identity is saved, and `make funnel` starts without a key.
set -eu
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

docker compose -f docker-compose.yml -f docker-compose.funnel.yml stop tailscale >/dev/null 2>&1 || true
docker rm -f ts-login >/dev/null 2>&1 || true
docker run -d --name ts-login -v anca-backend_tailscale-state:/var/lib/tailscale \
  tailscale/tailscale:v1.104.1 sh -c "
    tailscaled --statedir=/var/lib/tailscale --tun=userspace-networking >/dev/null 2>&1 &
    sleep 3
    tailscale up --hostname=${TS_HOSTNAME:-anca-api} --advertise-tags=tag:anca-api --reset --timeout=15m
    echo UP_EXIT=\$?
    sleep infinity" >/dev/null
trap 'docker rm -f ts-login >/dev/null 2>&1' EXIT

until docker logs ts-login 2>&1 | grep -qE "login\.tailscale\.com/a/|UP_EXIT"; do sleep 1; done
url=$(docker logs ts-login 2>&1 | grep -oE "https://login\.tailscale\.com/a/[A-Za-z0-9]+" | tail -1)
if [ -n "$url" ]; then
  echo "Open this URL on any device signed in to the tailnet and approve the machine:"
  echo "  $url"
  echo "(valid for 15 minutes; waiting...)"
fi
until docker logs ts-login 2>&1 | grep -q UP_EXIT; do sleep 3; done
if docker logs ts-login 2>&1 | grep -q "UP_EXIT=0"; then
  echo "Joined the tailnet. Now run: make funnel"
else
  echo "Login did not complete:"; docker logs ts-login 2>&1 | tail -5; exit 1
fi
