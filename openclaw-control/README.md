# OpenClaw Control

Production-oriented control plane assets for the AI office.

## Quick start

1. Review policies in `policies/`.
2. Validate with `scripts/oc-audit`.
3. Dry-run rollout with `scripts/oc-rollout --env local control-plane` or `scripts/oc-rollout --env vps control-plane`.
4. Use `tests/smoke.sh` before shipping changes.
5. Install with `scripts/oc-install-local` or `scripts/oc-install-vps`.
6. Verify with `scripts/oc-verify local` or `scripts/oc-verify vps`.
7. Sync Claude skills with `scripts/oc-sync-claude-skills`.

## Preferred commands

- Ops: `oc-audit`, `oc-rollout`, `oc-rollback`, `oc-hook-test`, `oc-alert-test`, `oc-cleanup`
- SDLC: `oc-sdlc sync`, `oc-sdlc from-webhook`, `oc-sdlc prepare-spec`, `oc-sdlc publish-spec`, `oc-sdlc bootstrap-branch`, `oc-sdlc record-pr`, `oc-sdlc record-ci`, `oc-sdlc status`
- GitHub Projects: `oc-github-project create-task` for dry-run task creation, `oc-github-project create-task --apply` for approved issue/project creation, `oc-github-project set-status --apply` for workflow status sync
- Research: `oc-research start-interview`, `oc-research update-intake`, `oc-research create-job`, `oc-research pause`, `oc-research resume`, `oc-research stop`, `oc-research status`
- Approval: `oc-approval list`, `oc-approval approve`, `oc-approval reject`, `oc-approval deliver`

Compatibility wrappers remain for now, but the preferred surface is the small toolbelt above.

## Scope

- OpenClaw runtime templates
- Monitoring and rollout toolbelt
- Hook registry and session policy
- Approval and alert routing policy
- Role-scoped skill packs
- Deterministic hook handlers with durable local state
- Operational hook entrypoints: `oc-hook-run`, `oc-sdlc-sync`, `oc-spec-publish`, `oc-alert-route`
- Canonical workflow entrypoints: `oc-sdlc`, `oc-approval`
- GitHub Projects v2 normalization path: `oc-github-project-normalize`, `oc-sdlc-from-github-webhook`
- Approval gate and delivery ops: `oc-approval-list`, `oc-approval-approve`, `oc-approval-reject`, `oc-spec-deliver`
- Webhook entrypoint: `oc-webhook-server`
- Managed VPS webhook stack: `openclaw-control-webhook.service` + `oc-nginx-sync`
- Activation/bootstrap helpers: `oc-webhook-bootstrap-secret`, `oc-webhook-probe`, `oc-telegram-route-bootstrap`, `oc-postgres-env-sync`, `oc-postgres-rotate-password`
- Durable research workflow: `oc-research` with explicit interview, scheduled job state, visible agent inventory entry, and pause/resume/stop controls
- GitHub Project task creation: `oc-github-project create-task`, dry-run by default
- GitHub Project apply mode requires `gh auth refresh -s project`

## SDLC lifecycle

The deterministic SDLC lifecycle currently implemented in the control plane is:

1. `oc-sdlc sync` or `oc-sdlc from-webhook`
2. `oc-sdlc prepare-spec`
3. `oc-sdlc publish-spec`
4. `oc-approval approve <spec-approval-id>`
5. `oc-sdlc bootstrap-branch`
6. `oc-sdlc record-pr`
7. `oc-sdlc record-ci`
8. `oc-approval approve <pr-digest-approval-id>`
9. `oc-approval deliver <pr-digest-approval-id>`

This path is validated locally by `tests/sdlc-e2e.sh`.

## Research lifecycle

Research jobs are not created from implicit chat memory. The control plane requires a durable interview first:

1. `oc-research start-interview <payload.json>`
2. `oc-research update-intake <job-id> <answers.json>`
3. `oc-research create-job <job-id>`
4. `oc-research pause|resume|stop <job-id>` from Telegram or operator tooling
5. `oc-research status <job-id>` for durable state and agent inventory

`create-job` blocks until sources, filters/metrics, schedule, output format, output schema, delivery route, and stop conditions are complete.

## Live canaries completed

- VPS webhook ingress canary via `oc-webhook-probe`
- Live Telegram alert canary through the alerts route
- Live Telegram spec canary through the approval delivery path
- Live Telegram PR-digest canary tied to a real GitHub draft PR and passing check run
