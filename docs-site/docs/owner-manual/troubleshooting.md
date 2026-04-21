---
sidebar_position: 8
title: Устранение неполадок
---

# Устранение неполадок

## Бот не отвечает

**Проверьте состояние OpenClaw:**
```bash
ssh root@80.74.25.43
systemctl status openclaw
journalctl -u openclaw -n 50
```

**Типичные причины:**
- OpenClaw упал — `systemctl restart openclaw`
- Ollama не запущен — `systemctl restart ollama`
- Проблема с токеном Telegram — проверьте `OPENCLAW_TG_BOT` в `/etc/systemd/system/openclaw.service`
- Невалидный конфиг — запустите `openclaw doctor --fix`

---

## OpenClaw Office UI недоступен (https://80.74.25.43/)

```bash
# Проверить nginx
systemctl status nginx
nginx -t

# Проверить, что UI бэкенд работает
ss -tlnp | grep -E '3001|18789'

# Проверить WebSocket
curl -s -k -H 'Upgrade: websocket' -H 'Connection: Upgrade' \
  https://localhost/gateway-ws
# Ожидаем: 400 (нормально — неполный WS handshake)

# Перезапуск
systemctl restart nginx
```

**Типичные причины:**
- nginx не запущен или сломан конфиг
- OpenClaw gateway на порту 18789 недоступен
- SSL-сертификат просрочен

---

## Star Office UI (legacy, порт 3000)

:::caution Устаревший интерфейс
Star Office UI больше не является основным. Используйте [OpenClaw Office UI](https://80.74.25.43/).
:::

```bash
systemctl status ai-office-ui
journalctl -u ai-office-ui -n 30
systemctl restart ai-office-ui
```

---

## Grafana недоступна (порт 4000)

```bash
docker ps | grep grafana
docker logs ai-office-grafana --tail 30
docker restart ai-office-grafana
```

**Проблема с PostgreSQL datasource:**
```bash
# Проверить пароль postgres
docker exec ai-office-postgres psql -U postgres -c 'SELECT 1;'

# Если ошибка авторизации — сбросить пароль
docker exec -u postgres ai-office-postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

---

## openclaw-control сервисы

```bash
# Проверить webhook server
systemctl status openclaw-control-webhook
journalctl -u openclaw-control-webhook -n 30

# Проверить monitoring
systemctl status openclaw-control-monitoring
journalctl -u openclaw-control-monitoring -n 30

# Перезапуск
systemctl restart openclaw-control-webhook
systemctl restart openclaw-control-monitoring
```

---

## Approval gate: задача "застряла"

Если спека или PR digest ожидает approval, но уведомление не пришло:

```bash
# Посмотреть список на approval
/opt/openclaw-control/scripts/oc-approval list

# Одобрить вручную
/opt/openclaw-control/scripts/oc-approval approve spec-pvti_42

# Проверить state файлы
ls -la /opt/openclaw-control/.runtime/approvals/
cat /opt/openclaw-control/.runtime/approvals/spec-pvti_42.json
```

---

## Туннель Mac → сервер не работает

Туннель cloudflared запускается на вашем Mac и открывает доступ к файлам Mac с сервера.

```bash
# На Mac — проверить статус
launchctl list | grep aioffice

# Перезапустить
launchctl unload ~/Library/LaunchAgents/ai.aioffice.cloudflared.plist
launchctl load ~/Library/LaunchAgents/ai.aioffice.cloudflared.plist
```

После перезапуска туннеля URL изменится. Обновите `MAC_FILES_URL` в `.env` и в `AGENTS.md` на сервере.

---

## Расшифровка голоса не работает

```bash
ssh root@80.74.25.43
# Проверить модель
ls /root/.cache/huggingface/

# Тест вручную
echo "test" | python3 -c "from faster_whisper import WhisperModel; print('OK')"
```

---

## Ошибка подключения к PostgreSQL

```bash
# Проверить контейнер
docker ps | grep postgres
docker logs ai-office-postgres --tail 20

# Тест подключения
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d ai_office -c "SELECT 1;"
```

---

## Composio инструменты не работают

Убедитесь что используется правильный ключ — потребительский ключ (формат `ck_...`):

```bash
echo $COMPOSIO_TOKEN_OPENCLAW  # должен начинаться с ck_
```

Если ключ неверный, обновите его в настройках openclaw и в systemd-службе.

---

## Просмотр всех журналов

```bash
# OpenClaw
journalctl -u openclaw -f

# Star Office UI
journalctl -u ai-office-ui -f

# Все сервисы AI Office
journalctl -u openclaw -u ai-office-ui -u ollama -f
```
