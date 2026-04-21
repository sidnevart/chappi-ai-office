#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
SOURCE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR" "$SOURCE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-research-runner"

cat >"$SOURCE_DIR/apartments.html" <<'HTML'
<html>
  <body>
    <a href="https://example.test/a1">2 rooms apartment near metro 150000 rub</a>
    <a href="https://example.test/a2">Studio apartment 90000 rub</a>
    <a href="https://example.test/a3">3 rooms apartment 210000 rub</a>
  </body>
</html>
HTML

cat >"$STATE_DIR/research-start.json" <<JSON
{
  "job_id": "apt-runner-canary",
  "job_type": "apartment_search",
  "title": "Apartment runner canary"
}
JSON

cat >"$STATE_DIR/research-complete.json" <<JSON
{
  "delivery_route": "research_digests",
  "filters_metrics": {"budget_max": 180000, "keywords": ["apartment"]},
  "output_format": ["table", "telegram_digest"],
  "output_schema": ["url", "title", "price", "source", "score"],
  "schedule": "@daily",
  "sources": ["file://$SOURCE_DIR/apartments.html"],
  "stop_conditions": ["manual stop"]
}
JSON

cd "$ROOT/.."

bash openclaw-control/scripts/oc-research start-interview "$STATE_DIR/research-start.json" >/tmp/oc-research-runner-start.out
bash openclaw-control/scripts/oc-research update-intake apt-runner-canary "$STATE_DIR/research-complete.json" >/tmp/oc-research-runner-update.out
bash openclaw-control/scripts/oc-research create-job apt-runner-canary >/tmp/oc-research-runner-create.out
bash openclaw-control/scripts/oc-research run-job apt-runner-canary >/tmp/oc-research-runner-run.out
bash openclaw-control/scripts/oc-research digest apt-runner-canary test-research-runner >/tmp/oc-research-runner-digest.out

test -f "$CONTROL_STATE_DIR/research/results/apt-runner-canary/test-research-runner.json"
test -f "$CONTROL_STATE_DIR/research/digests/apt-runner-canary/test-research-runner.json"
grep -q 'https://example.test/a1' "$CONTROL_STATE_DIR/research/results/apt-runner-canary/test-research-runner.json"
! grep -q 'https://example.test/a3' "$CONTROL_STATE_DIR/research/results/apt-runner-canary/test-research-runner.json"
grep -q '🏠 OpenClaw Research' "$CONTROL_STATE_DIR/research/digests/apt-runner-canary/test-research-runner.json"

echo "[research-runner-e2e] ok"
