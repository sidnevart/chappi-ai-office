---
sidebar_position: 3
title: Настройка Mac
---

# Настройка Mac

Mac используется как рабочее место разработчика для управления AI Office. Основной агент работает на сервере.

## Claude Code

```bash
# Установка
npm install -g @anthropic/claude-code

# Настройка (введите API-ключ Anthropic)
claude
```

## Туннель к файлам Mac (cloudflared)

Позволяет агенту на сервере читать файлы с вашего Mac.

```bash
# Установка
brew install cloudflared

# Создайте папку для туннеля
mkdir -p ~/Documents/Projects/ai_office/tunnel
```

Создайте скрипт запуска `~/Documents/Projects/ai_office/tunnel/start.sh`:

```bash
#!/bin/bash
# Запускает локальный файловый сервер и туннель cloudflared
cd ~/Documents/Projects/ai_office
python3 -m http.server 18500 &
cloudflared tunnel --url http://localhost:18500 --no-autoupdate --protocol http2
```

Создайте агент запуска `~/Library/LaunchAgents/ai.aioffice.cloudflared.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.aioffice.cloudflared</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/cloudflared</string>
    <string>tunnel</string>
    <string>--url</string>
    <string>http://localhost:18500</string>
    <string>--no-autoupdate</string>
    <string>--protocol</string>
    <string>http2</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/cloudflared.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/cloudflared.err</string>
</dict>
</plist>
```

```bash
# Загрузить автозапуск
launchctl load ~/Library/LaunchAgents/ai.aioffice.cloudflared.plist

# Проверить статус
launchctl list | grep aioffice

# Получить URL туннеля (он меняется при каждом запуске)
cat /tmp/cloudflared.log | grep "trycloudflare.com"
```

**Важно:** URL туннеля меняется после каждого перезапуска. После перезапуска обновите `MAC_FILES_URL` в `.env` и в `AGENTS.md` на сервере.

## Файл переменных окружения

Создайте `~/Documents/Projects/ai_office/.env`:

```ini
OPENCLAW_TG_BOT=ВАШ_ТОКЕН_TELEGRAM
SERVER_USER=root
SERVER_IP=ВАШ_IP
SERVER_PASSWORD=ВАШ_ПАРОЛЬ
POSTGRES_PASSWORD=ВАШ_ПАРОЛЬ_POSTGRES
POSTGRES_USER=postgres
POSTGRES_DB=ai_office
POSTGRES_HOST=ВАШ_IP
POSTGRES_PORT=5432
MAC_FILESERVER_TOKEN=придумайте-токен-для-защиты
MAC_FILES_URL=https://ВАША-ССЫЛКА.trycloudflare.com
```

**Никогда не добавляйте `.env` в git!** Он уже есть в `.gitignore`.
