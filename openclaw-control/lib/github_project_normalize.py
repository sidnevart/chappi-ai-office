#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "unknown-project"


def load_payload(source: str) -> dict:
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(source)


def normalize_github_project_payload(payload: dict) -> dict:
    item = payload.get("projects_v2_item", {})
    project = payload.get("projects_v2", {})
    org = payload.get("organization", {})
    content = payload.get("content", {})

    project_title = project.get("title") or os.environ.get("GITHUB_PROJECT_NAME") or "github-project"
    item_id = str(item.get("node_id") or item.get("id") or payload.get("id") or "unknown-item")
    normalized = {
        "item_id": item_id,
        "project_number": project.get("number") or os.environ.get("GITHUB_PROJECT_NUMBER") or "",
        "project_owner": org.get("login") or os.environ.get("GITHUB_PROJECT_OWNER") or os.environ.get("GITHUB_OWNER") or "",
        "project_key": slug(f"{org.get('login', 'org')}-{project_title}"),
        "status": payload.get("action", "changed"),
        "title": content.get("title") or payload.get("title") or item.get("title") or "",
    }
    if isinstance(content, dict):
        issue_url = content.get("html_url") or content.get("url") or ""
        if issue_url:
            normalized["issue_url"] = issue_url

    repo_name = ""
    repository = payload.get("repository", {})
    if repository:
        repo_name = repository.get("full_name") or repository.get("name") or ""
    if not repo_name and isinstance(content, dict):
        repo = content.get("repository")
        if isinstance(repo, dict):
            repo_name = repo.get("full_name") or repo.get("name") or ""
    if repo_name:
        normalized["repository"] = repo_name
    if project.get("node_id"):
        normalized["job_id"] = f"{normalized['project_key']}-{item_id}"
    normalized["session_key"] = f"sdlc:{normalized['project_key']}:{item_id}"
    return normalized


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: github_project_normalize.py <payload.json>", file=sys.stderr)
        return 1
    payload = load_payload(sys.argv[1])
    normalized = normalize_github_project_payload(payload)
    print(json.dumps(normalized, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
