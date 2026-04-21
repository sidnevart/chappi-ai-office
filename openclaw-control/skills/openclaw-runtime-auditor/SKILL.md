---
name: openclaw-runtime-auditor
description: Audit OpenClaw runtime state, gateway health, Office UI connectivity, monitoring status, and restart loops. Use for incidents, slow responses, reconnect loops, missing telemetry, or before rollout work.
---

# OpenClaw Runtime Auditor

- Inspect first: service state, ports, journals, Docker monitoring, recent restarts.
- Correlate one incident ID across gateway, UI, hooks, and alerts.
- Report root cause, blast radius, and the smallest safe remediation.
- Do not mutate runtime until dry-run and approval class are explicit.
- Reference: `../references/operator-guidelines.md`
