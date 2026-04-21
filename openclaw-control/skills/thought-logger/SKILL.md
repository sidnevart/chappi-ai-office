---
name: thought-logger
description: Log the agent's reasoning, decisions, and plan changes. Write thought process to durable files for transparency and debugging.
---

# Thought Logger

Make the agent's reasoning transparent to the human operator.

## What to log

- **Decision rationale**: Why did I choose approach A over B?
- **Plan changes**: What changed in the plan and why?
- **Risk assessment**: What could go wrong?
- **Assumptions**: What am I assuming?
- **Blockers**: What's stopping progress?
- **Handoff reasoning**: Why am I handing off to another agent?

## Where to log

### 1. Workspace thought file

Write to `thoughts/YYYY-MM-DD.md` in your agent workspace:

```markdown
## 2026-04-21 14:32 UTC — Session <session_id>

**Task**: <brief description>
**State**: <current state>

### Decision
<I chose X because Y>

### Plan
1. <step 1>
2. <step 2>

### Risks
- <risk 1>
- <risk 2>

### Blockers
- <blocker or "none">
```

### 2. PostgreSQL notes

```bash
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "INSERT INTO notes (content, tags, source)
   VALUES ('<thought summary>', ARRAY['thought','<agent-id>','<job-id>'], '<agent-id>');"
```

### 3. Event log

```bash
echo '{"agent_id":"<id>","event":"thought","summary":"<one-line>","timestamp":"<ISO8601>"}' \
  >> .runtime/events/agent-thoughts.jsonl
```

## Transparency levels

| Level | What to log | Audience |
|-------|-------------|----------|
| `public` | State transitions, task completions | UI dashboards, Telegram |
| `internal` | Decision rationale, plan changes | Workspace files, KB |
| `debug` | Full reasoning, tool calls, errors | Session logs, JSONL |

## Rules

- Always log at `public` level for state changes
- Log at `internal` level for non-obvious decisions
- Log at `debug` level only when debugging failures
- Never log secrets, tokens, or personal data
- One thought per decision — don't over-log
- When handing off, summarize your reasoning for the next agent
