# Architecture

The control plane is split into five bounded areas:

- Runtime: OpenClaw gateway, Office UI, hooks, systemd, monitoring.
- Workflow: SDLC jobs, research jobs, approvals, alert routing.
- State: durable job state, approval state, alert events, agent inventory.
- Skills: Superpowers foundation plus custom role-scoped skills.
- Operations: rollout, rollback, auditing, cleanup, smoke tests.

## Core agents

Implemented:

- `office-controller` (implicit): intake router and state owner; main session.
- `sdlc-orchestrator` (real profile): GitHub Project to spec to PR flow.
- `coder-runner` (real profile): isolated implementation sessions with approval gates.
- `review-watcher` (real profile): CI status and PR digest publication.

Deferred until stable:

- `research-orchestrator`: interview, job creation, schedule, output delivery.
- `ops-operator`: runtime health, rollout, rollback, systemd, Docker.
- `alert-router`: enrichment, dedupe, severity routing.

## Durable entities

- `job_state`: workflow state machine keyed by `job_id`.
- `approval_state`: pending and resolved approval requests keyed by `approval_id`.
- `alert_event`: routed operator events keyed by `alert_id`.
- `agent_state`: role, zone, active job, heartbeat, current tool activity.
- `tool_activity`: tool execution metadata for future UI overlays.

Schemas for these entities live under `openclaw-control/schemas/` and are
validated by `scripts/oc-state-validate`.

## Current SDLC path

The implemented deterministic SDLC path is now:

1. `oc-sdlc from-webhook` or `oc-sdlc sync`
2. durable `job_state` write under `jobs/sdlc/...`
3. `oc-sdlc prepare-spec`
4. durable spec artifact write under `specs/...`
5. `oc-sdlc publish-spec`
6. durable `approval_state` write plus `outbox/specs/...`
7. `oc-approval approve <spec-approval-id>`
8. `oc-sdlc bootstrap-branch`
9. `oc-sdlc record-pr`
10. `oc-sdlc record-ci`
11. durable PR digest approval and `outbox/prs/...`

That path is validated by `tests/sdlc-e2e.sh` and included in `tests/smoke.sh`.

## Session namespaces

- `sdlc:<project_key>:<item_id>`
- `research:<job_id>`
- `ops:<incident_id>`
- `approval:<approval_id>`

Main human chat is not a durable workflow namespace.
