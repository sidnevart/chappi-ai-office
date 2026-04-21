#!/usr/bin/env python3
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policies"
DEFAULT_STATE_DIR = ROOT / ".runtime"
PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "unknown"


def state_dir() -> Path:
    return Path(os.environ.get("CONTROL_STATE_DIR", DEFAULT_STATE_DIR)).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    Path(temp_name).replace(path)


def append_jsonl(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def parse_scalar(value: str):
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value.strip("'\"")


def load_routes() -> dict:
    routes = {}
    current = None
    list_key = None
    for raw in (POLICY_DIR / "routing.yaml").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if text in {"version: 1", "routes:"}:
            continue
        if indent == 2 and text.endswith(":"):
            current = text[:-1]
            routes[current] = {}
            list_key = None
            continue
        if current is None:
            continue
        if indent == 4 and ":" in text:
            key, rest = text.split(":", 1)
            rest = rest.strip()
            if rest:
                routes[current][key] = parse_scalar(rest)
                list_key = None
            else:
                routes[current][key] = []
                list_key = key
            continue
        if indent == 6 and text.startswith("- ") and list_key:
            routes[current].setdefault(list_key, []).append(parse_scalar(text[2:]))
    return routes


def load_severity_policy() -> dict:
    severities = {}
    current = None
    for raw in (POLICY_DIR / "alert-severity.yaml").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if text in {"version: 1", "severity:"}:
            continue
        if indent == 2 and text.endswith(":"):
            current = text[:-1]
            severities[current] = {}
            continue
        if current and indent == 4 and ":" in text:
            key, rest = text.split(":", 1)
            severities[current][key] = parse_scalar(rest)
    return severities


def load_payload(source: str | None) -> dict:
    if source:
        if source.lstrip().startswith("{"):
            return json.loads(source)
        candidate = Path(source)
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
        return json.loads(source)
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)
    return {}


def emit(payload: dict, exit_code: int = 0) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    raise SystemExit(exit_code)


def bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def delivery_mode() -> str:
    return os.environ.get("CONTROL_DELIVERY_MODE", "dry-run")


def send_telegram_message(chat_id: str, token: str, text: str) -> tuple[bool, str]:
    encoded = parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode()
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    req = request.Request(endpoint, data=encoded, method="POST")
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        ok = bool(body.get("ok"))
        description = "telegram_sent" if ok else body.get("description", "telegram_failed")
        return ok, description
    except error.URLError as exc:
        return False, f"telegram_error:{exc.reason}"


def render_template(template_path: Path, output_path: Path) -> dict:
    template = template_path.read_text(encoding="utf-8")
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = os.environ.get(name)
        if value is None:
            missing.add(name)
            return match.group(0)
        return value

    rendered = PLACEHOLDER_RE.sub(replace, template)
    ensure_parent(output_path)
    output_path.write_text(rendered, encoding="utf-8")
    return {
        "missing": sorted(missing),
        "output": str(output_path),
        "template": str(template_path),
    }


def record_event(kind: str, payload: dict) -> None:
    append_jsonl(state_dir() / "events" / f"{kind}.jsonl", payload)


def handle_github_project_sync(payload: dict) -> dict:
    run_id = os.environ.get("RUN_ID", f"sync-{slug(payload.get('id', 'manual'))}")
    project_key = str(payload.get("project_key") or os.environ.get("GITHUB_PROJECT_ID") or "unknown-project")
    item_id = str(
        payload.get("item_id")
        or payload.get("id")
        or payload.get("project_item", {}).get("id")
        or f"item-{run_id}"
    )
    title = payload.get("title") or payload.get("project_item", {}).get("title") or ""
    repository = payload.get("repository") or payload.get("repo") or ""
    project_status = payload.get("status") or payload.get("project_status") or "new"
    session_key = payload.get("session_key") or f"sdlc:{project_key}:{item_id}"
    missing = []
    if not title:
        missing.append("title")
    if not repository:
        missing.append("repository")

    job_state = {
        "job_id": payload.get("job_id") or f"{project_key}-{item_id}",
        "item_id": item_id,
        "issue_url": payload.get("issue_url") or payload.get("url") or "",
        "kind": "sdlc_job",
        "missing_fields": missing,
        "owner": "sdlc-orchestrator",
        "project_key": project_key,
        "project_item_id": payload.get("project_item_id") or payload.get("project_item", {}).get("id") or "",
        "project_number": payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER", ""),
        "project_owner": payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER", ""),
        "repository": repository,
        "run_id": run_id,
        "session_key": session_key,
        "state": "intake_needed" if missing else "synced",
        "status": project_status,
        "title": title,
        "updated_at": now_iso(),
    }
    state_path = state_dir() / "jobs" / "sdlc" / slug(project_key) / f"{slug(item_id)}.json"
    atomic_write_json(state_path, job_state)
    record_event(
        "github-project-sync",
        {
            "event_type": "github.project_item.changed",
            "item_id": item_id,
            "project_key": project_key,
            "run_id": run_id,
            "state": job_state["state"],
            "timestamp": now_iso(),
        },
    )
    return {
        "job_id": job_state["job_id"],
        "run_id": run_id,
        "session_key": session_key,
        "state_path": str(state_path),
        "status": "ok",
        "summary": f"synced github project item {item_id} as {job_state['state']}",
    }


def format_spec_message(payload: dict, approval_id: str) -> str:
    title = payload.get("title") or "Спека готова к ревью"
    doc_url = payload.get("doc_url") or payload.get("spec_url") or "doc-url-missing"
    summary = payload.get("summary") or "Краткое описание не передано."
    project_key = payload.get("project_key") or "project-missing"
    item_id = payload.get("item_id") or payload.get("spec_id") or "item-missing"
    run_id = os.environ.get("RUN_ID", payload.get("run_id") or f"spec-{slug(title)}")
    next_action = payload.get("next_action") or f"Проверь документ и дай решение по approval `{approval_id}` до старта реализации."
    return "\n".join(
        [
            "📋 OpenClaw: спека на ревью",
            "",
            "🟡 Статус: ждет решения",
            f"🧩 Задача: {title}",
            f"📁 Проект: {project_key}",
            f"🔖 Item: {item_id}",
            f"✅ Approval: `{approval_id}`",
            f"🧵 Run: `{run_id}`",
            f"📄 Документ: {doc_url}",
            "",
            "📝 Кратко:",
            summary,
            "",
            "👉 Что сделать:",
            next_action,
        ]
    )


def severity_emoji(severity: str) -> str:
    return {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }.get(severity, "🟡")


def format_alert_message(payload: dict, severity: str, run_id: str, dedupe_key: str, count: int) -> str:
    summary = payload.get("summary") or "Краткое описание не передано"
    system = payload.get("system") or "runtime"
    event_type = payload.get("event_type") or "runtime.alert"
    correlation_id = payload.get("correlation_id") or run_id
    next_action = payload.get("next_action") or "Проверь состояние runtime и последние события"
    evidence = payload.get("evidence") or payload.get("details") or ""
    emoji = severity_emoji(severity)
    lines = [
        f"{emoji} OpenClaw: алерт [{severity.upper()}]",
        "",
        f"⚠️ Суть: {summary}",
        f"🧱 Система: {system}",
        f"📌 Событие: {event_type}",
        f"🔗 Correlation: `{correlation_id}`",
        f"🧵 Run: `{run_id}`",
        f"🔁 Dedupe: `{dedupe_key}`",
        f"📊 Повторов: {count}",
        "",
        "👉 Что сделать:",
        next_action,
    ]
    if evidence:
        lines.extend(["", "🔎 Детали:", str(evidence)[:1200]])
    return "\n".join(lines)


def handle_spec_review_publish(payload: dict) -> dict:
    routes = load_routes()
    route = routes.get("specs", {})
    run_id = os.environ.get("RUN_ID", f"spec-{slug(payload.get('title', 'manual'))}")
    item_id = str(payload.get("item_id") or payload.get("spec_id") or run_id)
    approval_id = str(payload.get("approval_id") or f"spec-{slug(item_id)}")
    session_key = payload.get("session_key") or f"approval:{approval_id}"
    message = format_spec_message(payload, approval_id)
    chat_env = route.get("channel_env", "TELEGRAM_SPECS_CHAT_ID")
    chat_id = os.environ.get(chat_env, "")
    delivery = "dry_run"
    reason = "dry_run_default"

    approval_state = {
        "approval_class": "explicit_approval",
        "approval_id": approval_id,
        "created_at": now_iso(),
        "delivery_route": "specs",
        "item_id": item_id,
        "job_id": payload.get("job_id"),
        "project_key": payload.get("project_key"),
        "run_id": run_id,
        "session_key": session_key,
        "status": "approved" if bool_env("CONTROL_APPROVED") else "pending",
        "title": payload.get("title") or "Spec ready for review",
    }
    atomic_write_json(state_dir() / "approvals" / f"{slug(approval_id)}.json", approval_state)

    outbox_payload = {
        "approval_id": approval_id,
        "chat_env": chat_env,
        "chat_id_present": bool(chat_id),
        "message": message,
        "route": "specs",
        "run_id": run_id,
        "timestamp": now_iso(),
    }
    atomic_write_json(state_dir() / "outbox" / "specs" / f"{slug(run_id)}.json", outbox_payload)

    if delivery_mode() == "apply":
        token = os.environ.get("OPENCLAW_TG_BOT", "")
        if not bool_env("CONTROL_APPROVED"):
            delivery = "blocked"
            reason = "explicit_approval_required"
        elif not chat_id:
            delivery = "blocked"
            reason = f"missing_env:{chat_env}"
        elif not token:
            delivery = "blocked"
            reason = "missing_env:OPENCLAW_TG_BOT"
        else:
            sent, reason = send_telegram_message(chat_id, token, message)
            delivery = "sent" if sent else "failed"

    record_event(
        "spec-review-publish",
        {
            "approval_id": approval_id,
            "delivery": delivery,
            "reason": reason,
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    return {
        "approval_id": approval_id,
        "delivery_status": delivery,
        "reason": reason,
        "run_id": run_id,
        "session_key": session_key,
        "status": "ok" if delivery != "failed" else "error",
        "summary": f"prepared spec review publication for {approval_id}",
    }


def handle_alert_route(payload: dict) -> dict:
    routes = load_routes()
    severity_policy = load_severity_policy()
    route = routes.get("alerts", {})
    severity = str(payload.get("severity") or "medium").lower()
    if severity not in severity_policy:
        severity = "medium"
    run_id = os.environ.get("RUN_ID", f"alert-{slug(payload.get('event_type', 'manual'))}")
    dedupe_window = int(severity_policy[severity].get("dedupe_window_seconds", 300))
    dedupe_key = payload.get("dedupe_key") or slug(
        f"{payload.get('system', 'runtime')}-{payload.get('event_type', 'alert')}-{payload.get('summary', 'no-summary')}"
    )
    dedupe_path = state_dir() / "alerts" / "dedupe" / f"{dedupe_key}.json"
    now = datetime.now(timezone.utc)
    previous = {}
    if dedupe_path.exists():
        previous = json.loads(dedupe_path.read_text(encoding="utf-8"))

    suppressed = False
    count = int(previous.get("count", 0))
    last_seen = previous.get("last_seen")
    if last_seen:
        age_seconds = int((now - datetime.fromisoformat(last_seen.replace("Z", "+00:00"))).total_seconds())
        if age_seconds < dedupe_window:
            suppressed = True

    count += 1
    dedupe_state = {
        "count": count,
        "dedupe_key": dedupe_key,
        "last_seen": now_iso(),
        "severity": severity,
        "window_seconds": dedupe_window,
    }
    atomic_write_json(dedupe_path, dedupe_state)

    chat_env = route.get("channel_env", "TELEGRAM_ALERTS_CHAT_ID")
    chat_id = os.environ.get(chat_env, "")
    message = format_alert_message(payload, severity, run_id, dedupe_key, count)

    delivery = "suppressed" if suppressed else "dry_run"
    reason = "dedupe_window_active" if suppressed else "dry_run_default"
    if not suppressed and delivery_mode() == "apply":
        token = os.environ.get("OPENCLAW_TG_BOT", "")
        if not chat_id:
            delivery = "blocked"
            reason = f"missing_env:{chat_env}"
        elif not token:
            delivery = "blocked"
            reason = "missing_env:OPENCLAW_TG_BOT"
        else:
            sent, reason = send_telegram_message(chat_id, token, message)
            delivery = "sent" if sent else "failed"

    alert_event = {
        "correlation_id": payload.get("correlation_id", run_id),
        "dedupe_key": dedupe_key,
        "delivery_status": delivery,
        "event_type": payload.get("event_type", "runtime.alert"),
        "message": message,
        "next_action": payload.get("next_action", "Inspect runtime state"),
        "reason": reason,
        "run_id": run_id,
        "severity": severity,
        "summary": payload.get("summary", "No summary provided"),
        "system": payload.get("system", "runtime"),
        "timestamp": now_iso(),
    }
    atomic_write_json(state_dir() / "alerts" / "events" / f"{slug(run_id)}.json", alert_event)
    record_event("alert-route", alert_event)
    return {
        "dedupe_key": dedupe_key,
        "delivery_status": delivery,
        "reason": reason,
        "run_id": run_id,
        "status": "ok" if delivery != "failed" else "error",
        "summary": f"processed alert {dedupe_key}",
    }


def sync_tree(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in [
        "README.md",
        "openclaw.json.template",
        "docs",
        "examples",
        "hooks",
        "lib",
        "policies",
        "scripts",
        "skills",
        "systemd",
        "tests",
    ]:
        source = ROOT / name
        target = destination / name
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            ensure_parent(target)
            shutil.copy2(source, target)
        copied.append(name)
    return {"copied": copied, "destination": str(destination)}


def main() -> None:
    if len(sys.argv) < 2:
        emit({"status": "error", "summary": "missing command"}, exit_code=1)

    command = sys.argv[1]
    if command == "render-config":
        if len(sys.argv) != 4:
            emit({"status": "error", "summary": "usage: render-config <template> <output>"}, exit_code=1)
        result = render_template(Path(sys.argv[2]), Path(sys.argv[3]))
        result["status"] = "ok" if not result["missing"] else "error"
        result["summary"] = "rendered config template"
        emit(result, exit_code=0 if not result["missing"] else 2)

    if command == "sync-tree":
        if len(sys.argv) != 3:
            emit({"status": "error", "summary": "usage: sync-tree <destination>"}, exit_code=1)
        result = sync_tree(Path(sys.argv[2]).expanduser())
        result["status"] = "ok"
        result["summary"] = "synced control-plane tree"
        emit(result)

    payload = load_payload(sys.argv[2] if len(sys.argv) > 2 else None)
    handlers = {
        "github-project-sync": handle_github_project_sync,
        "spec-review-publish": handle_spec_review_publish,
        "alert-route": handle_alert_route,
    }
    handler = handlers.get(command)
    if handler is None:
        emit({"status": "error", "summary": f"unknown command: {command}"}, exit_code=1)
    emit(handler(payload))


if __name__ == "__main__":
    main()
