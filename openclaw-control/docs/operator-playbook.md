# Operator Playbook

## Incident loop

1. Run `scripts/oc-audit`.
2. Run `scripts/oc-preflight <local|vps>`.
2. Confirm current service state and blast radius.
3. Use `scripts/oc-rollout --dry-run <target>`.
4. Take backups before `--apply`.
5. Validate with `scripts/oc-verify <local|vps>`, then service health, logs, and approval routes.
6. Record follow-up policy or automation changes.

## Standard targets

- `monitoring-hotfix`: Grafana, Loki, Promtail, datasource checks.
- `runtime-config`: OpenClaw config templates, gateway policy.
- `systemd-sync`: unit templates and restart policy.
- `nginx-sync`: webhook route snippet and nginx site patching.
- `webhook-activate`: enable and restart `openclaw-control-webhook.service`.
- `monitoring-activate`: enable and restart `openclaw-control-monitoring.service`.
- `control-plane`: docs, hooks, skills, scripts, policies.

## Preferred CLI surface

- Core ops: `oc-audit`, `oc-rollout`, `oc-rollback`, `oc-hook-test`, `oc-alert-test`, `oc-cleanup`
- SDLC orchestration: `oc-sdlc`
- GitHub Project task creation: `oc-github-project`
- Research lifecycle: `oc-research`
- Approval operations: `oc-approval`
- Narrow wrappers remain for compatibility, but new automation should call the canonical commands above.

## Install entrypoints

- `scripts/oc-install-local`: local control-plane sync, optional config render, Codex skill sync.
- `scripts/oc-install-vps`: VPS control-plane sync, optional runtime-config and systemd-sync apply.
- `scripts/oc-nginx-sync`: patch webhook route into nginx and reload config.
- `scripts/oc-sync-codex-skills`: refresh `.codex/skills` from `openclaw-control/skills`.
- `scripts/oc-sdlc`: sync GitHub items, normalize raw webhooks, prepare specs, publish specs, prepare Claude-runner dry-runs, inspect SDLC job state.
- `scripts/oc-spec-artifact`: publish prepared spec Markdown into the docs artifact tree and store checksum metadata.
- `scripts/oc-github-project`: create GitHub issue/project tasks, move status, close canary issues; dry-run by default, apply only after approval.
- `scripts/oc-research`: interview, create, run, digest, pause, resume, stop, and inspect durable research jobs.
- `scripts/oc-approval`: list, approve, reject, and deliver approval-gated human messages.
- `scripts/oc-webhook-bootstrap-secret`: create `GITHUB_WEBHOOK_SECRET` on VPS if missing.
- `scripts/oc-webhook-probe`: send a signed dry-run GitHub Projects webhook through nginx.
- `scripts/oc-telegram-route-bootstrap`: map control-plane `TELEGRAM_*` route vars from legacy `TG_*` vars on VPS when needed.
- `scripts/oc-postgres-env-sync`: copy the current Postgres password value from the running container into `/root/.env` without rotating it.
- `scripts/oc-postgres-rotate-password`: rotate the Postgres password, update `/root/.env`, restart dependent services, and validate a fresh TCP login.

## Gateway unit rule

- `openclaw.service` is the canonical gateway unit.
- `openclaw-control-gateway.service` is deprecated and should be removed by `systemd-sync`.
- `systemd-sync` updates `openclaw.service` in place and manages
  `openclaw-control-monitoring.service` and `openclaw-control-webhook.service`.

## Webhook intake rule

- `openclaw-control-webhook.service` listens on localhost only.
- nginx exposes `/hooks/github/projects-v2-item` and proxies to the local webhook service.
- GitHub delivery validation should use `X-Hub-Signature-256` and `GITHUB_WEBHOOK_SECRET`.
- If `GITHUB_WEBHOOK_SECRET` is absent, webhook verification should fail closed in production.
- Bring-up path: `oc-webhook-bootstrap-secret apply`, `oc-rollout --apply --env vps webhook-activate`, then `oc-webhook-probe`.

## SDLC progression rule

- Spec publication creates a pending approval record in the `approval:` namespace.
- Spec artifacts are stable Markdown files. Use `oc-spec-artifact publish <project-key> <item-id>` after `prepare-spec` to copy the spec to `CONTROL_DOCS_ARTIFACT_DIR` and update `doc_url`.
- Branch bootstrap is blocked until the spec approval is marked `approved`.
- Coder execution starts with `oc-sdlc run-coder <project-key> <item-id>`, which creates a bounded Claude handoff prompt and dry-run command.
- Production default: if `CONTROL_CLAUDE_MODEL` is unset, Claude CLI uses its configured native backend.
- Non-Claude models such as `kimi-*`, `glm-*`, or `qwen-*` are treated as `bridge` mode and require both `CONTROL_CLAUDE_BASE_URL` and `CONTROL_CLAUDE_API_KEY`; otherwise the runner fails preflight before any git mutation.
- Apply path: `oc-sdlc run-coder <project-key> <item-id> --apply` prepares the executor; `CONTROL_CODER_EXECUTE=1` runs Claude CLI in the isolated worktree. `CONTROL_CODER_PUSH_APPROVED=1` and `CONTROL_CODER_PR_APPROVED=1` remain separate gates for push and PR creation.
- CI pass creates a second approval request for the PR digest before human delivery.
- Human-facing delivery happens through `oc-approval deliver`, not by writing directly to Telegram from ad hoc scripts.
- Production specs route: `TELEGRAM_SPECS_CHAT_ID` should point to `@chappi_ai_office_specs`.
- Production PR route: `TELEGRAM_PRS_CHAT_ID` should point to `@chappi_ai_office_pr`.
- Safe-channel bring-up may temporarily map specs/PRs to a notify chat only before dedicated production groups are assigned.

## GitHub Project Task Rule

- Dry-run: `openclaw-control/scripts/oc-github-project create-task payload.json`
- Apply: `openclaw-control/scripts/oc-github-project create-task --apply payload.json`
- Status dry-run: `openclaw-control/scripts/oc-github-project set-status payload.json`
- Status apply: `openclaw-control/scripts/oc-github-project set-status --apply payload.json`
- Required fields: `title`, `repository`, `project_owner`, and either `project_title` or `project_number`.
- Apply creates a GitHub issue and adds it to the configured GitHub Project through `gh`.
- The local `gh` token must include `project`; use `gh auth refresh -s project` before live apply.
- Canary cleanup: `openclaw-control/scripts/oc-github-project close-canary payload.json` records a dry-run; add `--apply` only when closing the test issue is approved.

Status sync maps OpenClaw SDLC state to GitHub Project status:

- `intake_needed` / `synced` -> `Todo`
- `spec_ready` -> `Tech Spec`
- `awaiting_spec_approval` -> `Specification Review`
- `spec_approved` / `branch_bootstrapped` / `implementing` -> `In Progress`
- `pr_open` / `awaiting_pr_digest_approval` -> `Code Review`
- `ci_failed` / `testing` -> `Testing`
- `ci_passed_notified` / `done` -> `Done`

## Research Progression Rule

- Start intake: `openclaw-control/scripts/oc-research start-interview payload.json`
- Add answers: `openclaw-control/scripts/oc-research update-intake <job-id> answers.json`
- Create only when complete: `openclaw-control/scripts/oc-research create-job <job-id>`
- Run one job: `openclaw-control/scripts/oc-research run-job <job-id>`
- Prepare digest: `openclaw-control/scripts/oc-research digest <job-id> <run-id>`
- Run due jobs: `openclaw-control/scripts/oc-research run-due`
- Pause/resume/stop: `openclaw-control/scripts/oc-research pause|resume|stop <job-id>`
- Inspect: `openclaw-control/scripts/oc-research status <job-id>`
- Required intake fields: sources, filters/metrics, schedule, output format, output schema, delivery route, and stop conditions.
- VPS scheduling uses `openclaw-control-research.timer`, which invokes `oc-research run-due` every 15 minutes. Job-specific cadence is still stored in durable job state.

## Required backups

- OpenClaw config: timestamped copy of `/root/.openclaw/openclaw.json`.
- systemd units: copy previous unit files before replacement.
- Postgres: schema-only or full dump depending on change.
- Docker compose services: capture `docker inspect` and current image tags.
