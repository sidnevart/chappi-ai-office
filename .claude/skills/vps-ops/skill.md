---
name: vps-ops
description: >-
  VPS operations for AI Office — SSH access, Docker service management,
  deploying postgres/pgvector container, setting up systemd services, checking
  open ports and service health on the remote server. Trigger phrases: "деплой
  на VPS", "SSH", "запусти docker", "postgres на сервере", "проверь сервисы".
  ALWAYS prints the command before executing. ALWAYS confirms before destructive ops.
  Do NOT use for: local Docker (use infra-agent), ollama model management (ollama-ops).
tools: Bash, Read
model: sonnet
---

# VPS Operations

## Load Credentials (never hardcode)
```bash
source /Users/artemsidnev/Documents/Projects/ai_office/.env
# Uses: SERVER_USER, SERVER_IP (or SERVER_HOST), SERVER_PASSWORD from .env
# If SERVER_IP not set, ask user
```

## 1. Test Connectivity
Always run first:
```bash
echo "Connecting to $SERVER_USER@$SERVER_IP..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
  "$SERVER_USER@$SERVER_IP" "echo '✅ Connected' && uname -a && uptime"
```

## 2. Check Running Services on VPS
```bash
ssh "$SERVER_USER@$SERVER_IP" "
  echo '=== Docker containers ===' && docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'docker not installed';
  echo '=== Listening ports ===' && ss -tlnp 2>/dev/null | grep LISTEN | head -20;
  echo '=== Disk ===' && df -h / 2>/dev/null;
  echo '=== RAM ===' && free -h 2>/dev/null;
"
```

## 3. Deploy Postgres + pgvector
Show this command before running, confirm first:
```bash
ssh "$SERVER_USER@$SERVER_IP" "
  docker ps -a --filter name=ai-office-postgres --format '{{.Names}}' | grep -q ai-office-postgres \
    && echo 'postgres already running' \
    || docker run -d \
        --name ai-office-postgres \
        --restart unless-stopped \
        -e POSTGRES_PASSWORD=\$POSTGRES_PASSWORD \
        -e POSTGRES_DB=ai_office \
        -p 5432:5432 \
        pgvector/pgvector:pg16 \
    && echo '✅ postgres deployed'
"
```

## 4. Deploy Ollama on VPS (if needed)
```bash
ssh "$SERVER_USER@$SERVER_IP" "
  which ollama && echo 'ollama already installed' \
    || (curl -fsSL https://ollama.com/install.sh | sh && echo '✅ ollama installed')
"
```

## 5. Service Health Check
```bash
ssh "$SERVER_USER@$SERVER_IP" "
  docker ps --filter name=ai-office --format '{{.Names}}: {{.Status}}'
"
```

## Safety Rules
1. Print every SSH command before running
2. Destructive ops (docker rm, rm -rf): STOP and confirm with user first
3. Never print credentials to output
4. On failure: show exit code + last 10 lines of stderr
5. After deploy: always run health check

## Report Format
```
=== VPS Status ===
Host: $SERVER_IP
✅ postgres: running (port 5432)
❌ ollama: not found
⏳ openclaw: pending setup
Next: [action]
```
