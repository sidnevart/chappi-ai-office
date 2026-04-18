# Chappi AI Office

Персональный ИИ-помощник на основе OpenClaw — работает круглосуточно на вашем сервере, общается через Telegram.

## Возможности

- **Всегда на связи** — работает на виртуальном сервере, не зависит от вашего компьютера
- **Личная база знаний** — PostgreSQL с pgvector, MemPalace для семантической памяти
- **Голосовые сообщения** — расшифровка через faster-Whisper локально на сервере
- **Мультиагентная работа** — инфраструктурный, исследовательский агенты и агент базы знаний
- **Интеграции** — Google Документы, Gmail, GitHub, Notion, Jira через Composio
- **Наблюдаемость** — Star Office UI (пиксельный дашборд) + Grafana

## Быстрый старт

Смотрите полную документацию: **[Руководство по настройке](docs-site/docs/setup-guide/prerequisites.md)**

Краткая схема:
1. Арендуйте VPS (Ubuntu 22.04, 4+ ГБ RAM)
2. Установите PostgreSQL, Ollama, Node.js на сервере
3. Установите и настройте OpenClaw (`npm install -g openclaw`)
4. Подключите Telegram-бота
5. Настройте Star Office UI и Grafana для наблюдаемости

## Архитектура

```
Telegram ←→ OpenClaw (VPS) ←→ Ollama (qwen3/glm-5/kimi-k2.5)
                ↓
         PostgreSQL + MemPalace (база знаний)
                ↓
         Composio (внешние сервисы)
```

## Дашборды

| Компонент | Назначение |
|-----------|-----------|
| [Star Office UI](:3000) | Визуальный статус агентов |
| [Grafana](:4000) | Метрики и аналитика |

## Структура репозитория

```
ai_office/
├── docs-site/          # Документация (Docusaurus)
├── .claude/
│   ├── agents/         # Субагенты Claude Code
│   ├── skills/         # Навыки Claude Code
│   └── hooks/          # Хуки безопасности
└── tunnel/             # Скрипты туннеля Mac → сервер
```

## Лицензия

MIT — используйте свободно, настраивайте под себя.

---

Сделано с любовью [@sidnevart](https://github.com/sidnevart)
