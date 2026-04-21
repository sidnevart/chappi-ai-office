#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-canary-cleanup"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-github-project close-canary '{"repository":"sidnevart/chappi-ai-office","issue_number":2,"project_owner":"sidnevart","project_number":2}' >/tmp/oc-canary-cleanup.out

test -f "$CONTROL_STATE_DIR/github-projects/canary-cleanup/issue-2.json"
grep -q '"mode": "dry-run"' "$CONTROL_STATE_DIR/github-projects/canary-cleanup/issue-2.json"
grep -q '"issue_number": 2' "$CONTROL_STATE_DIR/github-projects/canary-cleanup/issue-2.json"

echo "[canary-cleanup] ok"
