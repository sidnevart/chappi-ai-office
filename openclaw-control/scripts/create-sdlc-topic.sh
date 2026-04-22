#!/usr/bin/env bash
# create-sdlc-topic.sh - Create Telegram forum topic for SDLC workflow
# Usage: create-sdlc-topic.sh <project_key> <item_id> [--message TEXT]
#
# This script creates a new forum topic in the OpenClaw specs channel
# and returns the topic ID for use in SDLC workflow.
#
# Environment:
#   OPENCLAW_SPECS_CHAT_ID - Telegram chat ID for specs/policy discussions
#   OPENCLAW_TG_BOT - Telegram bot token

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse arguments
PROJECT_KEY="${1:-}"
ITEM_ID="${2:-}"
MESSAGE="${3:-Topic created for SDLC tracking}"
DRY_RUN="${DRY_RUN:-false}"

# Validate arguments
if [[ -z "$PROJECT_KEY" || -z "$ITEM_ID" ]]; then
    echo "Usage: $0 <project_key> <item_id> [--message TEXT]" >&2
    exit 1
fi

# Get chat ID
CHAT_ID="${OPENCLAW_SPECS_CHAT_ID:-}"
if [[ -z "$CHAT_ID" ]]; then
    echo "Error: OPENCLAW_SPECS_CHAT_ID environment variable is required" >&2
    exit 1
fi

# Generate topic name
TOPIC_NAME="📋 ${PROJECT_KEY}: ${ITEM_ID}"

# Check for dry-run mode
if [[ "$DRY_RUN" == "true" ]]; then
    jq -n \
        --arg project_key "$PROJECT_KEY" \
        --arg item_id "$ITEM_ID" \
        --arg topic_name "$TOPIC_NAME" \
        --arg chat_id "$CHAT_ID" \
        '{
            status: "dry_run",
            topic_name: $topic_name,
            project_key: $project_key,
            item_id: $item_id,
            chat_id: $chat_id,
            summary: ("Would create forum topic '"'"'" + $topic_name + "'"'"' in channel"),
            note: "Set DRY_RUN=false to create topic"
        }'
    exit 0
fi

# Create topic using Python module
python3 "$ROOT/lib/forum_topic.py" create "$CHAT_ID" "$TOPIC_NAME" --message "$MESSAGE"