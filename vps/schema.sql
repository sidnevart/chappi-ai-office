-- Chappi AI Office — схема базы данных PostgreSQL
-- Применяется автоматически при docker-compose up (initdb.d)
-- или вручную: psql -U postgres -d ai_office -f schema.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- Заметки и факты
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT[],
    source TEXT DEFAULT 'telegram',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Задачи
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done', 'blocked')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Ссылки
CREATE TABLE IF NOT EXISTS links (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    tags TEXT[],
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Исследовательские отчёты
CREATE TABLE IF NOT EXISTS research_reports (
    id SERIAL PRIMARY KEY,
    query TEXT,
    content TEXT,
    sources JSONB DEFAULT '[]',
    confidence TEXT DEFAULT 'medium',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Журнал событий агента (для Star Office UI / Grafana)
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

-- Профиль пользователя (ключ-значение)
CREATE TABLE IF NOT EXISTS profile_memory (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Контекст репозиториев
CREATE TABLE IF NOT EXISTS repo_context (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    path TEXT,
    summary TEXT,
    embedding vector(1536),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Каталог навыков агента
CREATE TABLE IF NOT EXISTS skills_catalog (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    trigger_phrases TEXT[],
    model_tier TEXT DEFAULT 'medium' CHECK (model_tier IN ('light', 'medium', 'heavy')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Документы (для MemPalace / семантического поиска)
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT,
    content TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Индексы для семантического поиска
CREATE INDEX IF NOT EXISTS notes_embedding_idx ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS links_embedding_idx ON links USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS research_embedding_idx ON research_reports USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_event_log_agent ON event_log USING btree (agent_id);
CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log USING btree (created_at DESC);
