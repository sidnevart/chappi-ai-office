# Systemd Templates

These templates are the target systemd source of truth once the control plane is adopted.

## Templates

- `openclaw.service`: canonical OpenClaw gateway unit with preflight and config guards.
- `openclaw-control-monitoring.service`: monitoring compose stack validation and startup.
- `openclaw-control-webhook.service`: GitHub Projects webhook intake.
- `openclaw-control-research.service` + `.timer`: durable research job scheduler; calls `oc-research run-due` and never runs free-form chat prompts.

Do not apply template updates directly without:

1. `scripts/oc-rollout --dry-run`
2. timestamped unit backup
3. `systemctl daemon-reload`
4. service health verification
