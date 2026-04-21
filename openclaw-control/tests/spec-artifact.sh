#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(mktemp -d)"
DOCS_DIR="$(mktemp -d)"
trap 'rm -rf "$STATE_DIR" "$DOCS_DIR"' EXIT

export CONTROL_STATE_DIR="$STATE_DIR/state"
export CONTROL_DOCS_ARTIFACT_DIR="$DOCS_DIR"
export CONTROL_DOCS_BASE_URL="https://docs.example.test/specs"
export RUN_ID="test-spec-artifact"

cd "$ROOT/.."

bash openclaw-control/scripts/oc-sdlc sync openclaw-control/tests/fixtures/github-project-sync.json >/tmp/oc-spec-artifact-sync.out
bash openclaw-control/scripts/oc-sdlc prepare-spec ai-office pvti_42 >/tmp/oc-spec-artifact-prepare.out
bash openclaw-control/scripts/oc-spec-artifact publish ai-office pvti_42 >/tmp/oc-spec-artifact-publish.out

test -f "$DOCS_DIR/ai-office/pvti_42.md"
test -f "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.artifact.json"
grep -q '"doc_url": "https://docs.example.test/specs/ai-office/pvti_42.md"' "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.artifact.json"
grep -q '"checksum_sha256":' "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.artifact.json"
grep -q 'https://docs.example.test/specs/ai-office/pvti_42.md' "$CONTROL_STATE_DIR/specs/ai-office/pvti_42.json"

echo "[spec-artifact] ok"
