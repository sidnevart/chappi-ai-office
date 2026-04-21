#!/bin/bash
LOG="/tmp/ai-office-cloudflared.log"
TG_BOT_TOKEN="7600176913:AAEbL8lDDB_1vSIm3bni2WB2jlSzusMwLxc"
TG_CHAT_ID="764315256"

sleep 5
URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | tail -1)

if [ -n "$URL" ]; then
  curl -s -X POST "https://api.telegram.org/bot$TG_BOT_TOKEN/sendMessage" \
    -d chat_id="$TG_CHAT_ID" \
    -d text="TUNNEL_UPDATE:$URL"
  echo "Published: $URL"
fi
