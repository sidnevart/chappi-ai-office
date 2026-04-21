#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from control_plane import atomic_write_json, now_iso, record_event, send_telegram_message, slug, state_dir

ROOT = Path(__file__).resolve().parents[1]


def approval_path(approval_id: str) -> Path:
    return state_dir() / "approvals" / f"{approval_id}.json"


def job_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "jobs" / "sdlc" / slug(project_key) / f"{slug(item_id)}.json"


def load_approval(approval_id: str) -> dict:
    path = approval_path(approval_id)
    if not path.exists():
        raise FileNotFoundError(f"approval not found: {approval_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def bool_env(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def maybe_sync_project_status(job: dict, sdlc_state: str) -> None:
    owner = job.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER") or ""
    number = job.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER") or ""
    project_item_id = job.get("project_item_id") or ""
    issue_url = job.get("issue_url") or job.get("url") or ""
    if not owner or not number or not (project_item_id or issue_url):
        return
    payload = {
        "issue_url": issue_url,
        "project_item_id": project_item_id,
        "project_number": number,
        "project_owner": owner,
        "sdlc_state": sdlc_state,
        "task_id": job.get("job_id") or job.get("item_id") or project_item_id,
        "title": job.get("title") or "",
    }
    apply = bool_env("CONTROL_GITHUB_PROJECT_STATUS_APPLY")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False)
        payload_path = handle.name
    try:
        cmd = [str(ROOT / "scripts" / "oc-github-project"), "set-status"]
        if apply:
            cmd.append("--apply")
        cmd.append(payload_path)
        completed = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        record_event(
            "approval-github-project-status",
            {
                "apply": apply,
                "event_type": "approval.github_project.status_sync",
                "exit_code": completed.returncode,
                "item_id": job.get("item_id"),
                "project_key": job.get("project_key"),
                "sdlc_state": sdlc_state,
                "stderr": completed.stderr[-1000:],
                "stdout": completed.stdout[-1000:],
                "timestamp": now_iso(),
            },
        )
    finally:
        Path(payload_path).unlink(missing_ok=True)


def update_linked_job(approval: dict, status: str) -> None:
    project_key = approval.get("project_key")
    item_id = approval.get("item_id")
    if not project_key or not item_id:
        return
    path = job_path(project_key, item_id)
    if not path.exists():
        return
    job = json.loads(path.read_text(encoding="utf-8"))
    route = approval.get("delivery_route")
    if route == "specs":
        job["approval_status"] = status
        job["state"] = "spec_approved" if status == "approved" else "spec_changes_requested"
    elif route == "prs":
        job["pr_digest_status"] = status
        job["state"] = "pr_digest_approved" if status == "approved" else "pr_digest_blocked"
    job["updated_at"] = now_iso()
    atomic_write_json(path, job)
    maybe_sync_project_status(job, job["state"])


def list_approvals() -> int:
    approvals_dir = state_dir() / "approvals"
    approvals = []
    if approvals_dir.exists():
        for path in sorted(approvals_dir.glob("*.json")):
            approvals.append(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(approvals, indent=2, sort_keys=True))
    return 0


def resolve_approval(approval_id: str, status: str) -> int:
    approval = load_approval(approval_id)
    approval["status"] = status
    atomic_write_json(approval_path(approval_id), approval)
    update_linked_job(approval, status)
    record_event(
        "approval-status",
        {
            "approval_id": approval_id,
            "delivery_route": approval.get("delivery_route"),
            "item_id": approval.get("item_id"),
            "project_key": approval.get("project_key"),
            "status": status,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"approval_id": approval_id, "status": status}, sort_keys=True))
    return 0


def deliver(approval_id: str) -> int:
    approval = load_approval(approval_id)
    if approval.get("status") != "approved":
        print(json.dumps({"status": "error", "summary": f"approval {approval_id} is not approved"}))
        return 1
    route = approval.get("delivery_route")
    outbox_path = state_dir() / "outbox" / str(route) / f"{approval.get('run_id')}.json"
    if not outbox_path.exists():
        print(json.dumps({"status": "error", "summary": f"outbox not found for {approval_id}"}))
        return 1
    payload = json.loads(outbox_path.read_text(encoding="utf-8"))
    chat_id = os.environ.get(payload["chat_env"], "")
    token = os.environ.get("OPENCLAW_TG_BOT", "")
    if not chat_id or not token:
        print(json.dumps({"status": "error", "summary": "telegram env missing"}))
        return 1
    sent, reason = send_telegram_message(chat_id, token, payload["message"])
    result = {
        "approval_id": approval_id,
        "delivery_status": "sent" if sent else "failed",
        "reason": reason,
    }
    approval["delivery_status"] = result["delivery_status"]
    approval["delivered_at"] = now_iso() if sent else approval.get("delivered_at")
    atomic_write_json(approval_path(approval_id), approval)
    update_linked_job(approval, approval.get("status", "approved"))
    if sent and route == "prs":
        project_key = approval.get("project_key")
        item_id = approval.get("item_id")
        if project_key and item_id:
            path = job_path(project_key, item_id)
            if path.exists():
                job = json.loads(path.read_text(encoding="utf-8"))
                job["state"] = "ci_passed_notified"
                job["pr_digest_status"] = "sent"
                job["updated_at"] = now_iso()
                atomic_write_json(path, job)
                maybe_sync_project_status(job, "ci_passed_notified")
    record_event(
        "approval-delivery",
        {
            "approval_id": approval_id,
            "delivery_route": route,
            "delivery_status": result["delivery_status"],
            "reason": reason,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if sent else 1


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: approval_ops.py <list|approve|reject|deliver|deliver-spec> [args...]", file=sys.stderr)
        return 1
    command = sys.argv[1]
    if command == "list":
        return list_approvals()
    if command == "approve":
        return resolve_approval(sys.argv[2], "approved")
    if command == "reject":
        return resolve_approval(sys.argv[2], "rejected")
    if command in {"deliver", "deliver-spec"}:
        return deliver(sys.argv[2])
    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
