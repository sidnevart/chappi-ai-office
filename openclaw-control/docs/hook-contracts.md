# Hook Contracts

Every hook entry must define:

- `id`: stable hook identifier.
- `event`: gateway or workflow event.
- `owner`: responsible agent or operator.
- `handler`: script or command path.
- `timeout_seconds`
- `retry_policy`
- `approval_class`
- `input_schema`
- `delivery`

## Guardrails

- Hooks run with a dedicated hook token and restricted env.
- Hook handlers do not accept free-form session keys from untrusted input.
- Handlers must emit structured result JSON with `status`, `run_id`, and `summary`.
- Failed hooks route to the alerts channel with dedupe metadata.
- Payload input is JSON via stdin or a fixture/file path argument.
- Handlers write durable state under `CONTROL_STATE_DIR` or `openclaw-control/.runtime`.
- GitHub Projects v2 item webhooks should be normalized first into
  `github_project_item_v1` before `github-project-sync` runs.
