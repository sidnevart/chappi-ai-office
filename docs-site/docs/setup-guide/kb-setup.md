---
sidebar_position: 5
title: База знаний
---

# Настройка базы знаний

База знаний уже создаётся при настройке сервера (раздел «Настройка сервера»). Этот раздел — дополнительные детали и проверка.

## Проверка схемы

```bash
PGPASSWORD=ВАШ_ПАРОЛЬ psql -h localhost -p 5432 -U postgres -d ai_office \
  -c "\dt"
```

Должны быть таблицы: `notes`, `tasks`, `links`, `research_reports`, `profile_memory`, `event_log`.

## Тест сохранения

Скажите агенту:
```
Запомни: тест базы знаний прошёл успешно — дата настройки [сегодняшняя дата]
```

Проверьте через PostgreSQL:
```bash
PGPASSWORD=ВАШ_ПАРОЛЬ psql -h localhost -p 5432 -U postgres -d ai_office \
  -c "SELECT content, created_at FROM notes ORDER BY created_at DESC LIMIT 1;"
```

## Резервное копирование

```bash
# Дамп базы данных
pg_dump -h localhost -U postgres -d ai_office > ai_office_backup_$(date +%Y%m%d).sql

# Или через Docker
docker exec ai-office-postgres pg_dump -U postgres ai_office > backup.sql
```

## Настройка векторных индексов (для ускорения поиска)

```bash
PGPASSWORD=ВАШ_ПАРОЛЬ psql -h localhost -p 5432 -U postgres -d ai_office << 'EOF'
CREATE INDEX IF NOT EXISTS notes_embedding_idx
  ON notes USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
EOF
```

Этот индекс ускоряет семантический поиск через MemPalace при большом количестве заметок.
