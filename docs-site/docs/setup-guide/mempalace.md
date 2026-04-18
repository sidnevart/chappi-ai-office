---
sidebar_position: 6
title: MemPalace
---

# MemPalace — семантическая память

MemPalace обеспечивает семантический поиск в памяти агента. В отличие от PostgreSQL (структурированные данные), MemPalace хранит контекст разговоров и находит связанную информацию по смыслу.

## Установка на сервере

```bash
ssh root@ВАШ_IP

# Создать виртуальное окружение Python
python3 -m venv /opt/ai-office/mempalace-venv

# Установить MemPalace
/opt/ai-office/mempalace-venv/bin/pip install mempalace

# Инициализировать
/opt/ai-office/mempalace-venv/bin/mempalace init
```

## Первоначальная индексация

```bash
# Проиндексировать существующие файлы AGENTS.md
/opt/ai-office/mempalace-venv/bin/mempalace mine /root/.openclaw/workspace/
```

## Использование

```bash
# Сохранить факт
/opt/ai-office/mempalace-venv/bin/mempalace remember "Пользователь предпочитает краткие ответы"

# Поиск
/opt/ai-office/mempalace-venv/bin/mempalace search "предпочтения по стилю ответов"

# Пробудить контекст (для начала сессии)
/opt/ai-office/mempalace-venv/bin/mempalace wake-up
```

## Интеграция с OpenClaw

Агент автоматически использует MemPalace согласно инструкциям в `AGENTS.md`. Явно просить не нужно — это происходит в фоне.

## Где хранятся данные

```
/root/.mempalace/   — база ChromaDB + граф знаний SQLite
```

Размер: ~300 МБ после инициализации, растёт по мере использования.
