#!/usr/bin/env bash
# Bootstrap a Let's Encrypt cert for ${DOMAIN} via the webroot challenge.
#
# Idempotent: a real cert already in place → exits 0. Otherwise:
#   [1] place a dummy self-signed cert so nginx can boot
#   [2] start nginx (only nginx)
#   [3] validate the webroot pipeline against LE staging
#   [4] delete the staging lineage and the dummy
#   [5] issue the real production cert
#   [6] reload nginx and bring up the rest of the stack
#
# Reads DOMAIN, LE_EMAIL, COMPOSE_FILE from .env.

set -euo pipefail

cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
    echo "ERROR: .env missing — copy .env.example to .env and fill it in." >&2
    exit 1
fi
# shellcheck disable=SC1091
source .env

: "${COMPOSE_FILE:?COMPOSE_FILE not set in .env (e.g. docker-compose.yml:docker-compose.prod.yml)}"
: "${DOMAIN:?DOMAIN not set in .env}"
: "${LE_EMAIL:?LE_EMAIL not set in .env}"

LIVE_DIR="/etc/letsencrypt/live/${DOMAIN}"
DUMMY_MARKER="${LIVE_DIR}/.bootstrap-dummy"

if [ -f "${LIVE_DIR}/fullchain.pem" ] && [ ! -e "${DUMMY_MARKER}" ]; then
    echo "Real cert already at ${LIVE_DIR}; nothing to do."
    exit 0
fi

echo "==> [1/5] Place dummy self-signed cert so nginx can boot"
mkdir -p "${LIVE_DIR}"
openssl req -x509 -newkey rsa:2048 -days 1 -nodes \
    -keyout "${LIVE_DIR}/privkey.pem" \
    -out "${LIVE_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}" 2>/dev/null
touch "${DUMMY_MARKER}"

echo "==> [2/5] Start nginx (only nginx — backend/frontend stay down)"
docker compose up -d --no-deps nginx
sleep 3

echo "==> [3/5] Validate webroot pipeline against LE staging"
docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --staging \
    --cert-name "${DOMAIN}-staging" \
    --email "${LE_EMAIL}" \
    --agree-tos --no-eff-email \
    --non-interactive \
    -d "${DOMAIN}" -d "www.${DOMAIN}"

echo "==> [4/5] Delete staging lineage and dummy cert"
docker compose run --rm certbot delete \
    --cert-name "${DOMAIN}-staging" --non-interactive
rm -rf "/etc/letsencrypt/live/${DOMAIN}" \
       "/etc/letsencrypt/archive/${DOMAIN}" \
       "/etc/letsencrypt/renewal/${DOMAIN}.conf"

echo "==> [5/5] Issue real production cert"
docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email "${LE_EMAIL}" \
    --agree-tos --no-eff-email \
    --non-interactive \
    -d "${DOMAIN}" -d "www.${DOMAIN}"

echo "==> Reload nginx and bring up rest of stack"
docker compose exec -T nginx nginx -s reload
docker compose up -d

echo
echo "==> Done. Cert details:"
openssl x509 -in "${LIVE_DIR}/fullchain.pem" -noout -issuer -subject -dates
