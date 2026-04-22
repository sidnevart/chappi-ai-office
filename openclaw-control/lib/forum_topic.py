#!/usr/bin/env python3
"""Create Telegram forum topics via Bot API.

This module provides functionality to create forum topics in Telegram
supergroups, integrating with the OpenClaw SDLC workflow.

Usage:
    python forum_topic.py create <chat_id> <topic_name> [--message TEXT]
    python forum_topic.py list <chat_id>
    python forum_topic.py close <chat_id> <topic_id>
    python forum_topic.py reopen <chat_id> <topic_id>

Environment variables:
    OPENCLAW_TG_BOT: Telegram bot token (required)
"""

import json
import os
import sys
from urllib import error, parse, request
from typing import Any


def get_bot_token() -> str:
    """Get Telegram bot token from environment."""
    token = os.environ.get("OPENCLAW_TG_BOT", "")
    if not token:
        raise ValueError("OPENCLAW_TG_BOT environment variable is required")
    return token


def telegram_api(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Call Telegram Bot API method."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    encoded = parse.urlencode(params).encode()
    req = request.Request(url, data=encoded, method="POST")
    try:
        with request.urlopen(req, timeout=30) as resp:
            body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        if not body.get("ok"):
            description = body.get("description", "Unknown error")
            raise RuntimeError(f"Telegram API error: {description}")
        return body.get("result", {})
    except error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def create_forum_topic(
    chat_id: str | int,
    name: str,
    icon_color: int | None = None,
    icon_custom_emoji_id: str | None = None,
) -> dict[str, Any]:
    """Create a new forum topic.

    Args:
        chat_id: Unique identifier for the target chat or username of the target supergroup
        name: Name of the topic, 1-128 characters
        icon_color: Color of the topic icon in RGB format (optional)
        icon_custom_emoji_id: Custom emoji for the topic icon (optional)

    Returns:
        dict with topic info (message_thread_id, name, etc.)
    """
    token = get_bot_token()
    params: dict[str, Any] = {"chat_id": chat_id, "name": name}
    if icon_color is not None:
        params["icon_color"] = icon_color
    if icon_custom_emoji_id:
        params["icon_custom_emoji_id"] = icon_custom_emoji_id
    return telegram_api(token, "createForumTopic", params)


def send_topic_message(
    chat_id: str | int,
    topic_id: int,
    text: str,
    parse_mode: str | None = None,
) -> dict[str, Any]:
    """Send a message to a forum topic.

    Args:
        chat_id: Chat ID
        topic_id: Topic thread ID
        text: Message text
        parse_mode: Parse mode (HTML, Markdown, etc.)

    Returns:
        dict with message info
    """
    token = get_bot_token()
    params: dict[str, Any] = {
        "chat_id": chat_id,
        "message_thread_id": topic_id,
        "text": text,
        "disable_web_page_preview": "true",
    }
    if parse_mode:
        params["parse_mode"] = parse_mode
    return telegram_api(token, "sendMessage", params)


def edit_forum_topic(
    chat_id: str | int,
    topic_id: int,
    name: str | None = None,
    icon_custom_emoji_id: str | None = None,
) -> dict[str, Any]:
    """Edit name and icon of a forum topic.

    Args:
        chat_id: Chat ID
        topic_id: Topic thread ID
        name: New topic name (optional)
        icon_custom_emoji_id: New custom emoji for the icon (optional)

    Returns:
        dict with updated topic info
    """
    token = get_bot_token()
    params: dict[str, Any] = {"chat_id": chat_id, "message_thread_id": topic_id}
    if name:
        params["name"] = name
    if icon_custom_emoji_id:
        params["icon_custom_emoji_id"] = icon_custom_emoji_id
    return telegram_api(token, "editForumTopic", params)


def close_forum_topic(chat_id: str | int, topic_id: int) -> dict[str, Any]:
    """Close a forum topic.

    Args:
        chat_id: Chat ID
        topic_id: Topic thread ID

    Returns:
        dict with result
    """
    token = get_bot_token()
    params: dict[str, Any] = {"chat_id": chat_id, "message_thread_id": topic_id}
    return telegram_api(token, "closeForumTopic", params)


def reopen_forum_topic(chat_id: str | int, topic_id: int) -> dict[str, Any]:
    """Reopen a closed forum topic.

    Args:
        chat_id: Chat ID
        topic_id: Topic thread ID

    Returns:
        dict with result
    """
    token = get_bot_token()
    params: dict[str, Any] = {"chat_id": chat_id, "message_thread_id": topic_id}
    return telegram_api(token, "reopenForumTopic", params)


def delete_forum_topic(chat_id: str | int, topic_id: int) -> dict[str, Any]:
    """Delete a forum topic.

    Args:
        chat_id: Chat ID
        topic_id: Topic thread ID

    Returns:
        dict with result
    """
    token = get_bot_token()
    params: dict[str, Any] = {"chat_id": chat_id, "message_thread_id": topic_id}
    return telegram_api(token, "deleteForumTopic", params)


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: forum_topic.py <command> [args...]", file=sys.stderr)
        print("Commands: create, edit, close, reopen, delete", file=sys.stderr)
        return 1

    command = sys.argv[1]

    try:
        if command == "create":
            if len(sys.argv) < 4:
                print("Usage: forum_topic.py create <chat_id> <name> [--message TEXT]", file=sys.stderr)
                return 1
            chat_id = sys.argv[2]
            name = sys.argv[3]
            message = None
            if "--message" in sys.argv:
                idx = sys.argv.index("--message")
                if idx + 1 < len(sys.argv):
                    message = sys.argv[idx + 1]

            result = create_forum_topic(chat_id, name)
            topic_id = result.get("message_thread_id")
            output = {
                "status": "ok",
                "topic_id": topic_id,
                "topic_name": name,
                "chat_id": chat_id,
                "summary": f"Created forum topic '{name}' (id: {topic_id}) in chat {chat_id}",
            }

            if message and topic_id:
                send_topic_message(chat_id, topic_id, message)
                output["message_sent"] = True

            print(json.dumps(output, indent=2))

        elif command == "edit":
            if len(sys.argv) < 4:
                print("Usage: forum_topic.py edit <chat_id> <topic_id> [--name NAME]", file=sys.stderr)
                return 1
            chat_id = sys.argv[2]
            topic_id = int(sys.argv[3])
            name = None
            if "--name" in sys.argv:
                idx = sys.argv.index("--name")
                if idx + 1 < len(sys.argv):
                    name = sys.argv[idx + 1]

            edit_forum_topic(chat_id, topic_id, name=name)
            print(json.dumps({"status": "ok", "summary": f"Edited topic {topic_id}"}, indent=2))

        elif command == "close":
            if len(sys.argv) < 4:
                print("Usage: forum_topic.py close <chat_id> <topic_id>", file=sys.stderr)
                return 1
            chat_id = sys.argv[2]
            topic_id = int(sys.argv[3])
            close_forum_topic(chat_id, topic_id)
            print(json.dumps({"status": "ok", "summary": f"Closed topic {topic_id}"}, indent=2))

        elif command == "reopen":
            if len(sys.argv) < 4:
                print("Usage: forum_topic.py reopen <chat_id> <topic_id>", file=sys.stderr)
                return 1
            chat_id = sys.argv[2]
            topic_id = int(sys.argv[3])
            reopen_forum_topic(chat_id, topic_id)
            print(json.dumps({"status": "ok", "summary": f"Reopened topic {topic_id}"}, indent=2))

        elif command == "delete":
            if len(sys.argv) < 4:
                print("Usage: forum_topic.py delete <chat_id> <topic_id>", file=sys.stderr)
                return 1
            chat_id = sys.argv[2]
            topic_id = int(sys.argv[3])
            delete_forum_topic(chat_id, topic_id)
            print(json.dumps({"status": "ok", "summary": f"Deleted topic {topic_id}"}, indent=2))

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            return 1

        return 0

    except ValueError as e:
        print(json.dumps({"status": "error", "summary": str(e)}), file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(json.dumps({"status": "error", "summary": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())