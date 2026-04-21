# Research Workflows

OpenClaw research jobs are durable workflows, not chat memory.

## Contract

Every research job starts with an interview and remains blocked until these fields are complete:

- `sources`
- `filters_metrics`
- `schedule`
- `output_format`
- `output_schema`
- `delivery_route`
- `stop_conditions`

## Commands

```bash
openclaw-control/scripts/oc-research start-interview payload.json
openclaw-control/scripts/oc-research update-intake <job-id> answers.json
openclaw-control/scripts/oc-research create-job <job-id>
openclaw-control/scripts/oc-research run-job <job-id>
openclaw-control/scripts/oc-research digest <job-id> <run-id>
openclaw-control/scripts/oc-research run-due
openclaw-control/scripts/oc-research pause <job-id>
openclaw-control/scripts/oc-research resume <job-id>
openclaw-control/scripts/oc-research stop <job-id>
openclaw-control/scripts/oc-research status <job-id>
```

## State

- Intake: `state/research/intake/<job-id>.json`
- Job: `state/jobs/research/<job-id>.json`
- Agent inventory: `state/agents/research/<job-id>.json`
- Results: `state/research/results/<job-id>/<run-id>.json`
- Digests: `state/research/digests/<job-id>/<run-id>.json`
- Dedupe: `state/research/dedupe/<job-id>.json`
- Events: `state/events/research-*.jsonl`

The agent inventory file gives the Office UI a stable source for future visualization: agent id, role, zone, active job id, session key, lifecycle status, and heartbeat.

## Telegram Control

Telegram handlers should map human commands to deterministic lifecycle commands:

- `pause <job-id>` -> `oc-research pause <job-id>`
- `resume <job-id>` -> `oc-research resume <job-id>`
- `stop <job-id>` -> `oc-research stop <job-id>`
- `status <job-id>` -> `oc-research status <job-id>`

Do not let Telegram free text create jobs directly. Free text can update intake answers, but `create-job` must still validate the required fields.

## Runner Contract

`run-job` fetches configured sources, extracts candidate links, applies deterministic filters, writes durable results, updates the research agent heartbeat, and records a run event. Current production-safe source types are local files and HTTP/HTTPS pages. The runner does not bypass anti-bot systems and does not scrape behind logins.

`digest` renders a Russian operator-friendly message with emoji, counts, warnings, and top links. Delivery is still a separate route/approval concern; digest generation only prepares the artifact.

`run-due` scans active jobs and runs jobs whose simple schedule is due. The systemd timer calls this command periodically; the job remains stoppable through `pause`, `resume`, and `stop`.

## Examples

Apartment search fields should include budget, geography, commute constraints, rooms, excluded listings, output columns, cadence, digest route, and stop conditions.

Startup discovery fields should include stage, geography, verticals, funding signals, traction signals, source priority, output columns, cadence, digest route, and stop conditions.

Trend scouting fields should include topics, source classes, freshness window, ranking signals, output columns, cadence, digest route, and stop conditions.
