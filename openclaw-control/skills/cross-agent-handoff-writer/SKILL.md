---
name: cross-agent-handoff-writer
description: Write explicit handoff packets between controller, coder, reviewer, and research agents. Use whenever work changes owners or moves between runtime roles.
---

# Cross Agent Handoff Writer

- Summarize current state, decision history, open risks, and next action.
- Include stable IDs: job, approval, PR, incident, and session key.
- Keep handoffs bounded so the next agent does not reload giant context.
- Prefer checklist-shaped packets over narrative dumps.
- Reference: `../references/operator-guidelines.md`
