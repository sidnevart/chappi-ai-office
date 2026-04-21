---
name: branch-pr-bootstrap
description: Create a task branch, initialize implementation context, and prepare PR metadata after approval. Use when a spec has been approved and coding is authorized.
---

# Branch PR Bootstrap

- Verify approval state before branch creation.
- Use explicit branch naming tied to internal task IDs.
- Prepare PR template, labels, and rollout notes early.
- Hand off to `coder-task-runner` with a bounded session key.
- Reference: `../references/sdlc-lifecycle.md`
