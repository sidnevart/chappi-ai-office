#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export RUN_ID="test-sdlc-e2e"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-sdlc sync openclaw-control/tests/fixtures/github-project-sync.json >/tmp/oc-sdlc-sync.out
bash openclaw-control/scripts/oc-sdlc prepare-spec ai-office pvti_42 >/tmp/oc-sdlc-prepare.out
bash openclaw-control/scripts/oc-sdlc publish-spec ai-office pvti_42 >/tmp/oc-sdlc-publish.out
bash openclaw-control/scripts/oc-approval approve spec-pvti_42 >/tmp/oc-sdlc-approve-spec.out
bash openclaw-control/scripts/oc-sdlc bootstrap-branch ai-office pvti_42 >/tmp/oc-sdlc-branch.out
bash openclaw-control/scripts/oc-sdlc record-pr ai-office pvti_42 openclaw-control/tests/fixtures/pr-ready.json >/tmp/oc-sdlc-pr.out
bash openclaw-control/scripts/oc-sdlc record-ci ai-office pvti_42 openclaw-control/tests/fixtures/ci-passed.json >/tmp/oc-sdlc-ci.out

bash openclaw-control/scripts/oc-state-validate job_state_v1 "$CONTROL_STATE_DIR/jobs/sdlc/ai-office/pvti_42.json" >/tmp/oc-sdlc-job-validate.out
bash openclaw-control/scripts/oc-state-validate approval_state_v1 "$CONTROL_STATE_DIR/approvals/spec-pvti_42.json" >/tmp/oc-sdlc-approval-validate.out
bash openclaw-control/scripts/oc-state-validate approval_state_v1 "$CONTROL_STATE_DIR/approvals/pr-pvti_42.json" >/tmp/oc-sdlc-pr-approval-validate.out

test -f "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.md"
test -f "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.json"
test -f "$CONTROL_STATE_DIR/branches/ai-office/pvti_42.json"
test -f "$CONTROL_STATE_DIR/prs/ai-office/pvti_42.json"
test -f "$CONTROL_STATE_DIR/ci/ai-office/pvti_42.json"
test -f "$CONTROL_STATE_DIR/outbox/prs/test-sdlc-e2e.json"
grep -q '"state": "awaiting_pr_digest_approval"' "$CONTROL_STATE_DIR/jobs/sdlc/ai-office/pvti_42.json"
grep -q '"status": "approved"' "$CONTROL_STATE_DIR/approvals/spec-pvti_42.json"
grep -q '"status": "pending"' "$CONTROL_STATE_DIR/approvals/pr-pvti_42.json"

echo "[sdlc-e2e] ok"
