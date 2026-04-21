# Chappi AI Office

Персональный ИИ-помощник на основе OpenClaw — работает круглосуточно на вашем сервере, общается через Telegram.

## Возможности

- **Всегда на связи** — работает на VPS, не зависит от вашего компьютера
- **Личная база знаний** — PostgreSQL с pgvector, MemPalace для семантической памяти
- **Голосовые сообщения** — расшифровка через faster-Whisper локально на сервере
- **Мультиагентная работа** — инфраструктурный, исследовательский агенты и агент базы знаний
- **Интеграции** — Gmail, Google Calendar, GitHub, Notion, Jira через Composio
- **Наблюдаемость** — Star Office UI (пиксельный дашборд) + OpenClaw Office UI + Grafana

## Быстрый старт

### Требования

- VPS Ubuntu 22.04, 4+ ГБ RAM (рекомендуется 8+ ГБ для Ollama)
- Telegram-бот (создаётся у @BotFather)
- Аккаунт Ollama (для cloud-моделей glm-5, kimi-k2.6)

### Установка

```bash
# 1. Клонировать репозиторий
git clone git@github.com:sidnevart/chappi-ai-office.git
cd chappi-ai-office

# 2. Заполнить переменные окружения
cp .env.example .env
# Отредактируй .env: токен Telegram, IP сервера, пароль БД и т.д.

# 3. Скопировать .env на VPS и запустить установку
scp .env root@YOUR_VPS_IP:/root/.env
ssh root@YOUR_VPS_IP "bash -s" < vps/setup.sh
```

После установки:
```bash
# На VPS — завершить настройку вручную:
ollama signin                              # для cloud-моделей
openclaw channels add telegram --token $OPENCLAW_TG_BOT
```

Подробное руководство: **[docs-site/docs/setup-guide/prerequisites.md](docs-site/docs/setup-guide/prerequisites.md)**

## Архитектура

```
Telegram ←→ OpenClaw (VPS :18789) ←→ Ollama (qwen3/glm-5/kimi-k2.6)
                ↓
         PostgreSQL + MemPalace (база знаний)
                ↓
         Composio (внешние сервисы)
```

## Дашборды

| Компонент | Порт | Назначение |
|-----------|------|-----------|
| Star Office UI | :3000 | Пиксельный визуальный статус агентов |
| OpenClaw Office UI | :3001 | BigTech изометрический офис |
| Grafana | :4000 | Метрики и аналитика |
| Документация | :5000 | Руководства владельца и по настройке |

## Структура репозитория

```
chappi-ai-office/
├── .env.example              # Шаблон переменных окружения
├── docker-compose.yml        # PostgreSQL + Grafana
├── docs-site/                # Документация (Docusaurus)
│   └── docs/
│       ├── owner-manual/     # Руководство владельца (8 статей)
│       └── setup-guide/      # Руководство по настройке (11 статей)
├── vps/
│   ├── setup.sh              # Скрипт установки на чистый VPS
│   ├── schema.sql            # Схема PostgreSQL (9 таблиц + pgvector)
│   ├── systemd/              # Шаблоны systemd-служб
│   ├── star-office/          # Flask Blueprint для AI Office роутов
│   ├── voice/                # Транскрипция голосовых (Whisper)
│   └── notify/               # Telegram-уведомления
├── .openclaw/
│   └── workspace/AGENTS.md  # Шаблон инструкций для агента
├── .claude/
│   ├── agents/               # Субагенты Claude Code
│   ├── skills/               # Навыки Claude Code (slash commands)
│   └── hooks/                # Хуки безопасности
└── tunnel/                   # Скрипты туннеля Mac → сервер
```

## Лицензия

MIT — используйте свободно, настраивайте под себя.

---

Сделано с любовью [@sidnevart](https://github.com/sidnevart)
