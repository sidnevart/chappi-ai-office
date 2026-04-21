---
name: openclaw-alert-router
description: Route runtime, workflow, hook, and service alerts into structured operator messages with dedupe and severity. Use when defining or debugging Telegram alert delivery.
---

# OpenClaw Alert Router

- Produce structured payloads, not raw log dumps.
- Attach severity, system, event type, correlation ID, and next action.
- Deduplicate repeated failures inside the policy window.
- Route by policy, never by hardcoded chat IDs.
- Reference: `docs/alerting.md`
