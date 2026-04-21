#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-research-e2e"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-research start-interview openclaw-control/tests/fixtures/research-start.json >/tmp/oc-research-start.out
if bash openclaw-control/scripts/oc-research create-job apt-moscow-weekly >/tmp/oc-research-blocked.out 2>/tmp/oc-research-blocked.err; then
  echo "create-job should block incomplete intake"
  exit 1
fi
bash openclaw-control/scripts/oc-research update-intake apt-moscow-weekly openclaw-control/tests/fixtures/research-complete.json >/tmp/oc-research-update.out
bash openclaw-control/scripts/oc-research create-job apt-moscow-weekly >/tmp/oc-research-create.out
bash openclaw-control/scripts/oc-research pause apt-moscow-weekly >/tmp/oc-research-pause.out
bash openclaw-control/scripts/oc-research resume apt-moscow-weekly >/tmp/oc-research-resume.out
bash openclaw-control/scripts/oc-research stop apt-moscow-weekly >/tmp/oc-research-stop.out

bash openclaw-control/scripts/oc-state-validate job_state_v1 "$CONTROL_STATE_DIR/jobs/research/apt-moscow-weekly.json" >/tmp/oc-research-job-validate.out
bash openclaw-control/scripts/oc-state-validate agent_state_v1 "$CONTROL_STATE_DIR/agents/research/apt-moscow-weekly.json" >/tmp/oc-research-agent-validate.out

test -f "$CONTROL_STATE_DIR/research/intake/apt-moscow-weekly.json"
test -f "$CONTROL_STATE_DIR/jobs/research/apt-moscow-weekly.json"
test -f "$CONTROL_STATE_DIR/agents/research/apt-moscow-weekly.json"
grep -q '"status": "stopped"' "$CONTROL_STATE_DIR/jobs/research/apt-moscow-weekly.json"
grep -q '"lifecycle_status": "stopped"' "$CONTROL_STATE_DIR/agents/research/apt-moscow-weekly.json"
grep -q '"session_key": "research:apt-moscow-weekly:intake"' "$CONTROL_STATE_DIR/jobs/research/apt-moscow-weekly.json"

echo "[research-e2e] ok"
