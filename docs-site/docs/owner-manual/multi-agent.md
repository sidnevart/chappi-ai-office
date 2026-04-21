---
sidebar_position: 5
title: Мультиагентная работа
---

# Мультиагентная работа

Chappi AI Office поддерживает параллельную работу нескольких специализированных агентов. Каждый агент имеет свою роль, модель и набор навыков.

## Типы агентов

| Агент | Специализация | Модель | Когда запускается |
|-------|--------------|--------|------------------|
| **main** (office-controller) | Приём входящих, общение, маршрутизация | `ollama/kimi-k2.6:cloud` | Всегда активен |
| **sdlc-orchestrator** | Подготовка спек, бутстрап веток | `heavy` (kimi-k2.6:cloud) | При задачах из GitHub Project |
| **coder-runner** | Написание кода, тесты, PR | `heavy` (kimi-k2.6:cloud) | После одобрения спеки |
| **review-watcher** | Мониторинг CI, PR дайджесты | `medium` (glm-5:cloud) | После открытия PR |

## Как агенты взаимодействуют

Агенты не работают изолированно — они передают задачи друг другу через durable state и shared PostgreSQL:

1. **sdlc-orchestrator** подготавливает спеку → публикует на approval
2. После одобрения → **sdlc-orchestrator** бутстрапит ветку → создаёт job для **coder-runner**
3. **coder-runner** пишет код → создаёт PR → уведомляет **review-watcher**
4. **review-watcher** мониторит CI → публикует PR digest → уведомляет в Telegram

Подробнее о SDLC workflow читайте в [SDLC-агенты и рабочий процесс](./sdlc-workflow).

## Как запустить субагента

Просто попросите в Telegram:

```
Запусти sdlc-orchestrator для задачи #42
Попроси coder-runner реализовать одобренную спеку
review-watcher: проверь статус CI для PR #123
```

Основной агент (`main`) сам решает, когда делегировать задачу специализированному субагенту. Делегация происходит через OpenClaw gateway — агент создаёт новую сессию с нужным namespace.

## Отображение в дашбордах

### OpenClaw Office UI (основной)

Состояние всех 4 агентов транслируется автоматически через WebSocket (`/gateway-ws`). Дополнительных вызовов не требуется.

### Grafana

События всех агентов записываются в `event_log` (PostgreSQL) и отображаются на дашборде «AI Office Observability».

## Общая база знаний

Все агенты работают с одной и той же базой данных PostgreSQL. Это значит:

- **sdlc-orchestrator** сохраняет спеку → **coder-runner** видит её
- **coder-runner** создаёт PR → **review-watcher** начинает мониторинг
- **review-watcher** логирует событие CI → в Grafana появляется запись
- **main** может в любой момент спросить статус любого job

## Durable state

Каждый агент хранит своё состояние в durable-формате:

| Агент | Где хранит state | Namespace |
|-------|-------------------|-----------|
| main | PostgreSQL + chat context | `main/<timestamp>` |
| sdlc-orchestrator | `openclaw-control/.runtime/job_state_v1.json` | `sdlc-orchestrator/<job_id>/<timestamp>` |
| coder-runner | `openclaw-control/.runtime/job_state_v1.json` | `coder-runner/<job_id>/<timestamp>` |
| review-watcher | `openclaw-control/.runtime/job_state_v1.json` | `review-watcher/<pr_id>/<timestamp>` |

При перезапуске OpenClaw агенты читают `job_state_v1.json` и возобновляют работу с последнего известного состояния.

## Ограничения

- Субагенты работают в рамках одного процесса OpenClaw gateway
- Параллельность ограничена `agents.defaults.maxConcurrent` (по умолчанию 4)
- Каждый субагент работает в своём namespace и не может читать контекст другого агента напрямую
- Для передачи данных между агентами используется `cross-agent-handoff-writer` skill и shared PostgreSQL
