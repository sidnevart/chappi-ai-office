---
name: kimi-k25-cloud-setup-for-claude-code-cli
description: Use when setting up or debugging Claude Code CLI with either the default Anthropic backend or an explicit Anthropic-compatible bridge for Kimi/GLM-class models.
---

# Kimi / Claude Code CLI Setup

Use this skill for Claude Code CLI setup, not for OpenClaw runtime config.

## Goal

Run `claude` against either:

- the default Anthropic backend, or
- an explicit Anthropic-compatible bridge when Kimi/GLM models are required.

## Expected Topology

- Claude Code CLI talks to an Anthropic-compatible endpoint.
- The default endpoint is Anthropic.
- If Kimi/GLM-backed execution is required, provide an explicit Anthropic-compatible bridge URL via `ANTHROPIC_BASE_URL`.

Do not point Claude Code directly at `http://localhost:11434` unless the machine is intentionally running a local Anthropic-compatible bridge. Raw Ollama is not enough for Claude Code.

## Safe Setup

```bash
claude
```

For a one-shot command against the default backend:

```bash
claude
```

For a one-shot command against a custom bridge:

```bash
ANTHROPIC_BASE_URL=http://<BRIDGE_HOST>:<PORT> ANTHROPIC_API_KEY=<bridge-token> claude
```

To go back to the normal Anthropic cloud path:

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_API_KEY
claude
```

## Verification

1. If using a bridge, confirm it is reachable:

```bash
curl -s http://<BRIDGE_HOST>:<PORT>/health
```

2. Start Claude Code with the chosen env vars.
3. If requests fail, check:
   - the bridge is actually Anthropic-compatible
   - the host/port is reachable
   - the bridge still has working upstream models

## Common Mistakes

- Setting `ANTHROPIC_AUTH_TOKEN=.env.ANTHROPIC_AUTH_TOKEN`
  This is invalid shell syntax and the wrong variable for this flow.
- Using `claude --model kimi-k2.5: cloud`
  The model string is malformed and the space breaks it.
- Pointing Claude Code at raw Ollama without a compatible Anthropic bridge.
- Assuming Kimi works through Claude Code just because `--model kimi-k2.6:cloud` is set. The backend must understand Anthropic traffic and route that model.

## Recommended Shell Aliases

```bash
alias cc-anthropic='unset ANTHROPIC_BASE_URL ANTHROPIC_API_KEY && claude'
alias cc-bridge='ANTHROPIC_BASE_URL=http://<BRIDGE_HOST>:<PORT> ANTHROPIC_API_KEY=<bridge-token> claude'
```

## When To Escalate

Escalate to `ollama-ops` if model availability is the problem.
Escalate to `openclaw-ops` if the issue is actually OpenClaw routing/config rather than Claude Code CLI setup.

## Eval Prompts

- "Настрой Claude Code через kimi подешевле"
- "Почему Claude Code не ходит через Kimi bridge?"
- "Дай правильные env для Claude Code через Anthropic-compatible bridge"

