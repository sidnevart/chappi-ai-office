---
sidebar_position: 2
title: Настройка сервера
---

# Настройка виртуального сервера

## Первоначальная настройка

```bash
# Подключитесь к серверу
ssh root@ВАШ_IP

# Обновите систему
apt update && apt upgrade -y

# Установите необходимые пакеты
apt install -y curl git wget nano htop ufw
```

## Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com | sh

# Запуск при старте системы
systemctl enable docker
systemctl start docker
```

## PostgreSQL с pgvector

```bash
# Запустите PostgreSQL в Docker
docker run -d \
  --name ai-office-postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=ВАШ_ПАРОЛЬ \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_office \
  -v pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

# Проверьте что работает
docker ps | grep postgres
```

## Создание схемы базы данных

```bash
PGPASSWORD=ВАШ_ПАРОЛЬ psql -h localhost -p 5432 -U postgres -d ai_office << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS notes (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  tags TEXT[],
  embedding vector(1536),
  source TEXT DEFAULT 'telegram',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  priority TEXT DEFAULT 'normal',
  status TEXT DEFAULT 'open',
  due_date DATE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS links (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  title TEXT,
  summary TEXT,
  tags TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS research_reports (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  query TEXT,
  sources TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profile_memory (
  id SERIAL PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event_log (
  id SERIAL PRIMARY KEY,
  agent_id TEXT DEFAULT 'main',
  state TEXT,
  tool_name TEXT,
  model TEXT,
  tokens_in INT,
  tokens_out INT,
  cost_usd NUMERIC(10,6),
  task_summary TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
EOF
```

## Ollama

```bash
# Установка
curl -fsSL https://ollama.com/install.sh | sh

# Запуск как служба
systemctl enable ollama
systemctl start ollama

# Войти в аккаунт (интерактивно)
ollama signin

# Загрузить модели
ollama pull qwen3:8b
ollama pull glm-5:cloud
ollama pull kimi-k2.5:cloud
```

## Брандмауэр

```bash
ufw allow OpenSSH
ufw allow 3000/tcp
ufw allow 4000/tcp
ufw allow 5000/tcp
ufw enable
```
