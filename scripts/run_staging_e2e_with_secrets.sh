#/usr/bin/env bash
set -euo pipefail

SECRETS_FILE=${1:-/etc/staging-secrets.env}

if [[ ! -f "$SECRETS_FILE" ]]; then
  echo "Secrets file $SECRETS_FILE is missing. Create it with the staging secrets (SECRET_KEY, ADMIN_*, MONGO_*, REDIS_PASSWORD, STAGING_TOKEN, CF_ACCESS_*)." >&2
  exit 1
fi

# Export everything from the secrets file into the environment for downstream commands.
set -a
source "$SECRETS_FILE"
set +a

exec sudo ./scripts/run_staging_e2e.sh
