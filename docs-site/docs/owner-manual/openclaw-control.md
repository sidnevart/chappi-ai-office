---
sidebar_position: 3
title: Панель управления — openclaw-control
---

# openclaw-control

`openclaw-control` — это production-oriented control plane («панель управления»), которая сидит рядом с OpenClaw и отвечает за безопасность, durability и оркестрацию рабочих процессов.

## Зачем это нужно

OpenClaw сам по себе — это мощный агент, но у него нет встроенных механизмов:

- **Явного контроля side effects** — он может написать код, создать PR или перезапустить сервис без подтверждения
- **Durable state** — при перезапуске агента теряется контекст текущих задач
- **Approval gates** — нет встроенного механизма «одобрить перед выполнением»
- **Управления навыками** — нет централизованного каталога, кто какой skill может использовать

`openclaw-control` решает эти проблемы, добавляя слой безопасности и оркестрации поверх OpenClaw.

## Приоритеты control plane

1. **Side effects явны** — любая опасная операция сначала показывается в режиме dry-run
2. **Approval перед изменениями** — risky mutations требуют явного одобрения
3. **Секреты вне git** — токены, пароли и приватные URL хранятся только в `.env`
4. **Durable state важнее памяти чата** — состояние задач хранится в файлах и БД, не в контексте модели
5. **Навыки маленькие и ролевые** — каждый skill отвечает за одну вещь и загружается только нужному агенту

## Что предоставляет

### Ops toolbelt — скрипты для операций

| Скрипт | Что делает |
|--------|-----------|
| `oc-audit` | Проверяет состояние control plane: целостность state, наличие секретов, работа сервисов |
| `oc-rollout` | Выкатывает изменения: `--env local` или `--env vps`, с `--dry-run` по умолчанию |
| `oc-rollback` | Откатывает последний rollout к предыдущей версии |
| `oc-verify` | Проверяет, что текущая конфигурация соответствует ожидаемой |
| `oc-cleanup` | Удаляет устаревший state, временные файлы, deadlocks |
| `oc-preflight` | Подготовка перед запуском: чистка stale config keys, валидация |
| `oc-state-validate` | Валидирует JSON state-файлы по schemas |

### SDLC-оркестрация

| Скрипт | Что делает |
|--------|-----------|
| `oc-sdlc sync` | Синхронизирует GitHub Project с внутренним job state |
| `oc-sdlc-from-github-webhook` | Обрабатывает webhook от GitHub Projects v2 |
| `oc-spec-publish` | Публикует спеку на ревью |
| `oc-spec-deliver` | Доставляет одобренную спеку в очередь на реализацию |
| `oc-approval list` | Показывает список задач, ожидающих approval |
| `oc-approval approve` | Одобряет задачу (например, спеку или PR digest) |
| `oc-approval reject` | Отклоняет задачу с причиной |

### Жизненный цикл исследований

| Скрипт | Что делает |
|--------|-----------|
| `oc-research` | Запускает intake interview для нового исследования |
| `oc-research start-interview` | Собирает требования: источники, фильтры, формат вывода |
| `oc-research create-job` | Создаёт durable research job с планом |
| `oc-research pause/resume/stop` | Управляет состоянием исследовательской задачи |

### GitHub Projects

| Скрипт | Что делает |
|--------|-----------|
| `oc-github-project create-task` | Создаёт задачу в GitHub Project |
| `oc-github-project set-status` | Меняет статус задачи |
| `oc-github-project-normalize` | Нормализует внешние идентификаторы во внутренний формат |

### Хуки и алерты

| Скрипт | Что делает |
|--------|-----------|
| `oc-hook-run` | Запускает hook по ID из registry |
| `oc-hook-test` | Тестирует hook на fixture-данных |
| `oc-alert-route` | Маршрутизирует алерты по severity в нужные каналы Telegram |
| `oc-alert-test` | Отправляет тестовый алерт для проверки доставки |

## Approval classes: кто что может делать

В `openclaw-control/policies/approvals.yaml` определены 4 класса операций:

### Automatic — выполняется автоматически

- Read-only инспекции (просмотр логов, проверка статуса)
- Static validation и schema checks
- Черновики спек и исследовательских summary

### Dry-run only — только просмотр изменений

- Config diffs (`oc-rollout --dry-run`)
- Hook diffs
- systemd diffs
- SQL и Docker change previews
- Предпросмотр установки/удаления skills

### Dry-run + explicit approval — просмотр + ручное подтверждение

- Изменения `openclaw.json`
- Изменения `AGENTS.md`, `IDENTITY.md`, `SKILLS.md`
- Изменения обработчиков хуков
- Создание/обновление/удаление systemd-юнитов
- `git push`, создание PR, доставка в Telegram группы
- Shell-команды с side effects (сервисы, файлы, БД, сеть)

### Never automatic — никогда автоматически

- Извлечение секретов
- Деструктивное удаление данных без бэкапа
- Merge, close, reopen PR или удаление ветки
- Отключение алертов или политик approval

## Структура директорий

### На VPS

```
/opt/openclaw-control/
├── scripts/           # Все oc-* скрипты
├── lib/               # Python-библиотеки (state_validate.py, webhook_server.py, ...)
├── hooks/             # Обработчики хуков (github-project-sync.sh, alert-route.sh, ...)
├── hooks/registry.yaml # Реестр хуков с approval_class и timeout
├── policies/          # approval-matrix, dry-run rules, routing, alert-severity
├── schemas/           # JSON schemas для state (job_state_v1, approval_state_v1, ...)
├── systemd/templates/ # Шаблоны systemd-юнитов
├── nginx/templates/   # Шаблоны nginx-конфигов
├── docs/              # Документация control plane (hook-contracts, skills-strategy, ...)
├── skills/            # OpenClaw-специфичные skills
│   ├── references/    # Общие референсы (sdlc-lifecycle, research-lifecycle)
│   └── */SKILL.md     # Отдельные skills
├── .runtime/          # Durable state
│   ├── specs/         # Спеки в Markdown и JSON
│   ├── approvals/     # Approval state
│   ├── outbox/        # Исходящие доставки
│   └── events/        # JSONL-логи событий для Promtail
├── tests/             # Smoke tests и fixtures
└── examples/          # Примеры конфигураций
```

### Локально (Mac)

```
~/.openclaw/control-plane/
├── scripts/           # Симлинки или копии oc-* скриптов
├── policies/          # Те же политики, что и на VPS
├── schemas/           # Те же schemas
└── .runtime/          # Локальный state (не публикуется на VPS автоматически)
```

## Local vs VPS

| Аспект | Local (Mac) | VPS |
|--------|-------------|-----|
| **Env файлы** | В папке проекта, не требуют root | `/opt/openclaw-control/.env`, root-owned |
| **Alerts** | Dry-run по умолчанию | Telegram alerting включён |
| **Side effects** | Локальное подтверждение | Требуется approval gate |
| **Отладка** | Прямые логи, local compose | Docker Compose, journalctl |
| **Rollout** | `oc-rollout --env local control-plane` | `oc-rollout --env vps control-plane` |
| **State** | `~/.openclaw/control-plane/.runtime` | `/opt/openclaw-control/.runtime` |
| **Systemd** | Нет | `openclaw.service`, `openclaw-control-webhook.service`, `openclaw-control-monitoring.service` |

## Связь со skills

Навыки делятся на два уровня:

### 1. Superpowers foundation (`.claude/skills/`)

Общие методологические навыки, синхронизируемые из `obra/superpowers`:

- `brainstorming`, `writing-plans`, `executing-plans`
- `subagent-driven-development`, `test-driven-development`
- `requesting-code-review`, `receiving-code-review`
- `systematic-debugging`, `verification-before-completion`

Эти skills загружаются Claude как broad methodology layer.

### 2. Custom OpenClaw control skills (`openclaw-control/skills/`)

Узкие, детерминированные, безопасные skills:

- `github-project-sync` — синхронизация GitHub Project
- `ci-status-watcher` — мониторинг CI
- `openclaw-config-guard` — валидация конфигурации
- `openclaw-runtime-auditor` — аудит runtime
- `cross-agent-handoff-writer` — handoff-пакеты между агентами

Эти skills отвечают за runtime safety, approvals, hooks, alerting и workflow-specific state transitions.

## Как пользоваться

### Проверить состояние

```bash
# На VPS
ssh root@80.74.25.43
cd /opt/openclaw-control
./scripts/oc-audit
```

### Посмотреть, что ожидает approval

```bash
./scripts/oc-approval list
```

### Одобрить спеку

```bash
./scripts/oc-approval approve spec-pvti_42
```

### Выкачать изменения (сначала dry-run)

```bash
./scripts/oc-rollout --env vps control-plane          # покажет, что изменится
./scripts/oc-rollout --env vps --apply control-plane  # применит
```

### Проверить state

```bash
./scripts/oc-state-validate openclaw-control/.runtime/job_state_v1.json
```
