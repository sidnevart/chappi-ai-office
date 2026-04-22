#!/usr/bin/env bash
# create-forum-topic.sh - Create a Telegram forum topic
# Usage: create-forum-topic.sh <chat_id> <topic_name> [message]
#
# Required environment variables:
#   OPENCLAW_TG_BOT - Telegram bot token (or use OPENCLAW_CONFIG)
#
# This script creates a new forum topic in a Telegram supergroup.
# It uses the Telegram Bot API createForumTopic method.

set -euo pipefail

# Parse arguments
CHAT_ID="${1:-}"
TOPIC_NAME="${2:-}"
MESSAGE="${3:-Topic created by OpenClaw SDLC}"

# Validate arguments
if [[ -z "$CHAT_ID" || -z "$TOPIC_NAME" ]]; then
    echo "Usage: $0 <chat_id> <topic_name> [message]" >&2
    exit 1
fi

# Get bot token
BOT_TOKEN="${OPENCLAW_TG_BOT:-}"
if [[ -z "$BOT_TOKEN" ]]; then
    echo "Error: OPENCLAW_TG_BOT environment variable is required" >&2
    exit 1
fi

# Create forum topic via Telegram API
RESPONSE=$(curl -s -X POST \
    "https://api.telegram.org/bot${BOT_TOKEN}/createForumTopic" \
    -d "chat_id=${CHAT_ID}" \
    -d "name=${TOPIC_NAME}")

# Check for errors
SUCCESS=$(echo "$RESPONSE" | jq -r '.ok // false')
if [[ "$SUCCESS" != "true" ]]; then
    ERROR=$(echo "$RESPONSE" | jq -r '.description // "Unknown error"')
    echo "Error creating forum topic: $ERROR" >&2
    exit 1
fi

# Extract topic info
TOPIC_ID=$(echo "$RESPONSE" | jq -r '.result.message_thread_id')
MESSAGE_ID=$(echo "$RESPONSE" | jq -r '.result.message_id')

# If initial message provided, send it to the topic
if [[ -n "$MESSAGE" ]]; then
    SEND_RESPONSE=$(curl -s -X POST \
        "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "message_thread_id=${TOPIC_ID}" \
        -d "text=${MESSAGE}" \
        -d "disable_web_page_preview=true")
    
    SEND_SUCCESS=$(echo "$SEND_RESPONSE" | jq -r '.ok // false')
    if [[ "$SEND_SUCCESS" != "true" ]]; then
        SEND_ERROR=$(echo "$SEND_RESPONSE" | jq -r '.description // "Unknown error"')
        echo "Warning: Topic created but failed to send initial message: $SEND_ERROR" >&2
    fi
fi

# Output result as JSON
jq -n \
    --arg topic_id "$TOPIC_ID" \
    --arg topic_name "$TOPIC_NAME" \
    --arg chat_id "$CHAT_ID" \
    --arg message_id "$MESSAGE_ID" \
    '{
        status: "ok",
        topic_id: ($topic_id | tonumber),
        topic_name: $topic_name,
        chat_id: $chat_id,
        message_id: ($message_id | tonumber),
        summary: ("Created forum topic '"'"'" + $topic_name + "'"'"' in chat " + $chat_id)
    }'