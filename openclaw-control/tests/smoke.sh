#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/.."

docker compose config -q
bash openclaw-control/scripts/oc-audit
bash openclaw-control/scripts/oc-hook-test
bash openclaw-control/tests/sdlc-e2e.sh
bash openclaw-control/tests/research-e2e.sh
bash openclaw-control/tests/github-project-task.sh
bash openclaw-control/tests/notification-format.sh
bash openclaw-control/tests/spec-artifact.sh
bash openclaw-control/tests/coder-runner-dry-run.sh
bash openclaw-control/tests/research-runner-e2e.sh
bash openclaw-control/tests/canary-cleanup.sh
for file in openclaw-control/scripts/* openclaw-control/tests/*; do
  [ -f "$file" ] || continue
  bash -n "$file"
done
for file in openclaw-control/hooks/*.sh; do
  [ -f "$file" ] || continue
  bash -n "$file"
done
echo "[smoke] ok"
