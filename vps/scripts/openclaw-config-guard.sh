#!/usr/bin/env bash
# Ensure openclaw.json has all required sections before gateway starts.
# Run as ExecStartPre in openclaw.service.
set -euo pipefail

CONFIG=/root/.openclaw/openclaw.json
ENV_FILE=/root/.env

[ -f "$ENV_FILE" ] && source "$ENV_FILE" || true

TG_TOKEN="${OPENCLAW_TG_BOT:-}"
GW_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"

python3 - << PYEOF
import json, sys

with open("$CONFIG") as f:
    cfg = json.load(f)

changed = False

# 1. gateway.mode must be "local"
gw = cfg.setdefault("gateway", {})
if gw.get("mode") != "local":
    gw["mode"] = "local"; changed = True
if gw.get("bind") not in ("lan", "tailnet", "auto", "custom"):
    gw["bind"] = "lan"; changed = True
gw.setdefault("auth", {})
if not gw["auth"].get("token") and "$GW_TOKEN":
    gw["auth"] = {"mode": "token", "token": "$GW_TOKEN"}; changed = True

# 2. hooks.internal must exist (required for Telegram to start)
hooks = cfg.setdefault("hooks", {})
if "internal" not in hooks:
    hooks["internal"] = {"enabled": True, "entries": {"session-memory": {"enabled": True}}}
    changed = True

# 3. channels.telegram must be enabled with token
tg_token = "$TG_TOKEN"
if tg_token:
    tg = cfg.setdefault("channels", {}).setdefault("telegram", {})
    if not tg.get("enabled") or not tg.get("botToken"):
        tg.update({
            "enabled": True,
            "dmPolicy": "pairing",
            "botToken": tg_token,
            "groupPolicy": "allowlist",
            "streamMode": "partial"
        })
        changed = True

if changed:
    with open("$CONFIG", "w") as f:
        json.dump(cfg, f, indent=2)
    print("[config-guard] Fixed openclaw.json")
else:
    print("[config-guard] Config OK")
PYEOF
