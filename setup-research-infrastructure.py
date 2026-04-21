import os
import json

# Create folder structure
folders = [
    "/research",
    "/research/founder-cron",
    "/research/company-deep-dives",
    "/research/generalized",
    "/research/apartments",
    "/opt/openclaw-control/.runtime/research",
    "/opt/openclaw-control/.runtime/research/intake",
    "/opt/openclaw-control/.runtime/research/jobs",
    "/opt/openclaw-control/.runtime/research/results",
    "/opt/openclaw-control/.runtime/research/digests",
    "/opt/openclaw-control/.runtime/research/dedupe",
    "/opt/openclaw-control/.runtime/research/apartments",
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created: {folder}")

# Create founder cron script
founder_cron_script = '''#!/bin/bash
# Founder Research Cron Script
# Runs daily at 09:00 via systemd timer

LOCK_FILE="/opt/openclaw-control/.runtime/research/founder-cron.lock"
RUNTIME_DIR="/opt/openclaw-control/.runtime/research"
LOG_FILE="/var/log/founder-cron.log"

# Timestamp
TS=$(date '+%Y-%m-%d %H:%M:%S')

# Check lock
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pid',''))" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "[$TS] ERROR: Founder cron already running (PID: $LOCK_PID)" >> "$LOG_FILE"
        exit 1
    else
        echo "[$TS] WARN: Stale lock file found, removing" >> "$LOG_FILE"
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock
echo "{\\"started_at\\": \\"$(date -Iseconds)\\", \\"pid\\": $$, \\"status\\": \\"running\\", \\"agent\\": \\"scout-monitor\\"}" > "$LOCK_FILE"
echo "[$TS] Founder cron started" >> "$LOG_FILE"

# Ensure directories exist
mkdir -p "$RUNTIME_DIR"/intake "$RUNTIME_DIR"/jobs "$RUNTIME_DIR"/results "$RUNTIME_DIR"/digests "$RUNTIME_DIR"/dedupe

# Create daily intake file
DATE=$(date '+%Y-%m-%d')
INTAKE_FILE="$RUNTIME_DIR/intake/founder-cron-$DATE.json"

cat > "$INTAKE_FILE" <<INTAKE_EOF
{
  "type": "founder-cron",
  "date": "$DATE",
  "status": "started",
  "sectors": ["fintech", "ai", "agentic-tools", "physical-ai", "cybersecurity"],
  "sources": [
    "techcrunch.com",
    "crunchbase.com",
    "dealroom.co",
    "sifted.eu",
    "ycombinator.com"
  ],
  "output_dir": "/research/founder-cron/$DATE"
}
INTAKE_EOF

# Create output directory
mkdir -p "/research/founder-cron/$DATE"

# Post to Telegram (via openclaw notification)
TG_NOTIFY_CHAT_ID=$(grep TG_NOTIFY_CHAT_ID /root/.env 2>/dev/null | cut -d= -f2)
if [ -n "$TG_NOTIFY_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${OPENCLAW_TG_BOT}/sendMessage" \\
        -H "Content-Type: application/json" \\
        -d "{\\"chat_id\\": $TG_NOTIFY_CHAT_ID, \\"text\\": \\"📊 Founder Cron started\\nDate: $DATE\\nStatus: DISCOVER phase\\nAgent: scout-monitor\\\"}" 2>/dev/null || true
fi

# Trigger scout-monitor via openclaw
# Note: This would be done via the main agent or research-orchestrator
# For now, we just log that it should be triggered
echo "[$TS] Should spawn: scout-monitor for founder-cron-$DATE" >> "$LOG_FILE"

# Update lock with completion
TS=$(date '+%Y-%m-%d %H:%M:%S')
echo "{\\"started_at\\": \\"$(date -Iseconds)\\", \\"pid\\": $$, \\"status\\": \\"completed\\", \\"finished_at\\": \\"$(date -Iseconds)\\"}" > "$LOCK_FILE"
echo "[$TS] Founder cron completed" >> "$LOG_FILE"

exit 0
'''

with open("/opt/openclaw-control/scripts/founder-cron.sh", "w") as f:
    f.write(founder_cron_script)
os.chmod("/opt/openclaw-control/scripts/founder-cron.sh", 0o755)
print("Created: /opt/openclaw-control/scripts/founder-cron.sh")

# Create apartment cron script
apartment_cron_script = '''#!/bin/bash
# Apartment Search Cron Script
# Runs daily via systemd timer

LOCK_FILE="/opt/openclaw-control/.runtime/research/apartment-cron.lock"
RUNTIME_DIR="/opt/openclaw-control/.runtime/research"
LOG_FILE="/var/log/apartment-cron.log"

TS=$(date '+%Y-%m-%d %H:%M:%S')

# Check lock
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pid',''))" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "[$TS] ERROR: Apartment cron already running" >> "$LOG_FILE"
        exit 1
    else
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock
echo "{\\"started_at\\": \\"$(date -Iseconds)\\", \\"pid\\": $$, \\"status\\": \\"running\\"}" > "$LOCK_FILE"
echo "[$TS] Apartment cron started" >> "$LOG_FILE"

DATE=$(date '+%Y-%m-%d')
mkdir -p "/research/apartments/$DATE"

# Create intake
INTAKE_FILE="$RUNTIME_DIR/intake/apartment-cron-$DATE.json"
cat > "$INTAKE_FILE" <<INTAKE_EOF
{
  "type": "apartment-cron",
  "date": "$DATE",
  "status": "started",
  "cities": ["moscow", "saint-petersburg"],
  "criteria": {
    "rooms": "1-2",
    "budget_max_rub": 80000,
    "districts": []
  }
}
INTAKE_EOF

echo "[$TS] Should spawn: scout-monitor for apartment search" >> "$LOG_FILE"

# Update lock
TS=$(date '+%Y-%m-%d %H:%M:%S')
echo "{\\"status\\": \\"completed\\", \\"finished_at\\": \\"$(date -Iseconds)\\"}" > "$LOCK_FILE"
echo "[$TS] Apartment cron completed" >> "$LOG_FILE"

exit 0
'''

with open("/opt/openclaw-control/scripts/apartment-cron.sh", "w") as f:
    f.write(apartment_cron_script)
os.chmod("/opt/openclaw-control/scripts/apartment-cron.sh", 0o755)
print("Created: /opt/openclaw-control/scripts/apartment-cron.sh")

# Create systemd timer for founder cron
founder_timer = '''[Unit]
Description=Founder Research Cron Timer

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
'''

founder_service = '''[Unit]
Description=Founder Research Cron
After=openclaw.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/root
EnvironmentFile=/root/.env
ExecStart=/opt/openclaw-control/scripts/founder-cron.sh
StandardOutput=append:/var/log/founder-cron.log
StandardError=append:/var/log/founder-cron.log
'''

with open("/etc/systemd/system/founder-cron.timer", "w") as f:
    f.write(founder_timer)
print("Created: /etc/systemd/system/founder-cron.timer")

with open("/etc/systemd/system/founder-cron.service", "w") as f:
    f.write(founder_service)
print("Created: /etc/systemd/system/founder-cron.service")

# Create systemd timer for apartment cron
apartment_timer = '''[Unit]
Description=Apartment Search Cron Timer

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
'''

apartment_service = '''[Unit]
Description=Apartment Search Cron
After=openclaw.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/root
EnvironmentFile=/root/.env
ExecStart=/opt/openclaw-control/scripts/apartment-cron.sh
StandardOutput=append:/var/log/apartment-cron.log
StandardError=append:/var/log/apartment-cron.log
'''

with open("/etc/systemd/system/apartment-cron.timer", "w") as f:
    f.write(apartment_timer)
print("Created: /etc/systemd/system/apartment-cron.timer")

with open("/etc/systemd/system/apartment-cron.service", "w") as f:
    f.write(apartment_service)
print("Created: /etc/systemd/system/apartment-cron.service")

# Create MEMORY.md template for research system
memory_md = '''# Research Memory

## Исследованные компании

### Founder Cron Discoveries

| Date | Company | Sector | Stage | Russia Fit | Status |
|------|---------|--------|-------|------------|--------|

### Company Deep Dives

| Date | Company | Trigger | Analyst | Status |
|------|---------|---------|---------|--------|

## Фонды

| Fund | Type | Portfolio | Notes |
|------|------|-----------|-------|

## Рынки

| Market | Size | Growth | Key Players |
|--------|------|--------|-------------|

## Открытые вопросы

1.

## Гипотезы

1.
'''

with open("/research/MEMORY.md", "w") as f:
    f.write(memory_md)
print("Created: /research/MEMORY.md")

print("\n=== Setup Complete ===")
print("To enable timers, run:")
print("  systemctl daemon-reload")
print("  systemctl enable --now founder-cron.timer")
print("  systemctl enable --now apartment-cron.timer")
