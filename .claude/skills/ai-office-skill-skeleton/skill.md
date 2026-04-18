---
name: ai-office-skill-skeleton
description: >-
  Create a new skill for the AI Office skill catalog. Use when the user says
  "создай скилл для X", "добавь новый скилл", "make a skill that...", or wants
  to extend the AI Office automation catalog. Generates the skill.md file in
  .claude/skills/ and optionally registers it in skills_catalog in the KB.
  Do NOT use for: editing existing skills (edit the file directly), creating
  Claude Code global skills (those go in ~/.claude/skills/).
argument-hint: <skill-name> [short description]
tools: Read, Write, Bash
model: sonnet
---

# Skill Skeleton Generator

## What This Creates
1. `ai_office/.claude/skills/<skill-name>/skill.md` — full skill definition
2. (Optional) DB entry in `skills_catalog` if Postgres is up

## Step 1: Gather Requirements
Before generating, determine:
- **name**: kebab-case, e.g. `gmail-summarizer`
- **trigger**: exact phrases that should invoke this skill
- **anti-triggers**: when NOT to invoke
- **tools needed**: Bash, Read, Write, WebSearch, etc.
- **model tier**: haiku (simple), sonnet (default), opus (complex reasoning)
- **what it does**: step-by-step procedure

## Step 2: Generate skill.md

Template to fill:
```markdown
---
name: <skill-name>
description: >-
  <What this skill does in 1-2 sentences.>
  Trigger phrases: "<phrase1>", "<phrase2>".
  Do NOT use for: <anti-trigger>.
tools: <Bash, Read, ...>
model: <haiku|sonnet|opus>
---

# <Skill Title>

## Purpose
<What this skill accomplishes>

## When to Use
- <trigger scenario 1>
- <trigger scenario 2>

## When NOT to Use
- <anti-trigger 1>
- <anti-trigger 2>

## Steps

### 1. <First Step>
```bash
# commands here
```

### 2. <Second Step>
...

## Output Format
<Describe expected output format>

## Safety / Notes
<Any important warnings or constraints>
```

## Step 3: Write the File
```bash
mkdir -p /Users/artemsidnev/Documents/Projects/ai_office/.claude/skills/<skill-name>
# Then write skill.md with Write tool
```

## Step 4: Register in KB (if postgres available)
```sql
INSERT INTO skills_catalog (name, description, trigger_phrases, model_tier)
VALUES (
  '<skill-name>',
  '<description>',
  ARRAY['<phrase1>', '<phrase2>'],
  '<light|medium|heavy>'
)
ON CONFLICT (name) DO UPDATE
  SET description = EXCLUDED.description,
      trigger_phrases = EXCLUDED.trigger_phrases;
```

## Step 5: Confirm
Tell user:
- Path to new skill file
- Which trigger phrases will activate it
- Which model tier it uses
- Whether it was registered in KB
