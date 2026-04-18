---
sidebar_position: 9
title: Интеграция с Google
---

# Интеграция с Google

Через Composio агент умеет работать с Google Документами, Таблицами, Диском, Задачами, а также Gmail и Google Календарём.

## Предварительные требования

1. Зарегистрируйтесь на [composio.dev](https://composio.dev)
2. Получите потребительский ключ (`ck_...`) в разделе **Settings → API Keys → Consumer Keys**
3. Добавьте ключ в настройки OpenClaw

## Настройка потребительского ключа

```bash
ssh root@ВАШ_IP

# Добавить в переменные окружения службы
systemctl edit openclaw
```

Добавьте строку:
```ini
[Service]
Environment=COMPOSIO_TOKEN_OPENCLAW=ck_ВАШ_КЛЮЧ
```

```bash
systemctl daemon-reload
systemctl restart openclaw
```

## Подключение Google Документов (уже работает)

Базовые инструменты Google Docs, Sheets, Drive, Tasks работают без дополнительной аутентификации через Composio.

Проверка:
```
Создай Google Документ с названием «Тест AI Office»
```

## Подключение Gmail и Google Календаря

Требуется браузерная авторизация через OAuth. Выполните на вашем Mac (не на сервере):

```bash
# Установить composio CLI
pip install composio-core

# Подключить Gmail
composio add gmail

# Подключить Календарь
composio add googlecalendar
```

После авторизации в браузере:
- Скопируйте учётные данные на сервер
- Обновите AGENTS.md с именами инструментов Gmail/Calendar

## Доступные инструменты

После настройки агент умеет:

| Сервис | Возможности |
|--------|------------|
| Google Документы | Создание, чтение, редактирование |
| Google Таблицы | Чтение и запись данных |
| Google Диск | Поиск файлов, загрузка |
| Google Задачи | Создание и управление задачами |
| Gmail | Чтение писем, отправка (после OAuth) |
| Google Календарь | Список событий, создание (после OAuth) |
| GitHub | Репозитории, задачи, пул-запросы |
| Notion | Страницы и базы данных |
| Jira | Задачи и проекты |
