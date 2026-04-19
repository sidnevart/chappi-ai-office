---
name: gateway-health
description: >-
  OpenClaw gateway self-healing: device pairing issues, UI reconnecting loops,
  "1008 pairing required", gateway crash recovery, config validation errors,
  Telegram channel drop. Use when: dashboard shows "Disconnected", "pairing required",
  "reconnecting", gateway stops responding, bot goes silent, openclaw service restarts
  unexpectedly. Trigger phrases: "openclaw не отвечает", "dashboard reconnecting",
  "pairing required", "gateway упал", "бот молчит", "ui не подключается",
  "openclaw сломался". Runs diagnosis first, fixes second, never destructive without confirm.
tools: Bash, Read, Edit
model: sonnet
---

# Gateway Health & Self-Healing

## Diagnosis First — Always Run Full Check

```bash
GW_TOKEN=$(grep OPENCLAW_GATEWAY_TOKEN /root/.env 2>/dev/null | cut -d= -f2)

echo "=== 1. Service status ==="
systemctl is-active openclaw && echo "✅ openclaw running" || echo "❌ openclaw DOWN"
systemctl is-active ai-office-new-ui && echo "✅ new-ui running" || echo "❌ new-ui DOWN"
systemctl is-active openclaw-auto-approve.timer && echo "✅ auto-approve timer" || echo "❌ auto-approve timer OFF"

echo ""
echo "=== 2. Gateway port ==="
ss -tlnp | grep 18789 && echo "✅ port 18789 open" || echo "❌ port 18789 NOT listening"

echo ""
echo "=== 3. Pending devices (need approval) ==="
python3 -c "
import json
p = json.load(open('/root/.openclaw/devices/pending.json'))
print(f'Pending: {len(p)} device(s)')
for rid, d in p.items():
    print(f'  {rid[:8]}... platform={d.get(\"platform\")} client={d.get(\"clientId\")}')
"

echo ""
echo "=== 4. Last errors (5 min) ==="
journalctl -u openclaw --no-pager -n 30 --since "5 minutes ago" 2>/dev/null \
  | grep -v composio | grep -iE 'error|fail|blocked|token|auth' | tail -10

echo ""
echo "=== 5. Config validity ==="
openclaw config get gateway 2>/dev/null | grep -v composio | head -20

echo ""
echo "=== 6. Telegram channel ==="
python3 -c "
import json
cfg = json.load(open('/root/.openclaw/openclaw.json'))
tg = cfg.get('channels', {}).get('telegram', {})
print('enabled:', tg.get('enabled'))
print('token set:', bool(tg.get('botToken')))
"
```

---

## Fix 1: "pairing required" / "1008" / Dashboard Reconnecting

**Cause:** New browser session generated a device ID not yet in paired.json.

```bash
GW_TOKEN=$(grep OPENCLAW_GATEWAY_TOKEN /root/.env 2>/dev/null | cut -d= -f2)
PENDING_FILE=/root/.openclaw/devices/pending.json

PENDING_IDS=$(python3 -c "
import json
try:
    d = json.load(open('$PENDING_FILE'))
    [print(k) for k in d]
except: pass
")

if [ -z "$PENDING_IDS" ]; then
    echo "ℹ️ No pending devices — issue may be elsewhere"
else
    for RID in $PENDING_IDS; do
        openclaw devices approve "$RID" \
            --token "$GW_TOKEN" \
            --url ws://127.0.0.1:18789 2>/dev/null \
            && echo "✅ Approved: $RID" \
            || echo "❌ Failed: $RID"
    done
    echo "Done. Browser should reconnect within 30s."
fi
```

**Prevention check (auto-approve timer):**
```bash
systemctl is-active openclaw-auto-approve.timer \
    && echo "✅ Auto-approve timer active (runs every 30s)" \
    || (systemctl enable --now openclaw-auto-approve.timer && echo "✅ Enabled timer")
```

---

## Fix 2: Gateway Won't Start — "auth token not configured"

**Cause:** OPENCLAW_GATEWAY_TOKEN missing from /root/.env, or openclaw.json lost gateway.auth section.

```bash
# Check token in .env
grep OPENCLAW_GATEWAY_TOKEN /root/.env || echo "❌ TOKEN MISSING"

# Check openclaw.json has auth config
python3 -c "
import json
cfg = json.load(open('/root/.openclaw/openclaw.json'))
gw = cfg.get('gateway', {})
auth = gw.get('auth', {})
print('gateway.mode:', gw.get('mode'))
print('gateway.auth.mode:', auth.get('mode'))
print('gateway.auth.token set:', bool(auth.get('token')))
"
```

**Fix if token missing from openclaw.json:**
```bash
GW_TOKEN=$(grep OPENCLAW_GATEWAY_TOKEN /root/.env | cut -d= -f2)
python3 - <<EOF
import json
with open('/root/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
cfg.setdefault('gateway', {})['auth'] = {
    'mode': 'token',
    'token': '$GW_TOKEN'
}
cfg['gateway']['mode'] = 'local'
with open('/root/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
print("Fixed gateway.auth in openclaw.json")
EOF
systemctl restart openclaw
sleep 5
systemctl is-active openclaw && echo "✅ openclaw running" || echo "❌ still failing — check journalctl -u openclaw -n 30"
```

---

## Fix 3: Gateway Won't Start — "gateway.mode not set"

```bash
openclaw config set gateway.mode local 2>/dev/null | grep -v composio
systemctl restart openclaw
```

---

## Fix 4: Telegram Goes Silent (bot stops responding)

**Cause 1:** Telegram channel config lost from openclaw.json (happens after some updates).

```bash
python3 -c "
import json
cfg = json.load(open('/root/.openclaw/openclaw.json'))
print(json.dumps(cfg.get('channels', {}), indent=2))
"
```

**Fix — restore telegram channel:**
```bash
TG_TOKEN=$(grep OPENCLAW_TG_BOT /root/.env | cut -d= -f2)
python3 - <<EOF
import json
with open('/root/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
cfg.setdefault('channels', {})['telegram'] = {
    'enabled': True,
    'dmPolicy': 'pairing',
    'botToken': '$TG_TOKEN',
    'groupPolicy': 'allowlist',
    'streamMode': 'partial'
}
with open('/root/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
print("Telegram channel restored")
EOF
systemctl restart openclaw
sleep 6
journalctl -u openclaw --no-pager -n 5 | grep -i telegram
```

**Cause 2:** Gateway restart counter hit limit (too many crashes).
```bash
systemctl reset-failed openclaw
systemctl restart openclaw
```

---

## Fix 5: openclaw-office UI (port 3001) Not Starting

```bash
systemctl status ai-office-new-ui --no-pager -l | tail -20
journalctl -u ai-office-new-ui --no-pager -n 20 | tail -20
```

**Fix — restart UI service:**
```bash
systemctl restart ai-office-new-ui
sleep 3
systemctl is-active ai-office-new-ui && echo "✅ UI up on :3001" || echo "❌ still down"
```

---

## Fix 6: Config Validation Error (agents.list / heartbeat)

**Cause:** openclaw.json restored from partial backup has deprecated fields.

```bash
# Check for validation errors
openclaw config get agents 2>&1 | grep -v composio | head -30
```

**Fix — remove deprecated fields:**
```bash
python3 - <<'EOF'
import json

with open('/root/.openclaw/openclaw.json') as f:
    cfg = json.load(f)

agents = cfg.get('agents', {})

# Fix agents.list items: remove 'description', fix heartbeat
if 'list' in agents:
    fixed = []
    for a in agents['list']:
        a.pop('description', None)
        if isinstance(a.get('heartbeat'), bool):
            a['heartbeat'] = {'enabled': a['heartbeat']}
        fixed.append(a)
    agents['list'] = fixed
    cfg['agents'] = agents

with open('/root/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
print("Fixed deprecated fields in agents.list")
EOF

systemctl restart openclaw
```

---

## Full Reset (Last Resort)

Only if all fixes fail. Backs up current state first.

```bash
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak.$(date +%Y%m%d%H%M%S)
echo "Backup created"

# Verify backup
ls -la /root/.openclaw/openclaw.json.bak.*

# Then restore from working partial backup if exists
PARTIAL=$(ls -td /root/.openclaw.partial-* 2>/dev/null | head -1)
if [ -n "$PARTIAL" ]; then
    echo "Found partial backup: $PARTIAL"
    echo "Run: python3 /usr/local/sbin/restore-openclaw-config.py to restore"
else
    echo "No partial backup found — must rebuild config manually"
fi
```

---

## Known Failure Patterns

| Symptom | Cause | Fix |
|---------|-------|-----|
| Dashboard: "1008 pairing required" | New device not approved | Fix 1 |
| Gateway won't start: "token not configured" | Token missing from .env or openclaw.json | Fix 2 |
| Gateway won't start: "mode not set" | gateway.mode missing after update | Fix 3 |
| Bot silent, no telegram logs at startup | channels.telegram lost from openclaw.json | Fix 4 |
| Office UI shows "reconnecting" forever | Device pending + auto-approve timer off | Fix 1 + check timer |
| openclaw crashes in loop | restart counter limit | Fix 4 cause 2 |
| Config validation errors | Deprecated fields in agents.list | Fix 6 |
