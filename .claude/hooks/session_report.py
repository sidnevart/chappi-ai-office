#!/usr/bin/env python3
"""
Stop hook: prints a structured session report at the end of each Claude session.
Reads optional session_log.jsonl for accumulated done/pending/blocked items.
"""
import json
import os
import sys
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "session_log.jsonl")
LOG_PATH = os.path.normpath(LOG_PATH)

def load_log():
    items = {"done": [], "pending": [], "blocked": [], "next": []}
    if not os.path.exists(LOG_PATH):
        return items
    with open(LOG_PATH) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                status = entry.get("status", "")
                text = entry.get("text", "")
                if status in items and text:
                    items[status].append(text)
            except Exception:
                continue
    return items

def main():
    items = load_log()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n{'='*50}")
    print(f"  AI Office — Session Report  [{now}]")
    print(f"{'='*50}")

    if items["done"]:
        print("\n✅ Done:")
        for item in items["done"][-5:]:
            print(f"   • {item}")
    else:
        print("\n✅ Done: (nothing logged this session)")

    if items["pending"]:
        print("\n⏳ Pending:")
        for item in items["pending"][-5:]:
            print(f"   • {item}")

    if items["blocked"]:
        print("\n🚫 Blocked:")
        for item in items["blocked"][-5:]:
            print(f"   • {item}")

    if items["next"]:
        print("\n➡️  Next:")
        for item in items["next"][-3:]:
            print(f"   • {item}")

    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
