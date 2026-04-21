#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-github-project-task"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-github-project create-task openclaw-control/tests/fixtures/github-project-task.json >/tmp/oc-github-project-task.out
bash openclaw-control/scripts/oc-github-project set-status openclaw-control/tests/fixtures/github-project-status.json >/tmp/oc-github-project-status.out

test -f "$CONTROL_STATE_DIR/github-projects/tasks/project-task-canary.json"
test -f "$CONTROL_STATE_DIR/github-projects/statuses/project-status-canary.json"
grep -q '"mode": "dry-run"' "$CONTROL_STATE_DIR/github-projects/tasks/project-task-canary.json"
grep -q '"status": "planned"' "$CONTROL_STATE_DIR/github-projects/tasks/project-task-canary.json"
grep -q 'OpenClaw SDLC project task canary' "$CONTROL_STATE_DIR/github-projects/tasks/project-task-canary.json"
grep -q '"project_status": "Specification Review"' "$CONTROL_STATE_DIR/github-projects/statuses/project-status-canary.json"

echo "[github-project-task] ok"
