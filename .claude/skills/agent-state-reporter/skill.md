---
name: agent-state-reporter
description: Report agent state transitions to Star Office UI, OpenClaw Office UI, and event_log. Use at every state change, tool call, and session boundary.
---

# Agent State Reporter

Push agent state to all observability surfaces on every transition.

## When to use

- At session start (before any work)
- After every tool call
- On state transitions (idle → running → waiting → blocked → errored)
- At session end
- Before handing off to another agent

## Surfaces

### 1. Star Office UI (REST)

```bash
curl -s -X POST http://localhost:3000/set_state \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "<agent-id>",
    "state": "<idle|researching|writing|executing|syncing|error>",
    "detail": "<brief description of current activity>",
    "task_id": "<job_id or approval_id>",
    "session_key": "<namespace>"
  }'
```

### 2. OpenClaw Office UI (WebSocket via gateway)

The gateway forwards agent state automatically when you use `openclaw session --agent <id>`. No extra action needed.

### 3. PostgreSQL event_log

```bash
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "INSERT INTO event_log (agent_id, state, tool_name, model, task_summary)
   VALUES ('<agent-id>', '<state>', '<tool>', '<model>', '<summary>');"
```

### 4. Local events JSONL

Append to `openclaw-control/.runtime/events/agent-state.jsonl`:
```json
{"agent_id":"<id>","state":"<state>","timestamp":"<ISO8601>","detail":"<desc>","session_key":"<key>"}
```

## Required fields

| Field | Description |
|-------|-------------|
| `agent_id` | Your agent ID (e.g., `sdlc-orchestrator`) |
| `state` | One of: `idle`, `researching`, `writing`, `executing`, `syncing`, `error` |
| `detail` | Human-readable description (max 200 chars) |
| `timestamp` | ISO8601 UTC |
| `session_key` | Your namespace (e.g., `sdlc:ai-office:42`) |

## Rules

- Always include `agent_id` — never default to `main`
- Keep `detail` concise but informative
- Report errors immediately with `state: error` and full detail
- Before handoff, report `state: idle` with detail about handoff target
- Do not report more than once per minute for the same state+task combination
