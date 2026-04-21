# SDLC Orchestrator Agent Continuity

## State Rules
- All job state is stored in /opt/ai-office/openclaw-control/.runtime/job_state_v1.json
- Session namespace: sdlc-orchestrator/{job_id}/{timestamp}
- On restart, read job_state_v1.json for active jobs and resume from last known state
- Do NOT start new jobs for issues already in in_progress or pending_approval state

## Handoff Rules
- After spec is approved, trigger coder-runner via gateway job queue
- After PR is opened, notify review-watcher to monitor CI and review status
- Report state transitions to UI via /agent-state endpoint
