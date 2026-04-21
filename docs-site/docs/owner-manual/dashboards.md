---
sidebar_position: 2
title: Дашборды и наблюдаемость
---

# Дашборды и наблюдаемость

## OpenClaw Office UI (основной интерфейс)

**Адрес:** [https://80.74.25.43/](https://80.74.25.43/)

Основной веб-интерфейс для наблюдения за агентами и взаимодействия с OpenClaw. Работает через nginx reverse proxy с SSL.

### Что отображается

- **Состояние агентов** — текущий статус каждого из 4 агентов
- **Текущая задача** — краткое описание активной операции
- **Поток мыслей** — видно, что агент «думает» в процессе работы
- **WebSocket** — живое подключение к OpenClaw gateway

### Эндпоинты

| Адрес | Назначение |
|-------|-----------|
| `/` | Главная страница с состоянием агентов |
| `/control` | Панель управления (если включена) |
| `/gateway-ws` | WebSocket endpoint для живого подключения |

### Когда использовать

Основной интерфейс для наблюдения за работой агентов в реальном времени.

---

## Grafana

**Адрес:** [http://80.74.25.43:4000](http://80.74.25.43:4000) (логин: `admin`, пароль: `admin1`)

Профессиональный дашборд метрик и логов.

### Дашборд «AI Office Observability»

| Панель | Что показывает |
|--------|---------------|
| **OpenClaw ERROR Logs** | Логи с уровнем ERROR из `/tmp/openclaw/*.log` |
| **OpenClaw WARN Logs** | Логи с уровнем WARN из `/tmp/openclaw/*.log` |
| **OpenClaw INFO Logs** | Логи с уровнем INFO из `/tmp/openclaw/*.log` |
| **AI Office Agent Events** | События агентов из `event_log` (PostgreSQL) |
| **Agent Activity (7 days)** | Активность агентов по часам за 7 дней |

### Источники данных

| Источник | Тип | Что читает |
|----------|-----|-----------|
| **Loki** | Логи | Логи OpenClaw и системные логи |
| **PostgreSQL** | БД | Таблица `event_log` |
| **Prometheus** | Метрики | Системные метрики (node-exporter) |

Логи OpenClaw читаются из `/tmp/openclaw/*.log` через Promtail, который парсит JSON и извлекает уровень из `_meta.logLevelName`.

---

## Star Office UI (legacy)

**Адрес:** [http://80.74.25.43:3000](http://80.74.25.43:3000)

:::caution Устаревший интерфейс
Это пиксельный игровой интерфейс (Star Office UI). Он больше не является основным. Используйте [OpenClaw Office UI](https://80.74.25.43/) как основной интерфейс.
:::

---

## Просмотр базы знаний напрямую

```bash
# Последние 5 событий агентов
PGPASSWORD=postgres psql -h 80.74.25.43 -p 5432 -U postgres -d ai_office \
  -c "SELECT agent_id, state, task_summary, created_at FROM event_log ORDER BY created_at DESC LIMIT 5;"

# Активные задачи
PGPASSWORD=postgres psql -h 80.74.25.43 -p 5432 -U postgres -d ai_office \
  -c "SELECT title, priority, status FROM tasks WHERE status != 'done';"

# События за последние 24 часа
PGPASSWORD=postgres psql -h 80.74.25.43 -p 5432 -U postgres -d ai_office \
  -c "SELECT COUNT(*) FROM event_log WHERE created_at > NOW() - INTERVAL '24 hours';"
```