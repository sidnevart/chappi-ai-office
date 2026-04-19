#!/usr/bin/env bash
set -euo pipefail

LOCK=/run/openclaw-watchdog.lock
exec 9>"$LOCK"
flock -n 9 || exit 0

log() {
  echo "[openclaw-watchdog] $*" | systemd-cat -t openclaw-watchdog -p info
}

warn() {
  echo "[openclaw-watchdog] $*" | systemd-cat -t openclaw-watchdog -p warning
}

check_session_pressure() {
  local json
  if ! json="$(timeout 25 /usr/bin/openclaw sessions --json 2>/dev/null)"; then
    warn "openclaw sessions failed; skipping session pressure check"
    return 0
  fi

  SESSION_JSON="$json" node <<'NODE'
const data = JSON.parse(process.env.SESSION_JSON || "{}");
const warnPct = Number(process.env.OPENCLAW_SESSION_WARN_PCT || 80);
const rotatePct = Number(process.env.OPENCLAW_SESSION_ROTATE_PCT || 95);
const rotateRe = new RegExp(process.env.OPENCLAW_SESSION_ROTATE_KEYS_REGEX || "^agent:main:main$");
const sessions = Array.isArray(data.sessions) ? data.sessions : [];
let exitCode = 0;

for (const session of sessions) {
  const total = Number(session.totalTokens);
  const limit = Number(session.contextTokens);
  if (!Number.isFinite(total) || !Number.isFinite(limit) || limit <= 0) continue;
  const pct = Math.round((total / limit) * 100);
  const key = String(session.key || session.sessionId || "");
  if (pct >= warnPct) {
    console.log(`warn ${key} ${pct}% ${total}/${limit}`);
  }
  if (pct >= rotatePct && rotateRe.test(key)) {
    console.log(`rotate ${key} ${pct}% ${total}/${limit}`);
    exitCode = 2;
  }
}

process.exit(exitCode);
NODE
}

rotate_main_session() {
  warn "main session exceeded token pressure threshold; archiving and rotating"
  systemctl stop openclaw.service || true

  node <<'NODE'
const fs = require("fs");
const path = require("path");

const sessionDir = "/root/.openclaw/agents/main/sessions";
const storePath = path.join(sessionDir, "sessions.json");
const key = "agent:main:main";
const ts = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
const backupDir = path.join(sessionDir, "backups", `${ts}-watchdog-${key.replace(/[^a-zA-Z0-9_.-]/g, "-")}`);

fs.mkdirSync(backupDir, {recursive: true, mode: 0o700});
if (fs.existsSync(storePath)) {
  fs.copyFileSync(storePath, path.join(backupDir, "sessions.json"));
}

const store = fs.existsSync(storePath) ? JSON.parse(fs.readFileSync(storePath, "utf8")) : {};
const entry = store[key] || null;
const transcript = entry && typeof entry.sessionFile === "string"
  ? entry.sessionFile
  : path.join(sessionDir, `${key}.jsonl`);

if (fs.existsSync(transcript)) {
  fs.renameSync(transcript, path.join(backupDir, path.basename(transcript) + ".archived"));
}

if (Object.prototype.hasOwnProperty.call(store, key)) {
  delete store[key];
  const tmp = `${storePath}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(store, null, 2) + "\n", {mode: 0o600});
  fs.renameSync(tmp, storePath);
}

console.log(backupDir);
NODE

  systemctl start openclaw.service || true
  sleep 8
}

if ! /usr/local/sbin/openclaw-preflight.sh >/dev/null 2>&1; then
  warn "preflight failed; restarting openclaw.service anyway"
  systemctl restart openclaw.service || true
  exit 0
fi

if ! systemctl is-active --quiet openclaw.service; then
  warn "openclaw.service inactive; starting"
  systemctl start openclaw.service || true
  sleep 8
fi

if ! ss -ltnp | grep -q ":18789"; then
  warn "port 18789 is not listening; restarting openclaw.service"
  systemctl restart openclaw.service || true
  exit 0
fi

if ! timeout 25 /usr/bin/openclaw health >/tmp/openclaw-watchdog-health.out 2>&1; then
  warn "openclaw health failed; restarting openclaw.service"
  systemctl restart openclaw.service || true
  exit 0
fi

set +e
session_pressure="$(check_session_pressure 2>&1)"
session_pressure_status=$?
set -e
if [ -n "$session_pressure" ]; then
  while IFS= read -r line; do
    case "$line" in
      rotate\ *) warn "session pressure critical: ${line#rotate }" ;;
      warn\ *) warn "session pressure high: ${line#warn }" ;;
      *) warn "$line" ;;
    esac
  done <<< "$session_pressure"
fi

if [ "$session_pressure_status" -eq 2 ]; then
  rotate_main_session
  if ! timeout 25 /usr/bin/openclaw health >/tmp/openclaw-watchdog-health.out 2>&1; then
    warn "openclaw health failed after session rotation; restarting openclaw.service"
    systemctl restart openclaw.service || true
    exit 0
  fi
elif [ "$session_pressure_status" -ne 0 ]; then
  warn "session pressure check failed with status $session_pressure_status"
fi

log "ok"
