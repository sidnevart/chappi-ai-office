#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from control_plane import atomic_write_json, load_payload, now_iso, record_event, slug, state_dir


STATUS_BY_STATE = {
    "new": "Todo",
    "synced": "Todo",
    "intake_needed": "Todo",
    "tech_spec": "Tech Spec",
    "spec_ready": "Tech Spec",
    "awaiting_spec_approval": "Specification Review",
    "spec_changes_requested": "Specification Review",
    "spec_approved": "In Progress",
    "branch_bootstrapped": "In Progress",
    "coder_dry_run_ready": "In Progress",
    "implementing": "In Progress",
    "pr_open": "Code Review",
    "awaiting_pr_digest_approval": "Code Review",
    "pr_digest_approved": "Code Review",
    "ci_failed": "Testing",
    "testing": "Testing",
    "ci_passed_notified": "Done",
    "done": "Done",
}


def bool_env(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def task_state_path(task_id: str) -> Path:
    return state_dir() / "github-projects" / "tasks" / f"{slug(task_id)}.json"


def status_state_path(task_id: str) -> Path:
    return state_dir() / "github-projects" / "statuses" / f"{slug(task_id)}.json"


def canary_cleanup_path(issue_number: int | str) -> Path:
    return state_dir() / "github-projects" / "canary-cleanup" / f"issue-{issue_number}.json"


def render_issue_body(payload: dict) -> str:
    lines = [
        payload.get("body") or payload.get("summary") or "OpenClaw task intake placeholder.",
        "",
        "## OpenClaw Control",
        f"- Task type: `{payload.get('task_type') or 'sdlc'}`",
        f"- Requested by: `{payload.get('requested_by') or 'openclaw'}`",
        f"- Session key: `{payload.get('session_key') or 'sdlc:github-project:new'}`",
        "",
        "## Acceptance Criteria",
    ]
    criteria = payload.get("acceptance_criteria") or []
    if isinstance(criteria, str):
        criteria = [criteria]
    if criteria:
        lines.extend(f"- {item}" for item in criteria)
    else:
        lines.append("- Intake must capture acceptance criteria before implementation starts.")
    return "\n".join(lines).strip() + "\n"


def validate_payload(payload: dict) -> list[str]:
    missing = []
    for field in ["title", "repository"]:
        if not payload.get(field):
            missing.append(field)
    if not (payload.get("project_title") or payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER")):
        missing.append("project_title_or_project_number")
    if not (payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER")):
        missing.append("project_owner")
    return missing


def run_gh(args: list[str]) -> str:
    try:
        completed = subprocess.run(["gh", *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return completed.stdout.strip()
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(detail) from exc


def ensure_project_scope() -> None:
    completed = subprocess.run(["gh", "auth", "status"], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = completed.stdout
    scopes = set()
    scopes_line = next((line for line in output.splitlines() if "Token scopes:" in line), "")
    if scopes_line:
        scopes = {scope.strip() for scope in re.findall(r"'([^']+)'", scopes_line)}
    if "project" not in scopes:
        raise RuntimeError("gh auth is missing required scope: project. Run: gh auth refresh -s project")


def create_issue(payload: dict) -> str:
    title = payload["title"]
    repository = payload["repository"]
    body = render_issue_body(payload)
    args = ["issue", "create", "--repo", repository, "--title", title]
    labels = payload.get("labels") or []
    if isinstance(labels, str):
        labels = [labels]
    for label in labels:
        args.extend(["--label", str(label)])
    assignees = payload.get("assignees") or []
    if isinstance(assignees, str):
        assignees = [assignees]
    for assignee in assignees:
        args.extend(["--assignee", str(assignee)])
    if payload.get("project_title"):
        args.extend(["--project", str(payload["project_title"])])
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        body_path = handle.name
    try:
        args.extend(["--body-file", body_path])
        return run_gh(args)
    finally:
        Path(body_path).unlink(missing_ok=True)


def add_issue_to_project(payload: dict, issue_url: str) -> dict:
    project_number = payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER")
    owner = payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER")
    if not project_number:
        return {"status": "skipped", "reason": "project_title_used_or_project_number_missing"}
    output = run_gh(
        [
            "project",
            "item-add",
            str(project_number),
            "--owner",
            str(owner),
            "--url",
            issue_url,
            "--format",
            "json",
        ]
    )
    return json.loads(output) if output else {"status": "ok"}


def project_owner(payload: dict) -> str:
    return str(payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER") or "")


def project_number(payload: dict) -> str:
    return str(payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER") or "")


def project_fields(owner: str, number: str) -> dict:
    output = run_gh(["project", "field-list", str(number), "--owner", owner, "--format", "json"])
    return json.loads(output)


def project_items(owner: str, number: str, limit: int = 100) -> dict:
    output = run_gh(["project", "item-list", str(number), "--owner", owner, "--format", "json", "--limit", str(limit)])
    return json.loads(output)


def find_status_field(fields_payload: dict) -> tuple[str, dict[str, str], str]:
    for field in fields_payload.get("fields", []):
        if field.get("name") == "Status" and field.get("type") == "ProjectV2SingleSelectField":
            options = {option["name"]: option["id"] for option in field.get("options", [])}
            project_id = field.get("projectId") or fields_payload.get("projectId") or ""
            return field["id"], options, project_id
    raise RuntimeError("GitHub Project Status field not found")


def find_project_item(items_payload: dict, payload: dict) -> dict:
    expected_item_id = payload.get("project_item_id")
    expected_url = payload.get("issue_url") or payload.get("url")
    expected_title = payload.get("title")
    for item in items_payload.get("items", []):
        content = item.get("content") or {}
        if expected_item_id and item.get("id") == expected_item_id:
            return item
        if expected_url and content.get("url") == expected_url:
            return item
        if expected_title and item.get("title") == expected_title:
            return item
    raise RuntimeError("GitHub Project item not found by project_item_id, issue_url, or title")


def resolve_status(payload: dict) -> str:
    explicit = payload.get("project_status") or payload.get("status")
    if explicit in set(STATUS_BY_STATE.values()):
        return str(explicit)
    state = str(payload.get("sdlc_state") or payload.get("state") or explicit or "").strip()
    if state in STATUS_BY_STATE:
        return STATUS_BY_STATE[state]
    raise RuntimeError(f"unknown project status or SDLC state: {state}")


def set_status(payload_path: str | None, apply: bool = False) -> int:
    payload = load_payload(payload_path)
    run_id = os.environ.get("RUN_ID", f"github-project-status-{slug(payload.get('task_id', 'manual'))}")
    task_id = str(payload.get("task_id") or payload.get("issue_url") or payload.get("project_item_id") or run_id)
    owner = project_owner(payload)
    number = project_number(payload)
    mode = "apply" if apply else "dry-run"
    if not owner or not number:
        print(json.dumps({"missing_fields": ["project_owner", "project_number"], "status": "error"}, sort_keys=True))
        return 2
    try:
        target_status = resolve_status(payload)
    except RuntimeError as exc:
        print(json.dumps({"status": "error", "summary": str(exc)}, sort_keys=True))
        return 2

    item_id = payload.get("project_item_id") or ""
    field_id = ""
    option_id = ""
    project_id = payload.get("project_id") or ""
    issue_url = payload.get("issue_url") or payload.get("url") or ""
    title = payload.get("title") or ""

    if apply:
        try:
            ensure_project_scope()
            fields = project_fields(owner, number)
            field_id, options, project_id_from_fields = find_status_field(fields)
            project_id = project_id or project_id_from_fields or str(payload.get("project_id") or "")
            if target_status not in options:
                raise RuntimeError(f"project status option not found: {target_status}")
            option_id = options[target_status]
            if not item_id:
                item = find_project_item(project_items(owner, number), payload)
                item_id = item["id"]
                issue_url = issue_url or (item.get("content") or {}).get("url") or ""
                title = title or item.get("title") or ""
            if not project_id:
                project_list = json.loads(run_gh(["project", "list", "--owner", owner, "--format", "json", "--limit", "100"]))
                for project in project_list.get("projects", []):
                    if str(project.get("number")) == str(number):
                        project_id = project["id"]
                        break
            if not project_id:
                raise RuntimeError("GitHub Project id not found")
            run_gh(
                [
                    "project",
                    "item-edit",
                    "--id",
                    item_id,
                    "--project-id",
                    project_id,
                    "--field-id",
                    field_id,
                    "--single-select-option-id",
                    option_id,
                ]
            )
        except RuntimeError as exc:
            print(json.dumps({"mode": mode, "run_id": run_id, "status": "error", "summary": str(exc), "task_id": task_id}, sort_keys=True))
            return 1

    state = {
        "applied_at": now_iso() if apply else "",
        "field_id": field_id,
        "issue_url": issue_url,
        "mode": mode,
        "option_id": option_id,
        "project_id": project_id,
        "project_item_id": item_id,
        "project_number": number,
        "project_owner": owner,
        "project_status": target_status,
        "run_id": run_id,
        "source_state": payload.get("sdlc_state") or payload.get("state") or payload.get("status") or "",
        "status": "updated" if apply else "planned",
        "task_id": task_id,
        "title": title,
        "updated_at": now_iso(),
    }
    atomic_write_json(status_state_path(task_id), state)
    record_event(
        "github-project-status",
        {
            "event_type": "github.project.status.updated" if apply else "github.project.status.planned",
            "mode": mode,
            "project_status": target_status,
            "run_id": run_id,
            "task_id": task_id,
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "mode": mode,
                "project_status": target_status,
                "run_id": run_id,
                "state_path": str(status_state_path(task_id)),
                "status": "ok",
                "summary": "updated GitHub Project status" if apply else "prepared GitHub Project status update",
                "task_id": task_id,
            },
            sort_keys=True,
        )
    )
    return 0


def create_task(payload_path: str | None, apply: bool = False) -> int:
    payload = load_payload(payload_path)
    run_id = os.environ.get("RUN_ID", f"github-task-{slug(payload.get('title', 'manual'))}")
    task_id = str(payload.get("task_id") or run_id)
    missing = validate_payload(payload)
    mode = "apply" if apply else "dry-run"
    issue_url = ""
    project_result = {}

    if missing:
        result = {
            "missing_fields": missing,
            "mode": mode,
            "run_id": run_id,
            "status": "error",
            "summary": "github project task payload is incomplete",
            "task_id": task_id,
        }
        print(json.dumps(result, sort_keys=True))
        return 2

    if apply:
        try:
            ensure_project_scope()
            issue_url = create_issue(payload)
            project_result = add_issue_to_project(payload, issue_url)
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            result = {
                "mode": mode,
                "run_id": run_id,
                "status": "error",
                "summary": str(exc),
                "task_id": task_id,
            }
            print(json.dumps(result, sort_keys=True))
            return 1

    state = {
        "body_preview": render_issue_body(payload),
        "created_at": now_iso(),
        "issue_url": issue_url,
        "mode": mode,
        "project_number": payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER", ""),
        "project_owner": payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER", ""),
        "project_result": project_result,
        "project_title": payload.get("project_title") or "",
        "repository": payload["repository"],
        "run_id": run_id,
        "session_key": payload.get("session_key") or f"sdlc:github-project:{slug(task_id)}",
        "status": "created" if apply else "planned",
        "task_id": task_id,
        "title": payload["title"],
    }
    atomic_write_json(task_state_path(task_id), state)
    record_event(
        "github-project-task",
        {
            "event_type": "github.project.task.created" if apply else "github.project.task.planned",
            "issue_url": issue_url,
            "mode": mode,
            "repository": payload["repository"],
            "run_id": run_id,
            "task_id": task_id,
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "issue_url": issue_url,
                "mode": mode,
                "run_id": run_id,
                "state_path": str(task_state_path(task_id)),
                "status": "ok",
                "summary": "created github issue and project item" if apply else "prepared github project task dry-run",
                "task_id": task_id,
            },
            sort_keys=True,
        )
    )
    return 0


def close_canary(payload_path: str | None, apply: bool = False) -> int:
    payload = load_payload(payload_path)
    issue_number = payload.get("issue_number") or payload.get("number")
    repository = payload.get("repository") or payload.get("repo")
    if not issue_number or not repository:
        print(json.dumps({"missing_fields": ["repository", "issue_number"], "status": "error"}, sort_keys=True))
        return 2
    run_id = os.environ.get("RUN_ID", f"canary-cleanup-{issue_number}")
    mode = "apply" if apply else "dry-run"
    close_status = "planned"
    issue_url = payload.get("issue_url") or f"https://github.com/{repository}/issues/{issue_number}"
    error_summary = ""
    if apply:
        try:
            run_gh(
                [
                    "issue",
                    "close",
                    str(issue_number),
                    "--repo",
                    str(repository),
                    "--comment",
                    "OpenClaw canary cleanup: тестовая задача закрыта после проверки GitHub Project flow.",
                    "--reason",
                    "completed",
                ]
            )
            close_status = "closed"
        except RuntimeError as exc:
            error_summary = str(exc)
            close_status = "failed"

    state = {
        "closed_at": now_iso() if close_status == "closed" else "",
        "issue_number": int(issue_number),
        "issue_url": issue_url,
        "mode": mode,
        "project_number": payload.get("project_number") or os.environ.get("GITHUB_PROJECT_NUMBER", ""),
        "project_owner": payload.get("project_owner") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER", ""),
        "repository": repository,
        "run_id": run_id,
        "status": close_status,
        "summary": error_summary or ("closed canary issue" if apply else "prepared canary issue cleanup"),
        "updated_at": now_iso(),
    }
    atomic_write_json(canary_cleanup_path(issue_number), state)
    record_event(
        "github-project-canary-cleanup",
        {
            "event_type": "github.project.canary.closed" if close_status == "closed" else "github.project.canary.cleanup_planned",
            "issue_number": int(issue_number),
            "mode": mode,
            "repository": repository,
            "run_id": run_id,
            "status": close_status,
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "issue_number": int(issue_number),
                "mode": mode,
                "run_id": run_id,
                "state_path": str(canary_cleanup_path(issue_number)),
                "status": "ok" if close_status in {"planned", "closed"} else "error",
                "summary": state["summary"],
            },
            sort_keys=True,
        )
    )
    return 0 if close_status in {"planned", "closed"} else 1


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: github_project_ops.py <create-task|set-status|sync-status|close-canary> [--apply] <payload.json>", file=sys.stderr)
        return 1
    command = sys.argv[1]
    if command not in {"create-task", "set-status", "sync-status", "close-canary"}:
        print(f"unknown command: {command}", file=sys.stderr)
        return 1
    apply = False
    payload_path = None
    for arg in sys.argv[2:]:
        if arg == "--apply":
            apply = True
        else:
            payload_path = arg
    apply = apply or bool_env("CONTROL_APPLY")
    if command == "create-task":
        return create_task(payload_path, apply=apply)
    if command == "close-canary":
        return close_canary(payload_path, apply=apply)
    return set_status(payload_path, apply=apply)


if __name__ == "__main__":
    raise SystemExit(main())
