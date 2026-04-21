#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-coder-runner-bridge-guard"
export CONTROL_CODER_REPO_ALLOWLIST="sidnevart/chappi-ai-office"
export CONTROL_CLAUDE_MODEL="kimi-k2.6:cloud"

cd "$ROOT/.."

cat >"$STATE_DIR/sync.json" <<'JSON'
{
  "item_id": "coder_bridge_42",
  "project_key": "chappi-ai-office",
  "repository": "sidnevart/chappi-ai-office",
  "status": "Todo",
  "title": "Coder runner bridge guard canary"
}
JSON

bash openclaw-control/scripts/oc-sdlc sync "$STATE_DIR/sync.json" >/tmp/oc-coder-bridge-sync.out
bash openclaw-control/scripts/oc-sdlc prepare-spec chappi-ai-office coder_bridge_42 >/tmp/oc-coder-bridge-spec.out
bash openclaw-control/scripts/oc-sdlc publish-spec chappi-ai-office coder_bridge_42 >/tmp/oc-coder-bridge-publish.out
bash openclaw-control/scripts/oc-approval approve spec-coder_bridge_42 >/tmp/oc-coder-bridge-approve.out
bash openclaw-control/scripts/oc-sdlc bootstrap-branch chappi-ai-office coder_bridge_42 >/tmp/oc-coder-bridge-branch.out

set +e
bash openclaw-control/scripts/oc-sdlc run-coder chappi-ai-office coder_bridge_42 >/tmp/oc-coder-bridge-run.out
status=$?
set -e

test "$status" -eq 1
grep -q '"backend_mode": "bridge"' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_bridge_42.json"
grep -q '"preflight_ok": false' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_bridge_42.json"
grep -q 'requires CONTROL_CLAUDE_BASE_URL' "$CONTROL_STATE_DIR/coder-runs/chappi-ai-office/coder_bridge_42.json"
grep -q '"state": "coder_failed"' "$CONTROL_STATE_DIR/jobs/sdlc/chappi-ai-office/coder_bridge_42.json"

echo "[coder-runner-bridge-guard] ok"
