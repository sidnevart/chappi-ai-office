# Review Watcher Agent Continuity

## State Rules
- PR state in /opt/ai-office/openclaw-control/.runtime/job_state_v1.json
- Session namespace: review-watcher/{pr_id}/{timestamp}
- On restart, resume monitoring active PRs from last known state

## Handoff Rules
- Triggered after PR open by coder-runner or orchestrator
- Reports CI failures and review blockers back to orchestrator
- Broadcasts daily PR digest to configured channels
- Report state transitions to UI via /agent-state endpoint
