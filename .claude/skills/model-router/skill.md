---
name: model-router
description: >-
  Model routing policy for AI Office. Use when deciding which model tier to
  assign to a task or subagent: light (qwen3.5:cloud), medium (glm-5:cloud),
  heavy (kimi-k2.5:cloud). Called internally before spawning research-agent,
  kb-agent, or infra-agent to pick the right model. Also useful when user asks
  "какую модель использовать для X". Returns tier + model + one-line reason.
  Do NOT use for: actually invoking models (that's done via ollama run),
  openclaw config, or infrastructure work.
tools: Read
model: haiku
---

# Model Routing Policy

## Tiers

| Tier   | Model           | Cost | Speed  | Context |
|--------|----------------|------|--------|---------|
| light  | qwen3.5:cloud  | Low  | Fast   | Short   |
| medium | glm-5:cloud    | Med  | Medium | Medium  |
| heavy  | kimi-k2.5:cloud| High | Slow   | Long    |

## Routing Rules (apply in order)

1. **light** — if task is one of:
   - Routing/classification decision
   - Short summary (< 500 words input)
   - Simple Q&A with known answer
   - Inbox triage / tag assignment
   - Status check / health check formatting

2. **medium** — if task is one of:
   - Code draft generation (< 200 lines)
   - Analysis of a known document
   - Structured data extraction
   - Research synthesis from pre-fetched sources
   - Writing notes / task descriptions
   - KB ingest and embedding generation

3. **heavy** — if task is one of:
   - Multi-step web research from scratch
   - Long-context code review (> 500 lines)
   - Complex planning across multiple phases
   - Anything requiring reasoning over 8k+ tokens
   - Cross-referencing multiple sources

## Access Rules (CRITICAL)
- **light** models: NEVER write-access to repos, external APIs, or production systems
- **medium** models: write-access to KB only; external writes require user confirmation
- **heavy** models: full access, but still confirm destructive external actions

## Output Format
Always return exactly:
```json
{ "tier": "light|medium|heavy", "model": "<model-name>", "reason": "<one line why>" }
```

## Examples
- "Summarize this note" → `{ "tier": "light", "model": "qwen3.5:cloud", "reason": "short summary task" }`
- "Research AI office tools" → `{ "tier": "heavy", "model": "kimi-k2.5:cloud", "reason": "multi-source web research" }`
- "Generate ingest script" → `{ "tier": "medium", "model": "glm-5:cloud", "reason": "code generation, medium complexity" }`
