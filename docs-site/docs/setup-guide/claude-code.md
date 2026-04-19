---
sidebar_position: 8
title: Claude Code
---

# Настройка Claude Code

Claude Code — инструмент разработчика на вашем Mac для управления AI Office через разговор с ИИ.

## Установка

```bash
npm install -g @anthropic/claude-code
```

## Запуск в папке проекта

```bash
cd ~/Documents/Projects/ai_office
claude
```

## Специализированные агенты

В папке `.claude/agents/` находятся субагенты для управления AI Office:

| Агент | Назначение |
|-------|-----------|
| `infra-agent` | Задачи на сервере: Docker, systemd, PostgreSQL |
| `research-agent` | Исследования и поиск в интернете |
| `kb-agent` | Работа с базой знаний: сохранение, поиск |

Использование в чате с Claude Code:
```
Используй infra-agent чтобы проверить состояние сервисов на сервере
```

## Навыки (Skills)

В папке `.claude/skills/` находятся специализированные команды:

| Команда | Действие |
|---------|---------|
| `/ai-office-discovery` | Показать состояние всех компонентов |
| `/kb-manage` | Управление базой знаний |

## Хуки безопасности

В папке `.claude/hooks/` находятся защитные скрипты:

- `secrets_guard.py` — блокирует случайную запись секретов в файлы
- `high_risk_guard.py` — предупреждает о потенциально опасных операциях
- `session_report.py` — сохраняет краткий отчёт после каждой сессии

## MCP-серверы

Настройки в `.claude/settings.json`. По умолчанию подключён MemPalace (семантический поиск) через SSH на VPS.

---

## Использование Ollama-моделей с VPS (экономия токенов)

По умолчанию Claude Code использует Anthropic API. Можно переключиться на модели Ollama на VPS.

### Алиасы в ~/.zshrc

```bash
# Claude Code → Ollama на VPS (через litellm прокси)
alias cc-local='ANTHROPIC_BASE_URL=http://YOUR_VPS_IP:8082 ANTHROPIC_API_KEY=ollama claude'
alias cc-cloud='unset ANTHROPIC_BASE_URL ANTHROPIC_API_KEY && claude'

# Codex → Ollama напрямую (через SSH-туннель)
alias cx-light='OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama codex -m qwen3:8b'
alias cx-medium='OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama codex -m glm-5:cloud'
```

Использование:
```bash
cc-local   # Claude Code → qwen3/glm-5 через VPS
cc-cloud   # Claude Code → стандартный Anthropic API
cx-light   # Codex → qwen3:8b (лёгкие задачи)
```

### Что нужно на VPS

**litellm** — прокси, переводящий формат Anthropic → OpenAI (для Ollama):

```bash
# Уже настроен как systemd-служба: ai-office/vps/systemd/litellm.service
systemctl status litellm   # проверить
systemctl start litellm    # запустить если не работает
```

Слушает на порту 8082.

### SSH-туннель для Codex (Ollama на порту 11434)

LaunchAgent уже создан: `~/Library/LaunchAgents/ai.aioffice.ollama-tunnel.plist`

Активировать:
```bash
launchctl load ~/Library/LaunchAgents/ai.aioffice.ollama-tunnel.plist
```

После этого `localhost:11434` → Ollama на VPS.
