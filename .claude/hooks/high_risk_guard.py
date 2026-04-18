#!/usr/bin/env python3
"""
PreToolUse hook: blocks or warns on high-risk Bash commands.
Reads CLAUDE_TOOL_INPUT from stdin (JSON).
Exit 2 = block. Exit 0 with stderr message = warn (command still runs).
"""
import json
import re
import sys

BLOCK_PATTERNS = [
    # Recursive delete of root or home
    (re.compile(r"rm\s+(-\w+\s+)*-rf?\s+(/|~[/\s]|/home|/root|/usr|/etc|/var)\b"), "rm -rf on system directory"),
    # Force push to main/master
    (re.compile(r"git\s+push\s+.*--force.*\b(main|master)\b"), "force push to main/master"),
    (re.compile(r"git\s+push\s+.*\b(main|master)\b.*--force"), "force push to main/master"),
    # Redirect to /etc
    (re.compile(r">\s*/etc/"), "write to /etc"),
    # Drop database
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE"),
    # Kill all processes
    (re.compile(r"kill\s+-9\s+-1\b"), "kill -9 -1 (kill all processes)"),
    # Wipe disk
    (re.compile(r"dd\s+.*of=/dev/(sd[a-z]|nvme|disk)\d*\b"), "dd write to block device"),
    # chmod 777 on system dirs
    (re.compile(r"chmod\s+777\s+/\b"), "chmod 777 on root"),
]

WARN_PATTERNS = [
    (re.compile(r"docker\s+rm\s+(-f\s+)?"), "docker rm — this will delete containers"),
    (re.compile(r"docker\s+rmi\s+"), "docker rmi — this will delete images"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE — check for WHERE clause"),
    (re.compile(r"systemctl\s+(stop|disable)\s+"), "stopping/disabling a systemd service"),
    (re.compile(r"git\s+reset\s+--hard"), "git reset --hard — local changes will be lost"),
    (re.compile(r"truncate\s+table", re.IGNORECASE), "TRUNCATE TABLE — all rows will be deleted"),
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    for pattern, label in BLOCK_PATTERNS:
        if pattern.search(command):
            print(
                f"🚫 HIGH-RISK GUARD: Blocked dangerous command.\n"
                f"   Reason: {label}\n"
                f"   Command: {command[:120]}\n"
                f"   If you are sure, confirm explicitly with the user first.",
                file=sys.stderr,
            )
            sys.exit(2)

    for pattern, label in WARN_PATTERNS:
        if pattern.search(command):
            print(
                f"⚠️  HIGH-RISK GUARD: Potentially dangerous operation detected.\n"
                f"   Reason: {label}\n"
                f"   Command: {command[:120]}\n"
                f"   Proceeding — but verify this is intentional.",
                file=sys.stderr,
            )
            # exit(0) = warn only, command still runs
            sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
