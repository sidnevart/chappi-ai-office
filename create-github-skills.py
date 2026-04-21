import os

BASE = "/root/.openclaw/skills"
os.makedirs(BASE, exist_ok=True)

SKILLS = {
    "proactive-research": """# proactive-research

## Описание

Проактивное поведение для исследовательских агентов. Агент сам предлагает действия, не ждет команды.

## Когда активируется

- Есть открытые задачи в agent_tasks со статусом pending
- Прошло N часов с последнего обновления по проекту
- Пользователь не давал команду в течение idle-периода

## Действия

1. Проверить agent_tasks на наличие pending задач
2. Проверить research/jobs на зависшие джобы
3. Если found → запустить соответствующего агента
4. Если нет активных задач → предложить пользователю через Telegram

## Команды

```bash
# Проверить статус
openclaw skills info proactive-research
```
""",

    "research-cog": """# research-cog

## Описание

Структурированный конвейер исследования: PLAN → GATHER → SYNTHESIZE → VALIDATE → OUTPUT.

## Фазы

### PLAN
- Определить цель исследования
- Сформулировать 3-5 ключевых вопросов
- Выбрать источники

### GATHER
- Поиск по открытым источникам (WebSearch, WebFetch)
- Скрейпинг страниц
- Извлечение структурированных данных

### SYNTHESIZE
- Агрегация фактов
- Устранение противоречий
- Выделение паттернов

### VALIDATE
- Перепроверка ключевых фактов
- Поиск контр-аргументов
- Оценка надежности источников

### OUTPUT
- Форматирование по шаблону
- Тегирование фактов
- Генерация открытых вопросов

## Использование

Активируется автоматически агентами company-dossier-analyst и scout-monitor.
""",

    "competitive-intelligence-market-research": """# competitive-intelligence-market-research

## Описание

Конкурентная разведка и анализ рынка. Сбор данных о конкурентах, рыночных трендах, sizing.

## Входные данные

- Название рынка / сектора
- География
- Список известных конкурентов (опционально)

## Выходные данные

1. **Market map** — визуальная карта конкурентов по осям
2. **Sizing** — TAM/SAM/SOM с обоснованием
3. **Competitor profiles** — 1-2 страницы на каждого
4. **Trends** — 5-7 ключевых трендов
5. **White spaces** — незанятые ниши

## Источники

- Crunchbase (funding, employees, valuation)
- LinkedIn (team, headcount)
- SimilarWeb (трафик)
- App stores (рейтинги, отзывы)
- Отчеты аналитиков (Gartner, CB Insights)
""",

    "slides-cog": """# slides-cog

## Описание

Генерация HTML-презентаций из структурированного контента.

## Вход

Markdown-файл со слайдами:
```markdown
# Заголовок слайда

- Bullet 1
- Bullet 2

## Примечание спикера
Текст заметки
```

## Выход

- `index.html` — reveal.js презентация
- `slides.json` — машиночитаемая структура

## Шаблон

Использует тему "white" с русскими шрифтами. Слайды:
1. Титульный
2. Проблема
3. Решение
4. Рынок
5. Бизнес-модель
6. Команд
7. Трекшн
8. Почему сейчас
9. Ask
10. Контакты

## Команды

Автоматически вызывается deliverables-architect при создании pitch deck.
""",

    "vector-memory-hack": """# vector-memory-hack

## Описание

Векторное хранилище для семантического поиска по исследовательским заметкам.

## Использование

1. Агент memory-librarian индексирует markdown-файлы в /research/
2. Векторы хранятся в PostgreSQL через pgvector
3. Поиск по смыслу: "найди компании в fintech с российским fit > 60"

## Схема

```sql
CREATE TABLE research_vectors (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ON research_vectors USING ivfflat (embedding vector_cosine_ops);
```

## API

- `index_file(path)` — индексировать файл
- `search(query, k=5)` — семантический поиск
- `get_related(file_path)` — найти похожие документы
""",

    "graphiti": """# graphiti

## Описание

Граф знаний для связей между сущностями исследовательской базы.

## Сущности

- Company
- Fund
- Market
- Feature
- Risk
- Hypothesis
- Person

## Отношения

- Fund → INVESTED_IN → Company
- Company → COMPETES_WITH → Company
- Company → OPERATES_IN → Market
- Company → HAS_FEATURE → Feature
- Company → FACES_RISK → Risk
- Company → HAS_HYPOTHESIS → Hypothesis
- Company → FOUNDED_BY → Person

## Хранение

PostgreSQL с расширением AGE или простые JSONB-таблицы:
```sql
CREATE TABLE knowledge_graph (
    id SERIAL PRIMARY KEY,
    source_type TEXT,
    source_id TEXT,
    relation TEXT,
    target_type TEXT,
    target_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Обновление

memory-librarian обновляет граф после каждого завершенного досье.
""",

    "rag-architect": """# rag-architect

## Описание

RAG (Retrieval-Augmented Generation) для исследовательских ответов. Агент отвечает на вопросы, опираясь на индексированные документы.

## Pipeline

1. **Retrieve**: поиск релевантных чанков в research_vectors
2. **Rerank**: ранжирование по релевантности
3. **Generate**: формирование ответа с цитатами
4. **Validate**: проверка, что ответ опирается на факты

## Использование

Активируется при запросе пользователя типа:
- "Что мы знаем про [company]?"
- "Какие компании в AI-агентах имеют fit > 70?"
- "Найди похожие на [company]"
""",

    "council-builder": """# council-builder

## Описание

Создание "совета" из нескольких агентов для коллективной оценки. Каждый агент дает свой взгляд, затем формируется консенсус.

## Механика

1. Определить вопрос (например, "инвестировать ли в Company X?")
2. Назначить агентов-экспертов:
   - investor-lens
   - operator-lens
   - russia-market-analyst
3. Каждый агент пишет свое мнение
4. research-orchestrator синтезирует:
   - Areas of agreement
   - Areas of disagreement
   - Consensus recommendation
   - Dissenting opinions

## Выход

```markdown
# Council Decision: [Topic]

## Участники

## Мнения

## Консенсус

## Расхождения

## Итоговая рекомендация
```
""",

    "create-agent-skills": """# create-agent-skills

## Описание

Утилита для создания новых агентов и их навыков. Шаблонизирует создание IDENTITY.md, AGENTS.md, SKILLS.md.

## Использование

```bash
# Создать нового агента
openclaw agents add my-agent --workspace ~/.openclaw/workspaces/my-agent

# Создать skill
mkdir -p ~/.openclaw/skills/local/my-skill
cat > ~/.openclaw/skills/local/my-skill/SKILL.md << 'EOF'
# my-skill

## Описание
...
EOF
```

## Шаблоны

Предоставляет готовые шаблоны для:
- Research agent
- Coder agent
- Reviewer agent
- Analyst agent
""",

    "docs-style": """# docs-style

## Описание

Стиль оформления документации и выходных артефактов. Единообразие форматирования.

## Правила Markdown

1. Заголовки H1 для документа, H2 для секций, H3 для подсекций
2. Таблицы для структурированных данных
3. Код в backticks, блоки кода с указанием языка
4. Ссылки в формате [текст](URL)
5. Изображения в отдельной директории

## Цветовая схема для HTML

- Primary: #1a73e8
- Success: #34a853
- Warning: #fbbc04
- Danger: #ea4335
- Text: #202124
- Background: #ffffff

## Шрифты

- Заголовки: Inter Semi Bold
- Текст: Inter Regular
- Моноширинный: JetBrains Mono
""",
}

for name, content in SKILLS.items():
    path = os.path.join(BASE, name)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "SKILL.md"), "w") as f:
        f.write(content)
    print(f"Created skill: {name}")

print(f"\nDone. Skills in {BASE}")
