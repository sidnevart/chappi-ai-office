---
name: kb-manage
description: >-
  Knowledge base management for AI Office (Postgres + pgvector). Use when
  setting up the KB schema, running ingest pipelines from Telegram, querying
  stored notes/documents/tasks, or configuring write-back and retrieval policy.
  KB entities: profile_memory, notes, links, documents, tasks, research_reports,
  repo_context, skills_catalog. Trigger phrases: "база знаний", "KB", "pgvector",
  "сохрани в KB", "найди в базе", "ingest", "postgres setup".
  Do NOT use for: docker/VPS setup (use vps-ops), raw postgres admin without KB context.
tools: Bash, Read, Write, Edit
model: sonnet
---

# Knowledge Base Management

## DB Connection
```bash
source /Users/artemsidnev/Documents/Projects/ai_office/.env
# Uses: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_PASSWORD from .env
# Default: localhost:5432, db=ai_office, user=postgres
PSQL="psql -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-ai_office}"
```

## 1. Initialize Schema (idempotent)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS profile_memory (
  id SERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notes (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  tags TEXT[],
  source TEXT DEFAULT 'telegram',
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS links (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  tags TEXT[],
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  filename TEXT,
  content TEXT,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','in_progress','done','blocked')),
  priority TEXT DEFAULT 'normal' CHECK (priority IN ('low','normal','high')),
  due_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS research_reports (
  id SERIAL PRIMARY KEY,
  query TEXT,
  content TEXT,
  sources JSONB DEFAULT '[]',
  confidence TEXT DEFAULT 'medium',
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS repo_context (
  id SERIAL PRIMARY KEY,
  repo TEXT NOT NULL,
  path TEXT,
  summary TEXT,
  embedding vector(1536),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skills_catalog (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  trigger_phrases TEXT[],
  model_tier TEXT DEFAULT 'medium' CHECK (model_tier IN ('light','medium','heavy')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notes_embedding_idx ON notes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS research_embedding_idx ON research_reports USING ivfflat (embedding vector_cosine_ops);
```

Run schema: `$PSQL -f schema.sql` or paste directly.

## 2. Write-back Policy

**SAVE to KB:**
- Explicit facts the user states ("я работаю в...", "мой сервер на...")
- Notes, links, summaries explicitly requested to save
- Completed tasks and their outcomes
- Research reports from research-agent
- Successful commands and their outputs (briefly)

**DO NOT SAVE:**
- Raw conversation noise or failed attempts
- Temporary debug output
- Intermediate reasoning steps
- Duplicate info already in KB

## 3. Retrieval Policy
```python
# Semantic search pattern (via psycopg2 or similar)
# Always top-3, return with relevance score
SELECT content, 1 - (embedding <=> $query_embedding) AS relevance
FROM notes
ORDER BY embedding <=> $query_embedding
LIMIT 3;
```

Output format: `[KB Result] relevance=0.92 | table=notes | <content>`

## 4. Quick Queries
```bash
# List recent tasks
$PSQL -c "SELECT title, status, due_at FROM tasks ORDER BY created_at DESC LIMIT 10;"

# Search notes by keyword
$PSQL -c "SELECT content, created_at FROM notes WHERE content ILIKE '%keyword%' LIMIT 5;"

# Skills catalog
$PSQL -c "SELECT name, model_tier, description FROM skills_catalog ORDER BY name;"
```
