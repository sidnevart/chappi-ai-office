#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-coder-runner"
export CONTROL_CODER_REPO_ALLOWLIST="sidnevart/chappi-ai-office"

cd "$ROOT/.."

cat >"$STATE_DIR/sync.json" <<'JSON'
{
  "item_id": "coder_42",
  "project_key": "chappi-ai-office",
  "repository": "sidnevart/chappi-ai-office",
  "status": "Todo",
  "title": "Coder runner dry-run canary"
}
JSON

bash openclaw-control/scripts/oc-sdlc sync "$STATE_DIR/sync.json" >/tmp/oc-coder-sync.out
bash openclaw-control/scripts/oc-sdlc prepare-spec chappi-ai-office coder_42 >/tmp/oc-coder-spec.out
bash openclaw-control/scripts/oc-sdlc publish-spec chappi-ai-office coder_42 >/tmp/oc-coder-publish.out
bash openclaw-control/scripts/oc-approval approve spec-coder_42 >/tmp/oc-coder-approve.out
bash openclaw-control/scripts/oc-sdlc bootstrap-branch chappi-ai-office coder_42 >/tmp/oc-coder-branch.out
bash openclaw-control/scripts/oc-sdlc run-coder chappi-ai-office coder_42 >/tmp/oc-coder-run.out

test -f "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"mode": "dry-run"' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"executor": "claude"' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"execution_mode": "patch"' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q 'claude --print' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"backend_mode": "native"' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"preflight_ok": true' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_42.json"
grep -q '"state": "coder_dry_run_ready"' "$CONTROL_STATE_DIR/jobs/sdlc/chappi-ai-office/coder_42.json"

echo "[coder-runner-dry-run] ok"
