# Session Key Policy

- Human chat stays outside workflow namespaces.
- Hooks may only create sessions with approved prefixes.
- Workflow state stores `job_id`, `session_key`, and `owner_agent` together.
- Free-form session keys from external payloads are rejected.
- `approval:` sessions are short-lived and scoped to a single request.
