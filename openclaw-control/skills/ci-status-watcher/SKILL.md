---
name: ci-status-watcher
description: Watch CI and PR status transitions, enrich failures, and trigger digest or alert events. Use after PR creation until merge-ready state is reached.
---

# CI Status Watcher

- Poll or subscribe with bounded retry policy.
- Route failed checks to alerts with actionable evidence.
- Route passed checks to `pr-digest-broadcaster`.
- Keep CI state attached to the internal task record.
- Reference: `../references/sdlc-lifecycle.md`
