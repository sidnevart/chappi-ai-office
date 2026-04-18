#!/usr/bin/env python3
"""
PreToolUse hook: blocks writing known-secret patterns to non-.env files.
Reads CLAUDE_TOOL_INPUT from stdin (JSON).
Exit 2 = block the tool call.
"""
import json
import re
import sys

SAFE_FILES = {".env", ".env.example"}

SECRET_PATTERNS = [
    # Telegram bot token: digits:AAE...
    re.compile(r"\d{7,12}:AAE[a-zA-Z0-9_-]{30,}"),
    # Generic long base64-ish tokens (40+ chars)
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
    # Private keys
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    # AWS-style keys
    re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # can't parse → allow

    tool_name = data.get("tool_name", "")
    inp = data.get("tool_input", {})

    # Only check Write / Edit / MultiEdit
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = inp.get("file_path", inp.get("path", ""))
    filename = file_path.split("/")[-1] if file_path else ""

    if filename in SAFE_FILES:
        sys.exit(0)

    # Content to check
    content_parts = []
    if "content" in inp:
        content_parts.append(inp["content"])
    if "new_string" in inp:
        content_parts.append(inp["new_string"])
    if "edits" in inp:
        for edit in inp.get("edits", []):
            content_parts.append(edit.get("new_string", ""))
    content = "\n".join(content_parts)

    for pattern in SECRET_PATTERNS:
        match = pattern.search(content)
        if match:
            # Redact match in message
            snippet = match.group()[:6] + "..." if len(match.group()) > 6 else "***"
            print(
                f"🔒 SECRETS GUARD: Possible secret pattern detected in non-.env file '{filename}'.\n"
                f"   Pattern matched: {snippet}\n"
                f"   If this is intentional, write to .env instead.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
