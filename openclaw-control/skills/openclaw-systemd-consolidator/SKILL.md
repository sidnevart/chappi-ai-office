---
name: openclaw-systemd-consolidator
description: Consolidate OpenClaw-related systemd units, timers, restart policy, and compose startup behavior. Use when service sprawl or boot-order drift appears.
---

# OpenClaw Systemd Consolidator

- Normalize units around templates and explicit dependencies.
- Keep monitoring, gateway, UI, and watchdog ownership clear.
- Preserve restart safety and reload validation.
- Require daemon-reload and post-change health checks.
- Reference: `../references/operator-guidelines.md`
