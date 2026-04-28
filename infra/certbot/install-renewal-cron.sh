#!/usr/bin/env bash
# Install (idempotently) a daily cron job that renews the Let's Encrypt
# cert via the certbot service and reloads nginx if a new cert was
# written. Identified by a sentinel comment so re-runs replace the old
# line cleanly even if the project path changes.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="/var/log/mathingo-renewal.log"
SENTINEL="# mathingo:letsencrypt-renewal"

CRON_LINE="0 3 * * * cd ${PROJECT_DIR} && docker compose run --rm certbot renew --quiet && docker compose exec -T nginx nginx -s reload >> ${LOG_FILE} 2>&1 ${SENTINEL}"

current="$(crontab -l 2>/dev/null || true)"

if echo "${current}" | grep -qF "${SENTINEL}"; then
    echo "Renewal cron already present; replacing with fresh line for ${PROJECT_DIR}."
    new_crontab="$(echo "${current}" | grep -vF "${SENTINEL}")"
else
    echo "Installing renewal cron for ${PROJECT_DIR}."
    new_crontab="${current}"
fi

{
    [ -n "${new_crontab}" ] && echo "${new_crontab}"
    echo "${CRON_LINE}"
} | crontab -

echo
echo "Cron line:"
echo "  ${CRON_LINE}"
echo
echo "Log: ${LOG_FILE} (created on first run)"
