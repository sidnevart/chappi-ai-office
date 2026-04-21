#!/usr/bin/env bash
set -euo pipefail

CONFIG="/root/.openclaw/openclaw.json"

log() {
  echo "[openclaw-preflight] $*"
}

if [[ -f "$CONFIG" ]]; then
  # OpenClaw 2026.2.x rejects these old keys. Remove them idempotently if they reappear.
  # Also strip deprecated agents.list[].description and agents.list[].heartbeat booleans.
  if node -e "
const fs=require('fs');
const p=process.argv[1];
const cfg=JSON.parse(fs.readFileSync(p,'utf8'));
let needsFix=false;
if (cfg.gateway && Object.prototype.hasOwnProperty.call(cfg.gateway,'url')) needsFix=true;
if (cfg.agents?.defaults?.subagents && Object.prototype.hasOwnProperty.call(cfg.agents.defaults.subagents,'enabled')) needsFix=true;
if (Array.isArray(cfg.agents?.list)) {
  for (const a of cfg.agents.list) {
    if (Object.prototype.hasOwnProperty.call(a,'description')) needsFix=true;
    if (Object.prototype.hasOwnProperty.call(a,'heartbeat')) needsFix=true;
  }
}
process.exit(needsFix ? 0 : 1);
" "$CONFIG"; then
    cp "$CONFIG" "$CONFIG.bak-$(date +%Y%m%d-%H%M%S)"
    node -e "
const fs=require('fs');
const p=process.argv[1];
const cfg=JSON.parse(fs.readFileSync(p,'utf8'));
if (cfg.gateway) delete cfg.gateway.url;
if (cfg.agents?.defaults?.subagents) {
  delete cfg.agents.defaults.subagents.enabled;
  if (Object.keys(cfg.agents.defaults.subagents).length===0) delete cfg.agents.defaults.subagents;
}
if (Array.isArray(cfg.agents?.list)) {
  for (const a of cfg.agents.list) {
    delete a.description;
    delete a.heartbeat;
  }
}
fs.writeFileSync(p, JSON.stringify(cfg,null,2)+'\n');
" "$CONFIG"
    log "removed stale OpenClaw config keys"
  fi
fi

# Prevent the per-user OpenClaw service from racing the system service on :18789.
if [[ -d /run/user/0 ]]; then
  XDG_RUNTIME_DIR=/run/user/0 systemctl --user disable --now openclaw-gateway.service >/dev/null 2>&1 || true
  XDG_RUNTIME_DIR=/run/user/0 systemctl --user mask openclaw-gateway.service >/dev/null 2>&1 || true
fi

/usr/bin/openclaw --version >/dev/null
