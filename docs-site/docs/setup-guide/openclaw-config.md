---
sidebar_position: 4
title: Настройка OpenClaw
---

# Настройка OpenClaw

## Установка на сервере

```bash
ssh root@ВАШ_IP

# Установить Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Установить OpenClaw
npm install -g openclaw

# Проверить
openclaw --version
```

## Настройка Telegram-канала

```bash
openclaw channels add telegram --token ВАШ_ТОКЕН_БОТА
openclaw channels list  # проверить
```

## Настройка псевдонимов моделей

```bash
openclaw models aliases add light ollama/qwen3:8b
openclaw models aliases add medium ollama/glm-5:cloud
openclaw models aliases add heavy ollama/kimi-k2.5:cloud

# Проверить
openclaw models aliases list
```

## Systemd-служба

Создайте `/etc/systemd/system/openclaw.service`:

```ini
[Unit]
Description=OpenClaw AI Office Gateway
After=network.target ollama.service

[Service]
Type=simple
ExecStart=/usr/bin/openclaw gateway --force --port 18789
Restart=on-failure
RestartSec=10
WorkingDirectory=/root
Environment=OPENCLAW_TG_BOT=ВАШ_ТОКЕН
Environment=OLLAMA_HOST=http://localhost:11434
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB=ai_office
Environment=POSTGRES_USER=postgres
Environment=POSTGRES_PASSWORD=ВАШ_ПАРОЛЬ

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable openclaw
systemctl start openclaw
systemctl status openclaw
```

## Файл AGENTS.md

Скопируйте файл `ai_office/.openclaw/workspace/AGENTS.md` из этого репозитория на сервер:

```bash
scp ai_office/.openclaw/workspace/AGENTS.md root@ВАШ_IP:/root/.openclaw/workspace/AGENTS.md
```

Обновите в нём адрес PostgreSQL на `localhost` (вместо внешнего IP):

```bash
# На сервере
sed -i 's/PGPASSWORD=postgres psql -h 80.74.25.43/PGPASSWORD=postgres psql -h localhost/g' \
  /root/.openclaw/workspace/AGENTS.md
```

## Проверка работы

Отправьте сообщение боту в Telegram. Бот должен ответить в течение 10 секунд.

Если нет ответа:
```bash
journalctl -u openclaw -n 20 --no-pager
```
