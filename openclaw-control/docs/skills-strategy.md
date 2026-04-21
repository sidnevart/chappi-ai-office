# Skills Strategy

The skill system has two layers:

- Superpowers foundation: broad capabilities, loaded through role packs, not globally.
- Custom OpenClaw control skills: narrow, deterministic, side-effect-aware.

## Role packs

- `ops`: runtime, config, hooks, monitoring, alerting, rollout.
- `sdlc`: intake, spec, branch, PR, CI watcher.
- `research`: interview, source strategy, lifecycle manager, digest, schema.
- `authoring`: Codex and Claude skill authoring and handoff.

## Superpowers foundation

For the SDLC path, the foundation layer comes from `obra/superpowers`.

The core workflow skills are:

- `brainstorming`
- `using-git-worktrees`
- `writing-plans`
- `subagent-driven-development`
- `executing-plans`
- `test-driven-development`
- `requesting-code-review`
- `finishing-a-development-branch`

The support skills are:

- `dispatching-parallel-agents`
- `receiving-code-review`
- `systematic-debugging`
- `verification-before-completion`
- `using-superpowers`
- `writing-skills`

These are synced into `.claude/skills` via `scripts/oc-sync-claude-skills`.
Claude uses them as the broad SDLC methodology layer; the custom OpenClaw
skills stay responsible for runtime safety, approvals, hooks, alerting, and
workflow-specific state transitions.

## Rules

- Keep `SKILL.md` concise.
- Move long checklists and examples into `skills/references/`.
- Wrap risky foundation skills with approval-aware custom skills.
