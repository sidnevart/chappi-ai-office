---
name: openclaw-config-guard
description: Validate and guard OpenClaw config, gateway auth, trusted origins, session namespace policy, and env-backed placeholders. Use when editing openclaw config templates or investigating config drift.
---

# OpenClaw Config Guard

- Compare desired config to template and current runtime state.
- Reject secrets in git-tracked config.
- Enforce env placeholders for chat IDs, tokens, and hostnames.
- Require backup, diff, and validation before apply.
- Reference: `../references/operator-guidelines.md`
