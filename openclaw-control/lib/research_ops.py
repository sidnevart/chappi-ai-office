#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request

from control_plane import atomic_write_json, load_payload, now_iso, record_event, slug, state_dir


REQUIRED_INTAKE_FIELDS = [
    "sources",
    "filters_metrics",
    "schedule",
    "output_format",
    "output_schema",
    "delivery_route",
    "stop_conditions",
]

SOURCE_SUGGESTIONS = {
    "apartment_search": [
        "listing marketplaces",
        "agency sites",
        "Telegram channels",
        "map and commute data",
        "building review sources",
    ],
    "startup_discovery": [
        "Product Hunt",
        "Crunchbase or Dealroom",
        "GitHub trending",
        "accelerator cohorts",
        "funding and tech news",
    ],
    "trend_scouting": [
        "Google Trends",
        "industry newsletters",
        "GitHub repositories",
        "arXiv or papers",
        "social discussion sources",
    ],
    "structured": [
        "primary source websites",
        "news and RSS feeds",
        "public databases",
        "expert/community sources",
    ],
}


QUESTION_BY_FIELD = {
    "sources": "Which sources are allowed, and which sources should be excluded?",
    "filters_metrics": "What filters and ranking metrics should be applied?",
    "schedule": "What cadence or cron schedule should run this job?",
    "output_format": "Should output be links, table, spreadsheet, Telegram digest, or a combination?",
    "output_schema": "Which columns or fields must be stored for each result?",
    "delivery_route": "Where should digests or alerts be delivered?",
    "stop_conditions": "When should this job stop or ask for confirmation?",
}


def research_root() -> Path:
    return state_dir() / "research"


def intake_path(job_id: str) -> Path:
    return research_root() / "intake" / f"{slug(job_id)}.json"


def job_path(job_id: str) -> Path:
    return state_dir() / "jobs" / "research" / f"{slug(job_id)}.json"


def agent_path(job_id: str) -> Path:
    return state_dir() / "agents" / "research" / f"{slug(job_id)}.json"


def results_dir(job_id: str) -> Path:
    return research_root() / "results" / slug(job_id)


def result_path(job_id: str, run_id: str) -> Path:
    return results_dir(job_id) / f"{slug(run_id)}.json"


def digest_path(job_id: str, run_id: str) -> Path:
    return research_root() / "digests" / slug(job_id) / f"{slug(run_id)}.json"


def dedupe_path(job_id: str) -> Path:
    return research_root() / "dedupe" / f"{slug(job_id)}.json"


def missing_fields(intake: dict) -> list[str]:
    missing = []
    for field in REQUIRED_INTAKE_FIELDS:
        value = intake.get(field)
        if value in (None, "", [], {}):
            missing.append(field)
    return missing


def next_questions(missing: list[str]) -> list[str]:
    return [QUESTION_BY_FIELD[field] for field in missing if field in QUESTION_BY_FIELD]


def load_intake(job_id: str) -> dict:
    path = intake_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"research intake not found: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_job(job_id: str) -> dict:
    path = job_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"research job not found: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_text(source: str) -> tuple[str, str]:
    parsed = parse.urlparse(source)
    if parsed.scheme == "file":
        path = Path(parse.unquote(parsed.path))
        return path.read_text(encoding="utf-8"), source
    if parsed.scheme in {"http", "https"}:
        req = request.Request(source, headers={"User-Agent": "OpenClawResearch/1.0"})
        with request.urlopen(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), source
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8"), path.resolve().as_uri()
    raise ValueError(f"unsupported research source: {source}")


def extract_links(html: str, base_url: str) -> list[dict]:
    matches = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.IGNORECASE | re.DOTALL)
    results = []
    for href, raw_text in matches:
        text = re.sub(r"<[^>]+>", " ", raw_text)
        text = re.sub(r"\s+", " ", text).strip()
        url = parse.urljoin(base_url, href.strip())
        if not text and not url:
            continue
        results.append({"source_url": base_url, "text": text, "url": url})
    return results


def parse_price(text: str) -> int | None:
    normalized = text.replace("\xa0", " ")
    candidates = re.findall(r"(\d[\d\s]{3,})\s*(?:₽|руб|р|rub)?", normalized, flags=re.IGNORECASE)
    prices = []
    for candidate in candidates:
        digits = re.sub(r"\D", "", candidate)
        if digits:
            prices.append(int(digits))
    return max(prices) if prices else None


def filters_match(item: dict, filters: dict) -> bool:
    text = str(item.get("text") or "")
    price = parse_price(text)
    item["price"] = price
    budget_max = filters.get("budget_max") or filters.get("max_budget")
    if budget_max and price is not None and price > int(budget_max):
        return False
    budget_min = filters.get("budget_min") or filters.get("min_budget")
    if budget_min and price is not None and price < int(budget_min):
        return False
    keywords = filters.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    if keywords and not any(str(keyword).lower() in text.lower() for keyword in keywords):
        return False
    exclude_keywords = filters.get("exclude_keywords") or []
    if isinstance(exclude_keywords, str):
        exclude_keywords = [exclude_keywords]
    if exclude_keywords and any(str(keyword).lower() in text.lower() for keyword in exclude_keywords):
        return False
    return True


def result_id(item: dict) -> str:
    return hashlib.sha256(str(item.get("url") or item.get("text") or "").encode("utf-8")).hexdigest()[:16]


def start_interview(payload_path: str | None) -> int:
    payload = load_payload(payload_path)
    job_type = payload.get("job_type") or "structured"
    job_id = str(payload.get("job_id") or f"research-{slug(job_type)}")
    run_id = os.environ.get("RUN_ID", f"research-interview-{slug(job_id)}")
    intake = {
        "created_at": now_iso(),
        "job_id": job_id,
        "job_type": job_type,
        "missing_fields": REQUIRED_INTAKE_FIELDS,
        "next_questions": next_questions(REQUIRED_INTAKE_FIELDS),
        "requested_by": payload.get("requested_by") or "openclaw",
        "run_id": run_id,
        "session_key": payload.get("session_key") or f"research:{slug(job_id)}:intake",
        "source_suggestions": SOURCE_SUGGESTIONS.get(job_type, SOURCE_SUGGESTIONS["structured"]),
        "state": "interviewing",
        "title": payload.get("title") or f"{job_type.replace('_', ' ').title()} research",
        "updated_at": now_iso(),
    }
    for field in REQUIRED_INTAKE_FIELDS:
        if field in payload:
            intake[field] = payload[field]
    intake["missing_fields"] = missing_fields(intake)
    intake["next_questions"] = next_questions(intake["missing_fields"])
    atomic_write_json(intake_path(job_id), intake)
    record_event(
        "research-intake",
        {
            "event_type": "research.interview.started",
            "job_id": job_id,
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "job_id": job_id,
                "missing_fields": intake["missing_fields"],
                "next_questions": intake["next_questions"],
                "source_suggestions": intake["source_suggestions"],
                "state_path": str(intake_path(job_id)),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


def update_intake(job_id: str, payload_path: str | None) -> int:
    intake = load_intake(job_id)
    patch = load_payload(payload_path)
    for key, value in patch.items():
        if key not in {"job_id", "created_at"}:
            intake[key] = value
    intake["updated_at"] = now_iso()
    intake["missing_fields"] = missing_fields(intake)
    intake["next_questions"] = next_questions(intake["missing_fields"])
    intake["state"] = "ready_to_create" if not intake["missing_fields"] else "interviewing"
    atomic_write_json(intake_path(job_id), intake)
    record_event(
        "research-intake",
        {
            "event_type": "research.interview.updated",
            "job_id": job_id,
            "missing_fields": intake["missing_fields"],
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "job_id": job_id,
                "missing_fields": intake["missing_fields"],
                "next_questions": intake["next_questions"],
                "state": intake["state"],
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


def create_job(job_id: str) -> int:
    intake = load_intake(job_id)
    missing = missing_fields(intake)
    if missing:
        print(
            json.dumps(
                {
                    "job_id": job_id,
                    "missing_fields": missing,
                    "next_questions": next_questions(missing),
                    "status": "blocked",
                    "summary": "research job cannot be created until intake is complete",
                },
                sort_keys=True,
            )
        )
        return 2
    run_id = os.environ.get("RUN_ID", f"research-job-{slug(job_id)}")
    session_key = intake.get("session_key") or f"research:{slug(job_id)}"
    job = {
        "delivery_route": intake["delivery_route"],
        "filters_metrics": intake["filters_metrics"],
        "job_id": job_id,
        "job_type": intake.get("job_type") or "structured",
        "kind": "research_job",
        "missing_fields": [],
        "output_format": intake["output_format"],
        "output_schema": intake["output_schema"],
        "owner": f"research-agent:{slug(job_id)}",
        "run_id": run_id,
        "schedule": intake["schedule"],
        "session_key": session_key,
        "sources": intake["sources"],
        "state": "scheduled",
        "status": "active",
        "stop_conditions": intake["stop_conditions"],
        "title": intake.get("title") or f"Research job {job_id}",
        "updated_at": now_iso(),
    }
    agent = {
        "active_job_id": job_id,
        "agent_id": f"research-agent-{slug(job_id)}",
        "heartbeat_at": now_iso(),
        "lifecycle_status": "active",
        "role": "research-agent",
        "session_key": session_key,
        "state": "waiting",
        "zone": "research",
    }
    atomic_write_json(job_path(job_id), job)
    atomic_write_json(agent_path(job_id), agent)
    record_event(
        "research-job",
        {
            "event_type": "research.job.created",
            "job_id": job_id,
            "run_id": run_id,
            "session_key": session_key,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"agent_id": agent["agent_id"], "job_id": job_id, "state": "scheduled", "status": "ok"}, sort_keys=True))
    return 0


def set_lifecycle(job_id: str, action: str) -> int:
    path = job_path(job_id)
    if not path.exists():
        print(json.dumps({"job_id": job_id, "status": "error", "summary": "research job not found"}, sort_keys=True))
        return 1
    job = json.loads(path.read_text(encoding="utf-8"))
    agent = json.loads(agent_path(job_id).read_text(encoding="utf-8")) if agent_path(job_id).exists() else {}
    if action == "pause":
        job["status"] = "paused"
        job["state"] = "paused"
        agent["state"] = "waiting"
        agent["lifecycle_status"] = "paused"
    elif action == "resume":
        job["status"] = "active"
        job["state"] = "scheduled"
        agent["state"] = "waiting"
        agent["lifecycle_status"] = "active"
    elif action == "stop":
        job["status"] = "stopped"
        job["state"] = "stopped"
        agent["state"] = "idle"
        agent["lifecycle_status"] = "stopped"
    else:
        print(json.dumps({"status": "error", "summary": f"unknown lifecycle action: {action}"}, sort_keys=True))
        return 1
    job["updated_at"] = now_iso()
    agent["heartbeat_at"] = now_iso()
    atomic_write_json(path, job)
    if agent:
        atomic_write_json(agent_path(job_id), agent)
    record_event(
        "research-job",
        {
            "event_type": f"research.job.{action}",
            "job_id": job_id,
            "status": job["status"],
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"job_id": job_id, "state": job["state"], "status": "ok"}, sort_keys=True))
    return 0


def run_job(job_id: str) -> int:
    job = load_job(job_id)
    if job.get("status") != "active":
        print(json.dumps({"job_id": job_id, "status": "blocked", "summary": f"job status is {job.get('status')}"}, sort_keys=True))
        return 2
    run_id = os.environ.get("RUN_ID", f"research-run-{slug(job_id)}")
    filters = job.get("filters_metrics") or {}
    sources = job.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]
    warnings = []
    found = []
    seen_urls = set()
    previous = {}
    if dedupe_path(job_id).exists():
        previous = json.loads(dedupe_path(job_id).read_text(encoding="utf-8"))
    previous_ids = set(previous.get("seen_result_ids") or [])

    for source in sources:
        try:
            text, base_url = load_source_text(str(source))
            for item in extract_links(text, base_url):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                if not filters_match(item, filters):
                    continue
                item["result_id"] = result_id(item)
                item["is_new"] = item["result_id"] not in previous_ids
                item["captured_at"] = now_iso()
                found.append(item)
        except Exception as exc:  # noqa: BLE001 - source failures should not kill the whole job.
            warnings.append({"source": str(source), "summary": str(exc)})

    payload = {
        "filters_metrics": filters,
        "job_id": job_id,
        "result_count": len(found),
        "results": found,
        "run_id": run_id,
        "sources": sources,
        "status": "ok",
        "warnings": warnings,
        "fetched_at": now_iso(),
    }
    atomic_write_json(result_path(job_id, run_id), payload)
    atomic_write_json(
        dedupe_path(job_id),
        {
            "job_id": job_id,
            "seen_result_ids": sorted(previous_ids | {item["result_id"] for item in found}),
            "updated_at": now_iso(),
        },
    )
    job["last_run_at"] = now_iso()
    job["last_run_id"] = run_id
    job["last_result_count"] = len(found)
    job["state"] = "ran"
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(job_id), job)
    if agent_path(job_id).exists():
        agent = json.loads(agent_path(job_id).read_text(encoding="utf-8"))
        agent["heartbeat_at"] = now_iso()
        agent["state"] = "waiting"
        atomic_write_json(agent_path(job_id), agent)
    record_event(
        "research-run",
        {
            "event_type": "research.job.ran",
            "job_id": job_id,
            "result_count": len(found),
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"job_id": job_id, "result_count": len(found), "run_id": run_id, "status": "ok"}, sort_keys=True))
    return 0


def render_digest(job: dict, result_payload: dict) -> str:
    results = result_payload.get("results") or []
    title = job.get("title") or job.get("job_id") or "Research"
    icon = "🏠" if job.get("job_type") == "apartment_search" else "🔎"
    lines = [
        f"{icon} OpenClaw Research",
        "",
        f"📌 Задача: {title}",
        f"🧵 Run: `{result_payload.get('run_id')}`",
        f"📊 Найдено: {len(results)}",
    ]
    warnings = result_payload.get("warnings") or []
    if warnings:
        lines.append(f"⚠️ Источники с ошибками: {len(warnings)}")
    lines.extend(["", "🔗 Результаты:"])
    if not results:
        lines.append("Новых подходящих результатов нет.")
    for index, item in enumerate(results[:10], start=1):
        price = item.get("price")
        price_text = f" · {price} ₽" if price else ""
        lines.append(f"{index}. {item.get('text') or 'Без названия'}{price_text}")
        lines.append(f"   {item.get('url')}")
    if len(results) > 10:
        lines.append(f"... еще {len(results) - 10}")
    return "\n".join(lines)


def digest(job_id: str, run_id: str) -> int:
    job = load_job(job_id)
    result_file = result_path(job_id, run_id)
    if not result_file.exists():
        print(json.dumps({"job_id": job_id, "run_id": run_id, "status": "error", "summary": "research result not found"}, sort_keys=True))
        return 1
    result_payload = json.loads(result_file.read_text(encoding="utf-8"))
    message = render_digest(job, result_payload)
    payload = {
        "delivery_route": job.get("delivery_route"),
        "job_id": job_id,
        "message": message,
        "result_path": str(result_file),
        "run_id": run_id,
        "status": "prepared",
        "timestamp": now_iso(),
    }
    atomic_write_json(digest_path(job_id, run_id), payload)
    record_event(
        "research-digest",
        {
            "event_type": "research.digest.prepared",
            "job_id": job_id,
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"digest_path": str(digest_path(job_id, run_id)), "job_id": job_id, "run_id": run_id, "status": "ok"}, sort_keys=True))
    return 0


def cron_due(schedule: str, last_run_at: str | None) -> bool:
    if not last_run_at:
        return True
    try:
        last = datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    now = datetime.now(timezone.utc)
    if schedule in {"@daily", "daily"}:
        return last.date() != now.date()
    if schedule in {"@hourly", "hourly"}:
        return last.strftime("%Y-%m-%dT%H") != now.strftime("%Y-%m-%dT%H")
    return False


def run_due() -> int:
    jobs_dir = state_dir() / "jobs" / "research"
    ran = []
    if jobs_dir.exists():
        for path in sorted(jobs_dir.glob("*.json")):
            job = json.loads(path.read_text(encoding="utf-8"))
            if job.get("status") == "active" and cron_due(str(job.get("schedule") or ""), job.get("last_run_at")):
                run_job(str(job["job_id"]))
                ran.append(job["job_id"])
    print(json.dumps({"ran": ran, "status": "ok"}, sort_keys=True))
    return 0


def show_status(job_id: str) -> int:
    payload = {
        "agent": json.loads(agent_path(job_id).read_text(encoding="utf-8")) if agent_path(job_id).exists() else None,
        "intake": json.loads(intake_path(job_id).read_text(encoding="utf-8")) if intake_path(job_id).exists() else None,
        "job": json.loads(job_path(job_id).read_text(encoding="utf-8")) if job_path(job_id).exists() else None,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: research_ops.py <start-interview|update-intake|create-job|run-job|digest|run-due|pause|resume|stop|status> ...", file=sys.stderr)
        return 1
    command = sys.argv[1]
    if command == "start-interview":
        return start_interview(sys.argv[2] if len(sys.argv) > 2 else None)
    if command == "update-intake":
        return update_intake(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    if command == "create-job":
        return create_job(sys.argv[2])
    if command == "run-job":
        return run_job(sys.argv[2])
    if command == "digest":
        return digest(sys.argv[2], sys.argv[3])
    if command == "run-due":
        return run_due()
    if command in {"pause", "resume", "stop"}:
        return set_lifecycle(sys.argv[2], command)
    if command == "status":
        return show_status(sys.argv[2])
    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
