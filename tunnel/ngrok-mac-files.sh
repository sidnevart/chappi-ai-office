#!/bin/bash
# Start fileserver + ngrok tunnel
export MAC_FILESERVER_TOKEN="${MAC_FILESERVER_TOKEN:-change-me-please}"
cd "$(dirname "$0")"
python3 mac-fileserver.py &
FILESERVER_PID=$!
echo "Fileserver started (PID $FILESERVER_PID)"

# Start ngrok
ngrok http 18500 --log=stdout --log-format=json 2>&1 &
NGROK_PID=$!

# Wait for ngrok to get URL
sleep 3
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for t in d.get('tunnels',[]):
    if t.get('proto') == 'https':
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo "✅ Mac files accessible at: $NGROK_URL"
    echo "Test: curl -H 'X-Token: $MAC_FILESERVER_TOKEN' $NGROK_URL/ai_office/"
    # Save URL to .env for agent to use
    grep -v MAC_FILES_URL /Users/artemsidnev/Documents/Projects/ai_office/.env > /tmp/env.tmp
    echo "MAC_FILES_URL=$NGROK_URL" >> /tmp/env.tmp
    mv /tmp/env.tmp /Users/artemsidnev/Documents/Projects/ai_office/.env
else
    echo "⚠️ Could not get ngrok URL"
fi

wait $FILESERVER_PID
