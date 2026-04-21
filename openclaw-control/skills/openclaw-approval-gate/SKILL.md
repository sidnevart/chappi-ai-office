---
name: openclaw-approval-gate
description: Classify actions into automatic, dry-run, explicit approval, or never automatic. Use whenever work touches configs, hooks, systemd, git push, PR creation, messaging, or destructive operations.
---

# OpenClaw Approval Gate

- Map every action to the approval matrix before execution.
- If class is `explicit_approval`, require dry-run evidence first.
- If class is `never_automatic`, stop and escalate.
- Emit a clear approval request with correlation ID and rollback path.
- Reference: `docs/approval-matrix.md`
