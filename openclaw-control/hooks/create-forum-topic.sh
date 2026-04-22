#!/usr/bin/env bash
# create-forum-topic.sh - Hook for creating Telegram forum topics
# Triggered by: sdlc.forum_topic.create event
#
# This hook creates a new forum topic in a Telegram supergroup
# and records the topic ID in the SDLC job state.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD="${1:-}"

# If no payload, try stdin
if [[ -z "$PAYLOAD" ]]; then
    PAYLOAD=$(cat)
fi

# Parse payload
CHAT_ID=$(jq -r '.chat_id // empty' <<< "$PAYLOAD")
TOPIC_NAME=$(jq -r '.topic_name // empty' <<< "$PAYLOAD")
MESSAGE=$(jq -r '.message // "Topic created for SDLC tracking"' <<< "$PAYLOAD")
PROJECT_KEY=$(jq -r '.project_key // empty' <<< "$PAYLOAD")
ITEM_ID=$(jq -r '.item_id // empty' <<< "$PAYLOAD")
RUN_ID=$(jq -r '.run_id // "topic-'$(date +%Y%m%d%H%M%S)'"' <<< "$PAYLOAD")

# Validate required fields
if [[ -z "$CHAT_ID" || -z "$TOPIC_NAME" ]]; then
    jq -n \
        --arg run_id "$RUN_ID" \
        '{
            status: "error",
            run_id: $run_id,
            summary: "Missing required fields: chat_id and topic_name are required"
        }' >&2
    exit 1
fi

# Get bot token
BOT_TOKEN="${OPENCLAW_TG_BOT:-}"
if [[ -z "$BOT_TOKEN" ]]; then
    jq -n \
        --arg run_id "$RUN_ID" \
        '{
            status: "error",
            run_id: $run_id,
            summary: "Missing environment variable: OPENCLAW_TG_BOT"
        }' >&2
    exit 1
fi

# Create the forum topic
RESPONSE=$(curl -s -X POST \
    "https://api.telegram.org/bot${BOT_TOKEN}/createForumTopic" \
    -d "chat_id=${CHAT_ID}" \
    -d "name=${TOPIC_NAME}")

# Check for errors
SUCCESS=$(jq -r '.ok // false' <<< "$RESPONSE")
if [[ "$SUCCESS" != "true" ]]; then
    ERROR=$(jq -r '.description // "Unknown error"' <<< "$RESPONSE")
    jq -n \
        --arg run_id "$RUN_ID" \
        --arg chat_id "$CHAT_ID" \
        --arg topic_name "$TOPIC_NAME" \
        --arg error "$ERROR" \
        '{
            status: "error",
            run_id: $run_id,
            chat_id: $chat_id,
            topic_name: $topic_name,
            summary: ("Failed to create forum topic: " + $error)
        }' >&2
    exit 1
fi

# Extract topic ID
TOPIC_ID=$(jq -r '.result.message_thread_id' <<< "$RESPONSE")
MESSAGE_ID=$(jq -r '.result.message_id' <<< "$RESPONSE")

# Send initial message if provided
if [[ -n "$MESSAGE" && "$MESSAGE" != "null" ]]; then
    SEND_RESPONSE=$(curl -s -X POST \
        "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "message_thread_id=${TOPIC_ID}" \
        -d "text=${MESSAGE}" \
        -d "disable_web_page_preview=true")
    
    SEND_SUCCESS=$(jq -r '.ok // false' <<< "$SEND_RESPONSE")
    if [[ "$SEND_SUCCESS" != "true" ]]; then
        # Log warning but don't fail
        echo "Warning: Failed to send initial message to topic" >&2
    fi
fi

# Record event if project_key and item_id provided
if [[ -n "$PROJECT_KEY" && -n "$ITEM_ID" ]]; then
    STATE_DIR="${CONTROL_STATE_DIR:-$ROOT/.runtime}"
    EVENT_FILE="$STATE_DIR/events/forum_topic_create.jsonl"
    mkdir -p "$(dirname "$EVENT_FILE")"
    
    jq -n \
        --arg project_key "$PROJECT_KEY" \
        --arg item_id "$ITEM_ID" \
        --arg topic_id "$TOPIC_ID" \
        --arg topic_name "$TOPIC_NAME" \
        --arg run_id "$RUN_ID" \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{
            event_type: "sdlc.forum_topic.created",
            project_key: $project_key,
            item_id: $item_id,
            topic_id: ($topic_id | tonumber),
            topic_name: $topic_name,
            run_id: $run_id,
            timestamp: $timestamp
        }' >> "$EVENT_FILE"
fi

# Output result
jq -n \
    --arg topic_id "$TOPIC_ID" \
    --arg topic_name "$TOPIC_NAME" \
    --arg chat_id "$CHAT_ID" \
    --arg message_id "$MESSAGE_ID" \
    --arg project_key "$PROJECT_KEY" \
    --arg item_id "$ITEM_ID" \
    --arg run_id "$RUN_ID" \
    '{
        status: "ok",
        topic_id: ($topic_id | tonumber),
        topic_name: $topic_name,
        chat_id: $chat_id,
        message_id: ($message_id | tonumber),
        project_key: $project_key,
        item_id: $item_id,
        run_id: $run_id,
        summary: ("Created forum topic '"'"'" + $topic_name + "'"'"' in chat " + $chat_id)
    }'