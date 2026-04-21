# Local vs VPS

## Local

- Dev env files, no systemd.
- Alerts default to dry-run.
- Browser side effects require local approval.
- Debugging uses direct logs and local compose.
- `oc-rollout --env local control-plane` syncs the bundle into `~/.openclaw/control-plane`.
- `oc-rollout --env local runtime-config` renders `~/.openclaw/openclaw.json` with backups.

## VPS

- Root-owned env files and systemd.
- Monitoring stack via Docker Compose.
- Telegram alerting enabled.
- Rollouts must be backup-first and restart-safe.
- `oc-rollout --env vps control-plane` syncs the bundle into `/opt/openclaw-control`.
- `oc-rollout --env vps runtime-config` backs up and renders `/root/.openclaw/openclaw.json`.
- `oc-rollout --env vps systemd-sync` updates canonical `openclaw.service`, `openclaw-control-monitoring.service`, and `openclaw-control-webhook.service`.
- `oc-rollout --env vps nginx-sync` patches the GitHub webhook path into nginx.
- `oc-rollout --env vps webhook-activate` and `oc-rollout --env vps monitoring-activate` are the live activation steps after sync.

## Shared rules

- Same templates and policies.
- Same hook registry shape.
- Same approval classes.
- Environment-specific values come from env, not committed config.
