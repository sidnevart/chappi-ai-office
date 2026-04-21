#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-notification-format"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-sdlc sync openclaw-control/tests/fixtures/github-project-sync.json >/tmp/oc-notify-sync.out
bash openclaw-control/scripts/oc-sdlc prepare-spec ai-office pvti_42 >/tmp/oc-notify-spec-prepare.out
bash openclaw-control/scripts/oc-sdlc publish-spec ai-office pvti_42 >/tmp/oc-notify-spec-publish.out
bash openclaw-control/scripts/oc-alert-route openclaw-control/tests/fixtures/alert-route.json >/tmp/oc-notify-alert.out
RUN_ID="test-notification-inline-json" python3 openclaw-control/lib/control_plane.py alert-route '{"severity":"medium","system":"control-plane","event_type":"notification.inline-json","summary":"Проверка inline JSON payload","next_action":"Проверить, что JSON не трактуется как путь.","dedupe_key":"inline-json-test"}' >/tmp/oc-notify-inline-json.out
bash openclaw-control/scripts/oc-approval approve spec-pvti_42 >/tmp/oc-notify-approve.out
bash openclaw-control/scripts/oc-sdlc bootstrap-branch ai-office pvti_42 >/tmp/oc-notify-branch.out
bash openclaw-control/scripts/oc-sdlc record-pr ai-office pvti_42 openclaw-control/tests/fixtures/pr-ready.json >/tmp/oc-notify-pr.out
bash openclaw-control/scripts/oc-sdlc record-ci ai-office pvti_42 openclaw-control/tests/fixtures/ci-passed.json >/tmp/oc-notify-ci.out

grep -q '📋 OpenClaw: спека на ревью' "$CONTROL_STATE_DIR/outbox/specs/test-notification-format.json"
grep -q 'Approval: `spec-pvti_42`' "$CONTROL_STATE_DIR/outbox/specs/test-notification-format.json"
grep -q '🟠 OpenClaw: алерт' "$CONTROL_STATE_DIR/alerts/events/test-notification-format.json"
grep -q '🟡 OpenClaw: алерт' "$CONTROL_STATE_DIR/alerts/events/test-notification-inline-json.json"
grep -q 'Проверка inline JSON payload' "$CONTROL_STATE_DIR/alerts/events/test-notification-inline-json.json"
grep -q '🔀 OpenClaw: PR готов к ревью' "$CONTROL_STATE_DIR/outbox/prs/test-notification-format.json"
grep -q 'Комментарии, замечания и requested changes оставляем в GitHub PR' "$CONTROL_STATE_DIR/outbox/prs/test-notification-format.json"

echo "[notification-format] ok"
