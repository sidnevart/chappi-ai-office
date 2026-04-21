---
sidebar_position: 4
title: Работа с OpenClaw
---

# Работа с OpenClaw

OpenClaw — ядро вашего ИИ-помощника. Работает как системная служба на сервере.

## Управление службой (на сервере)

```bash
# Статус
systemctl status openclaw

# Перезапуск
systemctl restart openclaw

# Остановка
systemctl stop openclaw

# Просмотр журнала
journalctl -u openclaw -f
```

## Полезные команды OpenClaw

```bash
# Статус шлюза
openclaw gateway status

# Список моделей
openclaw models list

# Псевдонимы моделей
openclaw models aliases list

# Список активных каналов
openclaw channels list

# Информация о Telegram-канале
openclaw channels info telegram
```

## Уровни моделей

Псевдонимы настроены так:

```bash
openclaw models aliases add light ollama/qwen3.5:cloud
openclaw models aliases add medium ollama/glm-5:cloud
openclaw models aliases add heavy ollama/kimi-k2.6:cloud
```

Агент выбирает уровень автоматически по сложности задачи. Вы также можете явно попросить:

```
Используй тяжёлую модель и проанализируй этот код
Кратко (лёгкая модель): что такое REST?
```

## Интеграция с openclaw-control

OpenClaw работает в паре с [openclaw-control](./openclaw-control) — control plane, который управляет:

- **Approval gates** — перед опасными операциями система запрашивает подтверждение
- **SDLC workflow** — задачи из GitHub Project → спеки → approval → код → PR
- **Durable state** — job state не теряется при перезапуске

Через Telegram можно управлять control plane:

```
Покажи статус задач в проекте
Одобри спеку spec-pvti_42
Поставь research job на паузу
```

### Approval gates

Когда агент хочет выполнить рискованную операцию, система ставит её на approval:

- **Automatic** — read-only операции выполняются сразу
- **Dry-run** — показывает, что изменится, без применения
- **Dry-run + explicit approval** — показывает diff, ждёт вашего «одобряю»
- **Never automatic** — merge PR, удаление данных, отключение алертов

Список на approval:
```bash
/opt/openclaw-control/scripts/oc-approval list
```

Одобрить:
```bash
/opt/openclaw-control/scripts/oc-approval approve spec-pvti_42
```

## Файлы конфигурации

Все настройки OpenClaw на сервере хранятся в `/root/.openclaw/workspace/`:

| Файл | Содержимое |
|------|-----------|
| `AGENTS.md` | Инструкции агента — кто он, что умеет, как действует |
| `MEMORY.md` | Долгосрочная память — важные факты и решения |
| `SOUL.md` | Личность агента |
| `USER.md` | Информация о вас |
| `TOOLS.md` | Описание доступных инструментов |
| `memory/YYYY-MM-DD.md` | Ежедневные заметки |

Каждый субагент имеет собственную директорию:

| Агент | Директория |
|-------|-----------|
| `main` | `/root/.openclaw/workspace/` |
| `sdlc-orchestrator` | `/root/.openclaw/workspaces/sdlc-orchestrator/` |
| `coder-runner` | `/root/.openclaw/workspaces/coder-runner/` |
| `review-watcher` | `/root/.openclaw/workspaces/review-watcher/` |

## Список агентов

```bash
openclaw agents list
```

## Изменение инструкций агента

Для изменения поведения агента отредактируйте `AGENTS.md` на сервере:

```bash
ssh root@80.74.25.43
nano /root/.openclaw/workspace/AGENTS.md
systemctl restart openclaw
```

## Сердцебиение (Heartbeat)

Агент периодически получает пинг и проверяет почту, календарь, уведомления. Конфигурация в `HEARTBEAT.md`:

```bash
nano /root/.openclaw/workspace/HEARTBEAT.md
```

Задачи для регулярного выполнения добавляются через крон OpenClaw:

```bash
openclaw cron list
openclaw cron add "office-status" --schedule "0 * * * *"
```
