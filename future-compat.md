# Future Compatibility Notes

## Claude Code CLI → Non-Claude Backend

Claude Code CLI uses the Anthropic SDK. The production-safe default is to run it against Anthropic directly.

If you want `Claude Code` to drive non-Claude models such as `kimi-*` or `glm-*`, you must place an Anthropic-compatible bridge in front of that model backend:

```bash
export CONTROL_CLAUDE_MODEL=kimi-k2.6:cloud
export CONTROL_CLAUDE_BASE_URL=http://<bridge-host>:<port>
export CONTROL_CLAUDE_API_KEY=<bridge-token>
```

**Caveat:** raw Ollama/OpenAI endpoints are not enough. Claude Code expects Anthropic-compatible response semantics, including tool-use behavior.

Current OpenClaw runner policy:

- no custom model configured: use native Claude backend
- custom non-Claude model configured: require explicit bridge vars or fail preflight

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
| Claude Code CLI | Complex multi-file coding, planning | Native Claude by default; custom models need Claude-format bridge |
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
