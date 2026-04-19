#!/usr/bin/env bash
# Auto-approve pending openclaw device pairing requests
set -euo pipefail

PENDING=/root/.openclaw/devices/pending.json
TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"
GW_URL="ws://127.0.0.1:18789"

[ -f "$PENDING" ] || exit 0

REQUEST_IDS=$(python3 -c "
import json, sys
try:
    d = json.load(open('$PENDING'))
    for rid in d:
        print(rid)
except:
    pass
")

[ -z "$REQUEST_IDS" ] && exit 0

for RID in $REQUEST_IDS; do
    if [ -n "$TOKEN" ]; then
        openclaw devices approve "$RID" --token "$TOKEN" --url "$GW_URL" 2>/dev/null \
            && echo "[auto-approve] approved $RID" \
            || echo "[auto-approve] failed $RID"
    else
        openclaw devices approve "$RID" --url "$GW_URL" 2>/dev/null \
            && echo "[auto-approve] approved $RID" \
            || echo "[auto-approve] failed $RID"
    fi
done
