---
name: spec-review-publisher
description: Publish spec review requests to the designated Telegram specs group with approval context and links. Use after spec generation and before implementation starts.
---

# Spec Review Publisher

- Publish only after explicit routing policy lookup.
- Include task ID, spec link, summary, and requested decision.
- Record approval result back into durable state.
- Never use Telegram as the system of record for review comments.
- Reference: `../references/sdlc-lifecycle.md`
