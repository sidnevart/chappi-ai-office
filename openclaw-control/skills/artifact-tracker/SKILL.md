---
name: artifact-tracker
description: Track all durable artifacts created by an agent. Log artifact creation, updates, and handoffs. Query artifact state for any job.
---

# Artifact Tracker

Track every file, JSON state, and handoff packet an agent produces.

## Artifact types

| Type | Location | Example |
|------|----------|---------|
| `job_state` | `.runtime/jobs/<kind>/<project>/<id>.json` | SDLC job state |
| `approval_state` | `.runtime/approvals/<id>.json` | Approval request |
| `spec` | `.runtime/specs/<project>/<id>.md` | Markdown spec |
| `spec_meta` | `.runtime/specs/<project>/<id>.json` | Spec metadata |
| `branch_meta` | `.runtime/branches/<project>/<id>.json` | Branch metadata |
| `pr_meta` | `.runtime/prs/<project>/<id>.json` | PR metadata |
| `ci_meta` | `.runtime/ci/<project>/<id>.json` | CI status |
| `coder_run` | `.runtime/coder-runs/<project>/<id>.json` | Coder execution state |
| `handoff` | `.runtime/handoffs/<job_id>.json` | Cross-agent handoff packet |
| `event` | `.runtime/events/<kind>.jsonl` | Event log |
| `outbox` | `.runtime/outbox/<route>/<id>.json` | Pending Telegram message |

## Logging

On every artifact creation or update:

```bash
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "INSERT INTO event_log (agent_id, state, task_summary)
   VALUES ('<agent-id>', 'artifact_created', '<artifact_path>');"
```

## Handoff packet format

```json
{
  "from_agent": "sdlc-orchestrator",
  "to_agent": "coder-runner",
  "job_id": "ai-office-42",
  "project_key": "ai-office",
  "item_id": "42",
  "session_key": "sdlc:ai-office:42",
  "branch_name": "sdlc/42-fix-typo",
  "spec_path": ".runtime/specs/ai-office/42.md",
  "worktree_path": ".runtime/coder-worktrees/ai-office/42/repo",
  "pr_url": "",
  "ci_expectations": ["pytest", "mypy"],
  "timestamp": "2026-04-21T12:00:00Z"
}
```

## Querying artifacts

```bash
# List all artifacts for a job
find .runtime -name "*<item_id>*" -type f

# Read current job state
cat .runtime/jobs/sdlc/<project>/<item_id>.json | jq .

# Read latest events for an agent
grep '"agent_id":"<id>"' .runtime/events/*.jsonl | tail -5
```

## Rules

- Every artifact must have a unique path derived from `project_key` + `item_id`
- Handoff packets are immutable — once written, never modify
- Always validate against schema before writing (use `scripts/oc-state-validate`)
- Log artifact creation before emitting any notification
- Clean up temporary artifacts after handoff is confirmed
