---
sidebar_position: 1
title: Предварительные требования
---

# Предварительные требования

Прежде чем начать, убедитесь что у вас есть всё необходимое.

## Что нужно купить / получить

### Виртуальный сервер

Рекомендуемые параметры:
- **ОС:** Ubuntu 22.04 LTS
- **Оперативная память:** минимум 4 ГБ (рекомендуется 8 ГБ)
- **Диск:** минимум 40 ГБ SSD
- **Процессор:** 2+ ядра

Проверенные провайдеры: Hetzner, DigitalOcean, Vultr, TimeWeb Cloud.

Нужен публичный IP-адрес для доступа к дашбордам.

### Аккаунт Telegram

- Создайте бота через [@BotFather](https://t.me/BotFather): `/newbot`
- Сохраните токен вида `123456789:AAEbL8...`
- Узнайте свой `chat_id`: отправьте сообщение боту [@userinfobot](https://t.me/userinfobot)

### Аккаунт Ollama Cloud

Нужен для использования облачных моделей (`glm-5:cloud`, `kimi-k2.6:cloud`):
- Зарегистрируйтесь на [ollama.com](https://ollama.com)
- Войдите через `ollama signin` на сервере

### Необязательно: Composio

Для интеграции с Google Документами, GitHub, Notion, Jira:
- Зарегистрируйтесь на [composio.dev](https://composio.dev)
- Получите потребительский ключ (`ck_...`) для OpenClaw

## Необходимые порты

Откройте в брандмауэре сервера:

| Порт | Назначение | Доступ |
|------|-----------|--------|
| 80 | HTTP → редирект на HTTPS | Публичный |
| 443 | OpenClaw Office UI (через nginx + SSL) | Публичный |
| 4000 | Grafana (метрики и логи) | Публичный |
| 3000 | Star Office UI (legacy, опционально) | Публичный |
| 5432 | PostgreSQL | Только внутренний |
| 11434 | Ollama | Только внутренний |
| 18789 | OpenClaw gateway | Только внутренний |

```bash
# Открыть порты через ufw
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 4000/tcp
ufw allow 3000/tcp  # legacy
```

:::note Docusaurus (порт 5000)
Порт 5000 используется только для локальной разработки документации на Mac. На VPS он не нужен.
:::

## Необходимое ПО на Mac (для управления)

- SSH-клиент (встроен в macOS)
- Claude Code: `npm install -g @anthropic/claude-code`
- cloudflared: `brew install cloudflared` (для туннеля Mac → сервер)
