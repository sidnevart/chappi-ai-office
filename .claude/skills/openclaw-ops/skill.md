---
name: openclaw-ops
description: >-
  OpenClaw / clawdbot orchestrator operations. Use when configuring the main
  orchestrator: checking which binary exists (openclaw vs clawdbot), setting up
  the Telegram channel, enabling plugins, configuring model routing tiers,
  restarting the service, reading or editing openclaw/clawdbot config files.
  Trigger phrases: "настрой openclaw", "clawdbot config", "подключи телеграм",
  "model routing", "плагины openclaw". Always verify the real binary name first.
  Do NOT use for: ollama model management (use ollama-ops), VPS infra (use vps-ops).
tools: Bash, Read, Edit, Write
model: sonnet
---

# OpenClaw / clawdbot Operations

## Step 0: Identify Binary (ALWAYS run first)
```bash
BINARY=""
which openclaw 2>/dev/null && BINARY="openclaw" && echo "Found: openclaw"
[ -z "$BINARY" ] && which clawdbot 2>/dev/null && BINARY="clawdbot" && echo "Found: clawdbot"
[ -z "$BINARY" ] && echo "ERROR: neither openclaw nor clawdbot found in PATH" && exit 1
echo "Active binary: $BINARY"
$BINARY --version 2>/dev/null || $BINARY version 2>/dev/null || echo "version command not supported"
$BINARY --help 2>&1 | head -50
```

## Step 1: Inspect Existing Config
```bash
$BINARY config show 2>/dev/null || \
  cat ~/.openclaw/config.yaml 2>/dev/null || \
  cat ~/.clawdbot/config.yaml 2>/dev/null || \
  echo "No config found — will create from scratch"
```

## Step 2: Telegram Channel Setup
- Token: read from `.env` as `$OPENCLAW_TG_BOT` — never hardcode
- Set up read-only channel first, write-access only after confirmation
```bash
source /Users/artemsidnev/Documents/Projects/ai_office/.env
$BINARY config set telegram.token "$OPENCLAW_TG_BOT" 2>/dev/null || \
  echo "Manual config needed — check $BINARY --help config"
```

## Step 3: Model Routing Config
Map to three tiers before applying:
- `light`  = `qwen3.5:cloud`   — fast tasks, summaries, routing decisions
- `medium` = `glm-5:cloud`     — analysis, code drafts, structured tasks
- `heavy`  = `kimi-k2.6:cloud` — complex research, long-context coding

Show diff before applying any config change.

## Step 4: Backup + Restart Pattern
```bash
# Backup current config
cp ~/.openclaw/config.yaml ~/.openclaw/config.yaml.bak 2>/dev/null || true
# Validate before restart
$BINARY config validate 2>/dev/null || echo "No validate command — check manually"
# Restart
$BINARY restart 2>/dev/null || systemctl restart $BINARY 2>/dev/null || echo "Manual restart needed"
```

## Safety Rules
- Weak models (light tier) NEVER get write-access to repos or external APIs
- All config changes: show diff first, confirm, then apply
- Always keep `.bak` of config before changes
- Report: done/pending/blocked after each major step
