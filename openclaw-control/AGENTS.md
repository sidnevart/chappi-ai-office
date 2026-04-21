# OpenClaw Control Plane

This tree defines the production-oriented control surface for the AI office.

## Priorities

1. Keep side effects explicit.
2. Require dry-run before risky mutation.
3. Keep secrets out of git.
4. Prefer durable job state over chat memory.
5. Keep skills small and role-specific.

## Required Inputs

- Load secrets from env files only.
- Do not commit chat IDs, tokens, passwords, or private URLs.
- Treat `openclaw.json.template`, `policies/`, `hooks/`, and `systemd/templates/` as privileged surfaces.

## Operating Rules

- Run `scripts/oc-audit` before rollout work.
- Use `scripts/oc-rollout --dry-run` before `--apply`.
- Do not mutate the VPS directly outside the control scripts unless handling an incident.
- Every incident fix should update a policy, script, or document here if the fix needs to persist.
