#!/usr/bin/env bash
# Chappi AI Office — установка на чистый VPS Ubuntu 22.04
#
# Использование:
#   1. Скопируй .env на VPS: scp .env root@YOUR_VPS_IP:/root/.env
#   2. На VPS: git clone git@github.com:sidnevart/chappi-ai-office.git /opt/ai-office/repo
#   3. На VPS: bash /opt/ai-office/repo/vps/setup.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE=/root/.env

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Не найден /root/.env — скопируй: scp .env root@VPS:/root/.env"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

echo "🚀 Chappi AI Office — установка на $(hostname)"

# ── Базовые пакеты ────────────────────────────────────────────────────────────
echo ""
echo "📦 Системные пакеты..."
apt-get update -qq
apt-get install -y curl git python3 python3-pip python3-venv ffmpeg gettext-base

# ── Node.js 20 ────────────────────────────────────────────────────────────────
echo ""
echo "📦 Node.js 20..."
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
node --version

# ── Python venv ───────────────────────────────────────────────────────────────
echo ""
echo "🐍 Python venv..."
VENV=/opt/ai-office/mempalace-venv
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet mempalace litellm "composio-core>=0.7" flask faster-whisper requests

# ── Docker ────────────────────────────────────────────────────────────────────
echo ""
echo "🐳 Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

# ── PostgreSQL + pgvector ──────────────────────────────────────────────────────
echo ""
echo "🗄️  PostgreSQL..."
cd "$REPO_DIR"
docker compose up -d postgres 2>/dev/null || docker-compose up -d postgres
echo "   ⏳ Ожидание готовности postgres..."
for i in {1..30}; do
  docker exec ai-office-postgres pg_isready -U postgres &>/dev/null && break || sleep 2
done
echo "   ✅ Postgres готов"

# Применить схему
docker exec -i ai-office-postgres psql -U postgres -d "${POSTGRES_DB:-ai_office}" \
  < "$REPO_DIR/vps/schema.sql" && echo "   ✅ Схема применена"

# ── Grafana ───────────────────────────────────────────────────────────────────
echo ""
echo "📊 Grafana..."
cd "$REPO_DIR"
docker compose up -d grafana 2>/dev/null || docker-compose up -d grafana

# ── Ollama ────────────────────────────────────────────────────────────────────
echo ""
echo "🤖 Ollama..."
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
systemctl enable --now ollama 2>/dev/null || true
sleep 3
ollama pull qwen3:8b || echo "   ⚠️  qwen3:8b недоступна"
echo "   ℹ️  Для cloud-моделей выполни: ollama signin"

# ── npm пакеты ────────────────────────────────────────────────────────────────
echo ""
echo "📦 npm global..."
npm install -g openclaw serve @ww-ai-lab/openclaw-office

# ── Star Office UI ────────────────────────────────────────────────────────────
echo ""
echo "🌟 Star Office UI..."
if [ ! -d /opt/ai-office/star-office ]; then
  git clone https://github.com/ringhyacinth/Star-Office-UI /opt/ai-office/star-office
fi

# ── Вспомогательные скрипты ───────────────────────────────────────────────────
echo ""
echo "📜 Скрипты..."
mkdir -p /opt/ai-office/voice /opt/ai-office/notify
cp "$REPO_DIR/vps/voice/transcribe.py" /opt/ai-office/voice/
cp "$REPO_DIR/vps/notify/notify.py"    /opt/ai-office/notify/
chmod +x /opt/ai-office/voice/transcribe.py /opt/ai-office/notify/notify.py
install -m 0755 "$REPO_DIR/vps/scripts/openclaw-preflight.sh" /usr/local/sbin/openclaw-preflight.sh
install -m 0755 "$REPO_DIR/vps/scripts/openclaw-watchdog.sh" /usr/local/sbin/openclaw-watchdog.sh
install -m 0755 "$REPO_DIR/vps/scripts/ai-office-postgres-firewall.sh" /usr/local/sbin/ai-office-postgres-firewall.sh

# ── Документация Docusaurus ───────────────────────────────────────────────────
echo ""
echo "📚 Документация..."
mkdir -p /opt/ai-office/docs
DOCS_SRC="$REPO_DIR/docs-site"
if [ -d "$DOCS_SRC" ]; then
  cd "$DOCS_SRC"
  npm install --silent
  npm run build
  cp -r build/. /opt/ai-office/docs/build/
  cd "$REPO_DIR"
fi

# ── OpenClaw workspace ────────────────────────────────────────────────────────
echo ""
echo "⚙️  OpenClaw workspace..."
mkdir -p /root/.openclaw/workspace/memory
AGENTS_TMPL="$REPO_DIR/.openclaw/workspace/AGENTS.md"
AGENTS_DEST="/root/.openclaw/workspace/AGENTS.md"
if [ ! -f "$AGENTS_DEST" ] && [ -f "$AGENTS_TMPL" ]; then
  envsubst < "$AGENTS_TMPL" > "$AGENTS_DEST"
  echo "   ✅ AGENTS.md создан из шаблона"
elif [ -f "$AGENTS_DEST" ]; then
  echo "   ℹ️  AGENTS.md уже существует, пропускаю"
fi

# ── MemPalace ─────────────────────────────────────────────────────────────────
echo ""
echo "🧠 MemPalace..."
"$VENV/bin/mempalace" init 2>/dev/null || true
"$VENV/bin/mempalace" mine /root/.openclaw/workspace 2>/dev/null || true

# ── systemd службы ────────────────────────────────────────────────────────────
echo ""
echo "⚙️  Systemd службы..."
SYSTEMD_SRC="$REPO_DIR/vps/systemd"
for svc in openclaw openclaw-watchdog ai-office-postgres-firewall ai-office-ui ai-office-docs ai-office-new-ui litellm; do
  src_file="$SYSTEMD_SRC/${svc}.service"
  if [ -f "$src_file" ]; then
    cp "$src_file" /etc/systemd/system/
  fi
done
if [ -f "$SYSTEMD_SRC/openclaw-watchdog.timer" ]; then
  cp "$SYSTEMD_SRC/openclaw-watchdog.timer" /etc/systemd/system/
fi
systemctl daemon-reload

for svc in openclaw ai-office-ui ai-office-docs ai-office-new-ui; do
  systemctl enable --now "$svc" 2>/dev/null \
    && echo "   ✅ $svc" \
    || echo "   ⚠️  $svc: проверь journalctl -u $svc"
done
systemctl enable --now openclaw-watchdog.timer 2>/dev/null \
  && echo "   ✅ openclaw-watchdog.timer" \
  || echo "   ⚠️  openclaw-watchdog.timer: проверь journalctl -u openclaw-watchdog"
systemctl enable --now ai-office-postgres-firewall.service 2>/dev/null \
  && echo "   ✅ ai-office-postgres-firewall.service" \
  || echo "   ⚠️  ai-office-postgres-firewall.service: проверь journalctl -u ai-office-postgres-firewall"

# ── Firewall ──────────────────────────────────────────────────────────────────
echo ""
echo "🔒 Firewall..."
if command -v ufw &>/dev/null; then
  ufw allow ssh     &>/dev/null
  ufw allow 3000/tcp &>/dev/null  # Star Office UI
  ufw allow 3001/tcp &>/dev/null  # OpenClaw Office UI
  ufw allow 4000/tcp &>/dev/null  # Grafana
  ufw allow 5000/tcp &>/dev/null  # Документация
  ufw --force enable &>/dev/null
  echo "   ✅ UFW настроен"
fi

# ── Итоговый отчёт ────────────────────────────────────────────────────────────
VPS_IP="${SERVER_IP:-$(curl -s ifconfig.me 2>/dev/null)}"
echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ Chappi AI Office установлен!"
echo ""
echo "🌐 Сервисы:"
echo "   Star Office UI:  http://${VPS_IP}:3000"
echo "   OpenClaw UI:     http://${VPS_IP}:3001"
echo "   Grafana:         http://${VPS_IP}:4000"
echo "   Документация:    http://${VPS_IP}:5000"
echo ""
echo "⚠️  Следующие шаги:"
echo "   1. ollama signin"
echo "      (для glm-5:cloud, kimi-k2.5:cloud)"
echo "   2. openclaw channels add telegram \\"
echo "      --token \$OPENCLAW_TG_BOT"
echo "   3. Проверь: systemctl status openclaw"
echo "═══════════════════════════════════════════════════"
