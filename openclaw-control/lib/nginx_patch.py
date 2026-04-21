#!/usr/bin/env python3
import sys
from pathlib import Path


INCLUDE_LINE = "    include /etc/nginx/snippets/openclaw-webhooks.inc;\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: nginx_patch.py <openclaw-ssl-path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    content = path.read_text(encoding="utf-8")
    if INCLUDE_LINE in content:
        print("include already present")
        return 0
    marker = "    location = /control { return 301 /control/; }\n"
    if marker not in content:
        print("marker not found", file=sys.stderr)
        return 1
    content = content.replace(marker, marker + "\n" + INCLUDE_LINE, 1)
    path.write_text(content, encoding="utf-8")
    print("patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
