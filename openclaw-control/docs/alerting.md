# Alerting

## Channels

- `alerts`: runtime, hook, service, and workflow failures.
- `specs`: spec review requests.
- `prs`: CI-passed PR digests.
- `research`: recurring research digests.

## Payload

Each alert includes:

- `severity`
- `system`
- `event_type`
- `correlation_id`
- `job_id` or `session_key`
- `summary`
- `evidence`
- `next_action`
- `dedupe_key`

## Dedupe

- Suppress identical alerts within a short window.
- Re-emit with higher severity when count or duration crosses thresholds.
- Do not send raw multiline logs without truncation and context.

## Operator Message Format

Alerts are written in Russian for human Telegram groups and include emoji, severity, summary, system, event type, correlation id, run id, dedupe key, seen count, next action, and bounded evidence.

Spec and PR messages use the same Russian operator pattern: message type, current status, title, project, item, approval id, run id, link, summary, and explicit next action.
