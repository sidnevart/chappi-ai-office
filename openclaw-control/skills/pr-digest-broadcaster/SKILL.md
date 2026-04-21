---
name: pr-digest-broadcaster
description: Publish concise PR digests to the PR Telegram group after CI passes. Use for operator visibility, not for code review handling.
---

# PR Digest Broadcaster

- Wait for CI success before posting.
- Include PR link, task ID, changed area, and risk notes.
- Keep code review discussion in GitHub comments.
- Route via policy-backed channel lookup.
- Reference: `../references/sdlc-lifecycle.md`
