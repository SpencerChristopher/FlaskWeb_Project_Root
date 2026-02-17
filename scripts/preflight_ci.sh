#!/usr/bin/env bash
set -euo pipefail

run_act=0
if [[ "${1:-}" == "-RunAct" || "${1:-}" == "--run-act" ]]; then
  run_act=1
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required tool: $1"
    return 1
  fi
  return 0
}

echo "Preflight: GitHub Actions workflow lint"
if require_cmd actionlint; then
  actionlint -color -format '{{.Filepath}}:{{.Line}}:{{.Column}}: {{.Message}}' .github/workflows/*.yml
else
  echo "Install actionlint via your package manager or from its release page, then re-run."
fi

if [[ "$run_act" -eq 1 ]]; then
  echo "Preflight: Local workflow run (act)"
  if require_cmd act; then
    act -W .github/workflows/test-deploy.yml
  else
    echo "Install act to run workflows locally, then re-run with -RunAct."
  fi
fi
