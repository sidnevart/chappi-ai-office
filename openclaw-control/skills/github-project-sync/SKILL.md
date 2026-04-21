---
name: github-project-sync
description: Sync GitHub Project items into internal task state, detect changed fields, and trigger intake or workflow transitions. Use on project-item create or update events.
---

# GitHub Project Sync

- Treat GitHub Project as intake state, not full workflow memory.
- Normalize external identifiers into internal `job_state`.
- Detect missing fields and queue intake interviews.
- Emit deterministic transition events for the SDLC workflow.
- Reference: `../references/sdlc-lifecycle.md`
