#!/usr/bin/env bash
set -euo pipefail

CONFIG="/root/.openclaw/openclaw.json"

log() {
  echo "[openclaw-preflight] $*"
}

if [[ -f "$CONFIG" ]]; then
  # OpenClaw 2026.2.x rejects this old key. Remove it idempotently if it reappears.
  if node -e "const fs=require('fs'); const p=process.argv[1]; const cfg=JSON.parse(fs.readFileSync(p,'utf8')); process.exit(cfg.gateway && Object.prototype.hasOwnProperty.call(cfg.gateway,'url') ? 0 : 1)" "$CONFIG"; then
    cp "$CONFIG" "$CONFIG.bak-$(date +%Y%m%d-%H%M%S)"
    node -e "const fs=require('fs'); const p=process.argv[1]; const cfg=JSON.parse(fs.readFileSync(p,'utf8')); delete cfg.gateway.url; fs.writeFileSync(p, JSON.stringify(cfg,null,2)+'\n')" "$CONFIG"
    log "removed stale gateway.url"
  fi
fi

# Prevent the per-user OpenClaw service from racing the system service on :18789.
if [[ -d /run/user/0 ]]; then
  XDG_RUNTIME_DIR=/run/user/0 systemctl --user disable --now openclaw-gateway.service >/dev/null 2>&1 || true
  XDG_RUNTIME_DIR=/run/user/0 systemctl --user mask openclaw-gateway.service >/dev/null 2>&1 || true
fi

/usr/bin/openclaw --version >/dev/null
