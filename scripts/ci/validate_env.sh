#!/usr/bin/env bash
set -euo pipefail

required_file="${1:-}"
if [ -z "$required_file" ] || [ ! -f "$required_file" ]; then
  echo "::error::Required env list not found: ${required_file:-<missing>}"
  exit 1
fi

missing=0
while IFS= read -r raw_line || [ -n "$raw_line" ]; do
  line="${raw_line%%#*}"
  key="$(echo "$line" | xargs)"
  if [ -z "$key" ]; then
    continue
  fi
  if [ -z "${!key:-}" ]; then
    echo "::error::Missing required environment variable: $key"
    missing=1
  fi
done < "$required_file"

if [ "$missing" -ne 0 ]; then
  echo "--- Environment Validation Failed ---"
  echo "Ensure required vars/secrets are set for this workflow."
  exit 1
fi

echo "Environment Validated Successfully."
