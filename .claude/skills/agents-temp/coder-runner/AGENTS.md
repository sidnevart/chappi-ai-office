# Coder Runner Agent Continuity

## State Rules
- Active job state in /opt/ai-office/openclaw-control/.runtime/job_state_v1.json
- Session namespace: coder-runner/{job_id}/{timestamp}
- On restart, resume from last known state in job_state_v1.json
- Track branch name, commit SHA, and test results in durable state

## Handoff Rules
- On spec approval, coder-runner picks up the job automatically
- After implementation + tests pass, open PR and notify review-watcher
- Report state transitions to UI via /agent-state endpoint
