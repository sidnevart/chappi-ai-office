# Approval Matrix

## Automatic

- Read-only inspections.
- Static validation and schema checks.
- Drafting specs and research summaries.

## Dry-run only

- Config diffs.
- Hook diffs.
- systemd diffs.
- SQL and Docker change previews.
- Skill install or removal previews.

## Dry-run plus explicit approval

- `openclaw.json` mutations.
- `AGENTS.md`, `USER.md`, `IDENTITY.md`, `HEARTBEAT.md`, `TOOLS.md`.
- Hook handler changes.
- systemd create, update, or delete.
- `git push`, PR creation, Telegram delivery to human groups.
- Runtime shell commands with service, file, db, or network side effects.

## Never automatic

- Secret extraction.
- Destructive data deletion without backup.
- PR merge, close, reopen, or branch delete.
- Disabling alerting or approval policy.
