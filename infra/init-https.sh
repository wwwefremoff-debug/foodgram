#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Create infra/.env first"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${DOMAIN:?Set DOMAIN in infra/.env, e.g. foodgram-name.duckdns.org}"
: "${CERTBOT_EMAIL:?Set CERTBOT_EMAIL in infra/.env}"

mkdir -p certbot/conf certbot/www

render() {
  local src=$1
  local dst=$2
  sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "$src" > "$dst"
}

echo "==> HTTP config for ACME (${DOMAIN})"
render nginx/nginx.http.conf.template nginx.conf
docker compose up -d --build
docker compose restart nginx
sleep 3

echo "==> Request Let's Encrypt certificate"
docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  -d "${DOMAIN}"

echo "==> Switch nginx to HTTPS"
render nginx/nginx.https.conf.template nginx.conf
docker compose up -d --force-recreate nginx

echo "Ready: https://${DOMAIN}/"
