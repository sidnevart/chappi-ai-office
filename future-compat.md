# Future Compatibility Notes

## Claude Code CLI → Ollama Backend

Claude Code CLI uses the Anthropic SDK. To redirect it to a local/custom backend:

```bash
# Point Claude Code at Ollama's OpenAI-compatible endpoint
export ANTHROPIC_BASE_URL=http://localhost:11434/v1
export ANTHROPIC_API_KEY=ollama   # dummy key, ollama ignores it

# Or set in ~/.claude/settings.json:
# "env": { "ANTHROPIC_BASE_URL": "http://localhost:11434/v1" }
```

**Caveat:** Claude Code expects Claude-specific response formats (tool_use, thinking blocks).
Ollama models respond in OpenAI format. Full compatibility requires a proxy layer.

**Recommended proxy:** `litellm` — translates between Anthropic and OpenAI formats:
```bash
pip install litellm
litellm --model ollama/glm-5:cloud --port 8082 --drop_params
export ANTHROPIC_BASE_URL=http://localhost:8082
```

Docs: https://docs.litellm.ai/docs/proxy/quick_start

---

## Codex CLI → Ollama Backend

Codex CLI uses OpenAI format natively — simpler to redirect:

```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama

codex --model glm-5:cloud "your task"
```

Docs: https://github.com/openai/codex

---

## When To Use Each

| Tool | Best for | Model |
|------|---------|-------|
| Claude Code CLI | Complex multi-file coding, planning | Needs Claude-format proxy |
| Codex CLI | Single-shot code gen, scripts | Direct ollama compat |
| OpenClaw agent | Telegram interactions, research, automation | glm-5:cloud / minimax-m2:cloud |

---

## Model Limits & Fallback Strategy

OpenClaw configured fallback chain:
```
glm-5:cloud → glm-4.6:cloud → minimax-m2:cloud → openai-codex/gpt-5.3-codex
```

If ollama cloud limits are hit: openclaw auto-falls back to next in chain.
openai-codex is the guaranteed fallback (has OAuth refresh tokens).

**Monitoring limits:**
```bash
openclaw models status   # shows usage stats per provider
openclaw channels status # shows Telegram health
```

---

## Notes for When This Is Revisited

- All secrets in `ai_office/.env`
- Postgres on VPS: `80.74.25.43:5432`, db=`ai_office`
- Coding sandbox: `docker exec -it ai-office-sandbox bash` on VPS
- OpenClaw workspace: `~/.openclaw/workspace/`
- Agent instructions: `~/.openclaw/workspace/AGENTS.md`
