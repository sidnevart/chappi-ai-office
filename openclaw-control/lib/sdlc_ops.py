#!/usr/bin/env python3
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from control_plane import (
    atomic_write_json,
    handle_github_project_sync,
    handle_spec_review_publish,
    load_payload,
    now_iso,
    record_event,
    slug,
    state_dir,
)
from github_project_normalize import normalize_github_project_payload

ROOT = Path(__file__).resolve().parents[1]


def push_state_to_ui(agent_id: str, state: str, detail: str, job: dict | None = None) -> None:
    """Push agent state to Star Office UI via REST. Never fail the main flow."""
    try:
        import urllib.request
        payload = json.dumps({
            "agent_id": agent_id,
            "state": state,
            "detail": detail[:200],
            "task_id": job.get("job_id") if job else None,
            "session_key": job.get("session_key") if job else None,
        }).encode()
        req = urllib.request.Request(
            os.environ.get("STAR_OFFICE_URL", "http://localhost:3000/set_state"),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


def job_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "jobs" / "sdlc" / slug(project_key) / f"{slug(item_id)}.json"


def spec_dir(project_key: str) -> Path:
    return state_dir() / "specs" / slug(project_key)


def spec_markdown_path(project_key: str, item_id: str) -> Path:
    return spec_dir(project_key) / f"{slug(item_id)}.md"


def spec_meta_path(project_key: str, item_id: str) -> Path:
    return spec_dir(project_key) / f"{slug(item_id)}.json"


def branch_meta_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "branches" / slug(project_key) / f"{slug(item_id)}.json"


def pr_meta_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "prs" / slug(project_key) / f"{slug(item_id)}.json"


def ci_meta_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "ci" / slug(project_key) / f"{slug(item_id)}.json"


def coder_run_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "coder-runs" / slug(project_key) / f"{slug(item_id)}.json"


def coder_prompt_path(project_key: str, item_id: str) -> Path:
    return state_dir() / "coder-runs" / slug(project_key) / f"{slug(item_id)}.prompt.md"


def load_job(project_key: str, item_id: str) -> dict:
    path = job_path(project_key, item_id)
    if not path.exists():
        raise FileNotFoundError(f"job not found: {project_key}/{item_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


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
            "sdlc-github-project-status",
            {
                "apply": apply,
                "event_type": "sdlc.github_project.status_sync",
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


def summarize_spec(job: dict) -> str:
    title = job.get("title") or "Untitled work item"
    repository = job.get("repository") or "repository-missing"
    return f"Implement '{title}' in {repository} with validation, rollout notes, and approval before branch creation."


def render_spec_markdown(job: dict) -> str:
    title = job.get("title") or "Untitled work item"
    repository = job.get("repository") or "repository-missing"
    item_id = job.get("item_id") or "item-missing"
    status = job.get("status") or "unknown"
    missing = ", ".join(job.get("missing_fields") or []) or "none"
    summary = summarize_spec(job)
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Intake",
            f"- Item ID: `{item_id}`",
            f"- Repository: `{repository}`",
            f"- Project status: `{status}`",
            f"- Missing fields at sync: `{missing}`",
            "",
            "## Summary",
            summary,
            "",
            "## Scope",
            f"- Implement the requested change for `{title}`.",
            "- Keep the change bounded to the relevant repository surface.",
            "- Preserve approval and rollout visibility.",
            "",
            "## Acceptance Criteria",
            "- The durable SDLC job state is updated for the task lifecycle.",
            "- The implementation plan is specific enough to hand off to a coder-runner.",
            "- Validation and rollback notes are present before branch creation.",
            "",
            "## Validation",
            "- Run the repo smoke tests relevant to the target repository.",
            "- Verify no policy or approval path is bypassed.",
            "",
            "## Rollout",
            "- Use dry-run first.",
            "- Capture the rollback command or previous artifact before apply.",
            "",
            "## Open Questions",
            "- Confirm exact acceptance criteria with the human reviewer if they are still implicit.",
            "- Confirm production rollout timing if the task affects live services.",
        ]
    )


def build_doc_url(project_key: str, item_id: str, spec_path: Path) -> str:
    base = os.environ.get("CONTROL_DOCS_BASE_URL", "").rstrip("/")
    if base:
        return f"{base}/{slug(project_key)}/{slug(item_id)}"
    return str(spec_path)


def spec_artifact_path(project_key: str, item_id: str) -> Path:
    return spec_dir(project_key) / f"{slug(item_id)}.artifact.json"


def artifact_doc_url(project_key: str, item_id: str) -> str:
    base = os.environ.get("CONTROL_DOCS_BASE_URL", "").rstrip("/")
    if not base:
        return ""
    return f"{base}/{slug(project_key)}/{slug(item_id)}.md"


def publish_spec_artifact(project_key: str, item_id: str) -> int:
    spec_path = spec_markdown_path(project_key, item_id)
    meta_path = spec_meta_path(project_key, item_id)
    if not spec_path.exists() or not meta_path.exists():
        print(json.dumps({"status": "error", "summary": f"spec artifact source missing for {project_key}/{item_id}"}, sort_keys=True))
        return 1

    artifact_root = Path(os.environ.get("CONTROL_DOCS_ARTIFACT_DIR", str(state_dir() / "docs" / "specs"))).resolve()
    artifact_path = artifact_root / slug(project_key) / f"{slug(item_id)}.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    content = spec_path.read_bytes()
    artifact_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    doc_url = artifact_doc_url(project_key, item_id) or str(artifact_path)
    published_at = now_iso()

    spec_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    spec_meta["artifact_path"] = str(artifact_path)
    spec_meta["checksum_sha256"] = checksum
    spec_meta["doc_url"] = doc_url
    spec_meta["published_at"] = published_at
    spec_meta["updated_at"] = published_at
    atomic_write_json(meta_path, spec_meta)

    job = load_job(project_key, item_id)
    job["doc_url"] = doc_url
    job["spec_artifact_path"] = str(artifact_path)
    job["spec_checksum_sha256"] = checksum
    job["updated_at"] = published_at
    atomic_write_json(job_path(project_key, item_id), job)

    artifact_meta = {
        "artifact_path": str(artifact_path),
        "checksum_sha256": checksum,
        "doc_url": doc_url,
        "item_id": item_id,
        "project_key": project_key,
        "published_at": published_at,
        "run_id": os.environ.get("RUN_ID", f"spec-artifact-{slug(item_id)}"),
        "spec_path": str(spec_path),
        "status": "published",
    }
    atomic_write_json(spec_artifact_path(project_key, item_id), artifact_meta)
    record_event(
        "sdlc-spec-artifact",
        {
            "checksum_sha256": checksum,
            "doc_url": doc_url,
            "event_type": "sdlc.spec.artifact_published",
            "item_id": item_id,
            "project_key": project_key,
            "timestamp": published_at,
        },
    )
    print(json.dumps({"artifact_path": str(artifact_path), "doc_url": doc_url, "status": "ok"}, sort_keys=True))
    return 0


def repo_allowed(repository: str) -> bool:
    allowlist = [item.strip() for item in os.environ.get("CONTROL_CODER_REPO_ALLOWLIST", "").split(",") if item.strip()]
    return not allowlist or repository in allowlist


def runner_execution_mode() -> str:
    mode = os.environ.get("CONTROL_CODER_EXECUTION_MODE", "patch").strip().lower()
    return mode if mode in {"patch", "tools"} else "patch"


def render_coder_prompt(job: dict, spec_meta: dict, branch_meta: dict) -> str:
    spec_body = ""
    spec_path = spec_meta.get("spec_path") or job.get("spec_path") or ""
    if spec_path and Path(str(spec_path)).exists():
        spec_body = Path(str(spec_path)).read_text(encoding="utf-8").strip()
    execution_rules = [
        "- Read the embedded spec before editing.",
        "- Keep the change scoped to the task.",
        "- Run relevant tests.",
        "- Do not push, create PRs, or mutate external services unless a separate approval gate authorizes it.",
        "- Return a concise implementation summary, validation evidence, and remaining risks.",
    ]
    if runner_execution_mode() == "patch":
        execution_rules.extend(
            [
                "- Inspect the repository with read-only tools if needed.",
                "- Return only a unified diff for the required changes.",
                "- Do not wrap the diff in Markdown fences.",
                "- If no change is needed, return exactly NO_CHANGES.",
            ]
        )
    return "\n".join(
        [
            "# OpenClaw Coder Runner Task",
            "",
            f"Repository: {job.get('repository') or 'repository-missing'}",
            f"Branch: {branch_meta.get('branch_name') or job.get('branch_name') or 'branch-missing'}",
            f"Task: {job.get('title') or 'Untitled task'}",
            f"Project item: {job.get('project_key')}/{job.get('item_id')}",
            f"Spec: {spec_meta.get('doc_url') or spec_meta.get('spec_path') or job.get('spec_path') or 'spec-missing'}",
            "",
            "Rules:",
            *execution_rules,
            "",
            "## Embedded Spec",
            spec_body or "Spec body missing.",
        ]
    )


def run_checked(
    args: list[str],
    cwd: Path | None = None,
    input_text: str | None = None,
    env_overrides: dict[str, str | None] | None = None,
    truncate_output: bool = True,
) -> dict:
    env = os.environ.copy()
    if env_overrides:
        for key, value in env_overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "args": args,
        "exit_code": completed.returncode,
        "stderr": completed.stderr[-4000:] if truncate_output else completed.stderr,
        "stdout": completed.stdout[-4000:] if truncate_output else completed.stdout,
    }


def default_base_branch(repository: str) -> str:
    return os.environ.get("CONTROL_CODER_BASE_BRANCH") or "main"


def default_commit_message(job: dict) -> str:
    title = str(job.get("title") or job.get("item_id") or "openclaw update").strip()
    return os.environ.get("CONTROL_CODER_COMMIT_MESSAGE", f"chore: {title}")


def repo_clone_url(repository: str) -> str:
    protocol = os.environ.get("CONTROL_CODER_GIT_PROTOCOL", "ssh").strip().lower()
    if protocol == "https":
        return f"https://github.com/{repository}.git"
    return f"git@github.com:{repository}.git"


def runner_cli() -> str:
    return os.environ.get("CONTROL_CODER_CLI", "claude").strip() or "claude"


def runner_model() -> str:
    return os.environ.get("CONTROL_CLAUDE_MODEL", "").strip()


def runner_env() -> dict[str, str | None]:
    env: dict[str, str | None] = {
        "ANTHROPIC_AUTH_TOKEN": None,
        "ANTHROPIC_API_KEY": None,
        "ANTHROPIC_BASE_URL": None,
    }
    base_url = os.environ.get("CONTROL_CLAUDE_BASE_URL", "").strip()
    api_key = os.environ.get("CONTROL_CLAUDE_API_KEY", "").strip()
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    return env


def model_requires_bridge(model: str) -> bool:
    normalized = model.strip().lower()
    if not normalized:
        return False
    return not (
        normalized.startswith("claude")
        or normalized.startswith("anthropic/claude")
    )


def runner_backend_mode() -> str:
    return "bridge" if model_requires_bridge(runner_model()) else "native"


def runner_preflight() -> tuple[bool, str]:
    cli = runner_cli()
    if not shutil.which(cli):
        return False, f"{cli} is not installed or not present in PATH"

    if cli != "claude":
        return True, ""

    model = runner_model()
    base_url = os.environ.get("CONTROL_CLAUDE_BASE_URL", "").strip()
    api_key = os.environ.get("CONTROL_CLAUDE_API_KEY", "").strip()
    if model_requires_bridge(model):
        if not base_url:
            return False, f"model {model} requires CONTROL_CLAUDE_BASE_URL for an Anthropic-compatible bridge"
        if not api_key:
            return False, f"model {model} requires CONTROL_CLAUDE_API_KEY for an Anthropic-compatible bridge"
    if base_url and not re.match(r"^https?://", base_url):
        return False, "CONTROL_CLAUDE_BASE_URL must start with http:// or https://"
    return True, ""


def build_runner_args(worktree: Path, prompt: str) -> list[str]:
    cli = runner_cli()
    if cli == "claude":
        args = [
            "claude",
            "--print",
            "--output-format",
            "json",
            "--setting-sources",
            "user",
            "--add-dir",
            str(worktree),
        ]
        if runner_execution_mode() == "patch":
            args.extend(
                [
                    "--permission-mode",
                    "dontAsk",
                    "--allowedTools=Read,Grep,Glob,LS",
                ]
            )
        else:
            args.extend(
                [
                    "--permission-mode",
                    "acceptEdits",
                ]
            )
        model = runner_model()
        if model:
            args.extend(["--model", model])
        if bool_env("CONTROL_CLAUDE_BYPASS_PERMISSIONS"):
            args.insert(2, "--dangerously-skip-permissions")
        args.append(prompt)
        return args
    return [cli, prompt]


def runner_result_text(stdout: str) -> str:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout.strip()
    if isinstance(payload, dict):
        result = payload.get("result")
        if isinstance(result, str):
            return result.strip()
    return stdout.strip()


def runner_payload(stdout: str) -> dict | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def extract_patch_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped == "NO_CHANGES":
        return "NO_CHANGES"
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:diff)?\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    for marker in ("diff --git ", "--- "):
        index = stripped.find(marker)
        if index >= 0:
            return stripped[index:].strip()
    return stripped


def apply_denied_edits(worktree: Path, payload: dict | None) -> tuple[bool, str]:
    if not payload:
        return False, ""
    denials = payload.get("permission_denials")
    if not isinstance(denials, list):
        return False, ""
    applied = 0
    for denial in denials:
        if not isinstance(denial, dict) or denial.get("tool_name") != "Edit":
            continue
        tool_input = denial.get("tool_input")
        if not isinstance(tool_input, dict):
            continue
        file_path = Path(str(tool_input.get("file_path") or "")).resolve()
        try:
            file_path.relative_to(worktree.resolve())
        except ValueError:
            return False, f"edit target escapes worktree: {file_path}"
        if not file_path.exists():
            return False, f"edit target missing: {file_path}"
        old_string = str(tool_input.get("old_string") or "")
        new_string = str(tool_input.get("new_string") or "")
        replace_all = bool(tool_input.get("replace_all"))
        current = file_path.read_text(encoding="utf-8")
        if old_string not in current:
            return False, f"edit old_string not found in {file_path}"
        updated = current.replace(old_string, new_string) if replace_all else current.replace(old_string, new_string, 1)
        file_path.write_text(updated, encoding="utf-8")
        applied += 1
    if applied:
        return True, f"applied {applied} denied Edit intents"
    return False, ""


def execute_coder_run(job: dict, state: dict, runner_args: list[str], prompt: str, worktree: Path) -> dict:
    repository = str(job["repository"])
    branch = str(state["branch_name"])
    base = str(job.get("base_branch") or default_base_branch(repository))
    steps = []
    worktree.parent.mkdir(parents=True, exist_ok=True)

    if not (worktree / ".git").exists():
        clone_url = repo_clone_url(repository)
        steps.append(run_checked(["git", "clone", clone_url, str(worktree)]))
        if steps[-1]["exit_code"] != 0:
            state["status"] = "failed"
            state["steps"] = steps
            return state

    for args in (
        ["git", "fetch", "origin"],
        ["git", "checkout", "-B", branch, f"origin/{base}"],
    ):
        steps.append(run_checked(args, cwd=worktree))
        if steps[-1]["exit_code"] != 0:
            state["status"] = "failed"
            state["steps"] = steps
            return state

    steps.append(run_checked(runner_args, cwd=worktree, env_overrides=runner_env(), truncate_output=False))
    state["runner_exit_code"] = steps[-1]["exit_code"]
    if steps[-1]["exit_code"] != 0:
        state["status"] = "failed"
        state["steps"] = steps
        return state

    raw_runner_output = steps[-1]["stdout"]
    Path(str(state["output_path"])).write_text(raw_runner_output, encoding="utf-8")

    if runner_execution_mode() == "patch":
        payload = runner_payload(raw_runner_output)
        applied_edits, applied_summary = apply_denied_edits(worktree, payload)
        patch_text = extract_patch_text(runner_result_text(raw_runner_output))
        state["runner_result_excerpt"] = applied_summary if applied_edits else patch_text[:4000]
        if applied_edits:
            patch_text = ""
        if patch_text == "NO_CHANGES" or (not patch_text.strip() and not applied_edits):
            state["status"] = "no_changes"
            state["steps"] = steps
            return state
        if patch_text.strip():
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
                handle.write(patch_text)
                patch_path = Path(handle.name)
            try:
                steps.append(run_checked(["git", "apply", "--whitespace=nowarn", str(patch_path)], cwd=worktree))
            finally:
                patch_path.unlink(missing_ok=True)
            if steps[-1]["exit_code"] != 0:
                state["status"] = "patch_failed"
                state["steps"] = steps
                return state

    validation_command = os.environ.get("CONTROL_CODER_TEST_COMMAND", "").strip()
    if validation_command:
        steps.append(run_checked(["bash", "-lc", validation_command], cwd=worktree))
        state["validation_exit_code"] = steps[-1]["exit_code"]
        if steps[-1]["exit_code"] != 0:
            state["status"] = "validation_failed"
            state["steps"] = steps
            return state

    steps.append(run_checked(["git", "status", "--short"], cwd=worktree))
    state["git_status"] = steps[-1]["stdout"]
    steps.append(run_checked(["git", "diff", "--stat"], cwd=worktree))
    state["git_diff_stat"] = steps[-1]["stdout"]
    if not state["git_status"].strip():
        state["status"] = "no_changes"
        state["steps"] = steps
        return state

    for args in (
        ["git", "add", "-A"],
        ["git", "commit", "-m", default_commit_message(job)],
    ):
        steps.append(run_checked(args, cwd=worktree))
        if steps[-1]["exit_code"] != 0:
            state["status"] = "commit_failed"
            state["steps"] = steps
            return state
    steps.append(run_checked(["git", "rev-parse", "HEAD"], cwd=worktree))
    state["commit_sha"] = steps[-1]["stdout"].strip()

    if bool_env("CONTROL_CODER_PUSH_APPROVED"):
        steps.append(run_checked(["git", "push", "-u", "origin", branch], cwd=worktree))
        state["push_exit_code"] = steps[-1]["exit_code"]
        if steps[-1]["exit_code"] != 0:
            state["status"] = "push_failed"
            state["steps"] = steps
            return state
        state["pushed"] = True
    else:
        state["pushed"] = False

    if bool_env("CONTROL_CODER_PR_APPROVED"):
        body = "\n".join(
            [
                f"OpenClaw task: {job.get('title') or job.get('item_id')}",
                "",
                f"Spec: {job.get('doc_url') or job.get('spec_path') or 'not recorded'}",
                f"Run: {state.get('run_id')}",
            ]
        )
        steps.append(run_checked(["gh", "pr", "create", "--repo", repository, "--head", branch, "--title", job.get("title") or branch, "--body", body]))
        state["pr_create_exit_code"] = steps[-1]["exit_code"]
        if steps[-1]["exit_code"] != 0:
            state["status"] = "pr_failed"
            state["steps"] = steps
            return state
        state["pr_url"] = steps[-1]["stdout"].strip()
    else:
        state["pr_url"] = ""

    state["status"] = "ready_for_pr" if not state.get("pr_url") else "pr_created"
    state["steps"] = steps
    return state


def run_coder(project_key: str, item_id: str, apply: bool = False) -> int:
    job = load_job(project_key, item_id)
    repository = job.get("repository") or ""
    if not repository:
        print(json.dumps({"status": "error", "summary": "repository is required for coder runner"}, sort_keys=True))
        return 2
    if not repo_allowed(repository):
        print(json.dumps({"repository": repository, "status": "error", "summary": "repository is not in CONTROL_CODER_REPO_ALLOWLIST"}, sort_keys=True))
        return 2
    if job.get("state") not in {"branch_bootstrapped", "coder_dry_run_ready", "implementing"}:
        print(json.dumps({"state": job.get("state"), "status": "error", "summary": "job must be branch_bootstrapped before coder runner"}, sort_keys=True))
        return 1

    spec_file = spec_meta_path(project_key, item_id)
    branch_file = branch_meta_path(project_key, item_id)
    if not spec_file.exists() or not branch_file.exists():
        print(json.dumps({"status": "error", "summary": "spec and branch metadata are required"}, sort_keys=True))
        return 1

    spec_meta = json.loads(spec_file.read_text(encoding="utf-8"))
    branch_meta = json.loads(branch_file.read_text(encoding="utf-8"))
    run_id = os.environ.get("RUN_ID", f"coder-{slug(item_id)}")
    mode = "apply" if apply else "dry-run"
    worktree = Path(os.environ.get("CONTROL_CODER_WORKTREE_ROOT", str(state_dir() / "coder-worktrees"))) / slug(project_key) / slug(item_id) / "repo"
    output_path = state_dir() / "coder-runs" / slug(project_key) / f"{slug(item_id)}.last-message.md"
    prompt_path = coder_prompt_path(project_key, item_id)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = render_coder_prompt(job, spec_meta, branch_meta)
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    preflight_ok, preflight_error = runner_preflight()
    runner_args = build_runner_args(worktree, prompt)
    state = {
        "backend_mode": runner_backend_mode(),
        "branch_name": branch_meta.get("branch_name") or job.get("branch_name"),
        "executor": runner_cli(),
        "executor_command": " ".join(shlex.quote(part) for part in runner_args),
        "created_at": now_iso(),
        "execution_mode": runner_execution_mode(),
        "item_id": item_id,
        "mode": mode,
        "model": runner_model() or "(claude default)",
        "git_protocol": os.environ.get("CONTROL_CODER_GIT_PROTOCOL", "ssh").strip().lower() or "ssh",
        "output_path": str(output_path),
        "preflight_error": preflight_error,
        "preflight_ok": preflight_ok,
        "project_key": project_key,
        "prompt_path": str(prompt_path),
        "repository": repository,
        "run_id": run_id,
        "status": "planned" if not apply else "prepared",
        "summary": "claude runner dry-run prepared" if not apply else "claude runner apply prepared; execution gated by CONTROL_CODER_EXECUTE",
        "worktree_path": str(worktree),
    }
    if not preflight_ok:
        state["status"] = "invalid_config"
        state["summary"] = preflight_error
    elif apply and bool_env("CONTROL_CODER_EXECUTE"):
        job["owner"] = "coder-runner"
        state = execute_coder_run(job, state, runner_args, prompt, worktree)
    elif apply:
        state["blocked_reason"] = "set CONTROL_CODER_EXECUTE=1 to run Claude CLI; for Kimi/GLM set CONTROL_CLAUDE_MODEL plus CONTROL_CLAUDE_BASE_URL/CONTROL_CLAUDE_API_KEY; push and PR stay behind CONTROL_CODER_PUSH_APPROVED=1 and CONTROL_CODER_PR_APPROVED=1"
    atomic_write_json(coder_run_path(project_key, item_id), state)

    push_state_to_ui(job.get("owner", "coder-runner"), "executing" if apply and preflight_ok else "idle", f"coder runner {mode}", job)
    job["coder_run_id"] = run_id
    job["coder_run_path"] = str(coder_run_path(project_key, item_id))
    if not apply:
        job["state"] = "coder_dry_run_ready" if preflight_ok else "coder_failed"
    elif state.get("status") == "pr_created":
        job["state"] = "pr_open"
        job["owner"] = "review-watcher"
        job["pr_url"] = state.get("pr_url", "")
        pr_url = str(state.get("pr_url") or "")
        pr_number_match = re.search(r"/pull/(\d+)", pr_url)
        pr_meta = {
            "created_at": now_iso(),
            "head_sha": "",
            "item_id": item_id,
            "pr_number": int(pr_number_match.group(1)) if pr_number_match else 0,
            "pr_url": pr_url,
            "project_key": project_key,
            "run_id": run_id,
            "session_key": job.get("session_key") or f"sdlc:{project_key}:{item_id}",
            "status": "open",
            "title": job.get("title") or f"PR for {item_id}",
        }
        atomic_write_json(pr_meta_path(project_key, item_id), pr_meta)
    elif state.get("status") in {"ready_for_pr", "prepared"}:
        job["state"] = "implementing"
    else:
        job["state"] = "coder_failed"
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(project_key, item_id), job)
    maybe_sync_project_status(job, job["state"])
    record_event(
        "sdlc-coder-run",
        {
            "event_type": "sdlc.coder.prepared" if preflight_ok and not apply else "sdlc.coder.blocked",
            "executor": runner_cli(),
            "item_id": item_id,
            "mode": mode,
            "project_key": project_key,
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"mode": mode, "run_id": run_id, "state_path": str(coder_run_path(project_key, item_id)), "status": "ok"}, sort_keys=True))
    return 0 if preflight_ok else 1


def normalize_webhook(payload_path: str) -> int:
    payload = load_payload(payload_path)
    print(json.dumps(normalize_github_project_payload(payload), sort_keys=True))
    return 0


def sync(payload_path: str) -> int:
    payload = load_payload(payload_path)
    print(json.dumps(handle_github_project_sync(payload), sort_keys=True))
    return 0


def from_webhook(payload_path: str) -> int:
    payload = load_payload(payload_path)
    normalized = normalize_github_project_payload(payload)
    print(json.dumps(handle_github_project_sync(normalized), sort_keys=True))
    return 0


def prepare_spec(project_key: str, item_id: str) -> int:
    job = load_job(project_key, item_id)
    if job.get("missing_fields"):
        print(
            json.dumps(
                {
                    "status": "error",
                    "summary": f"job {project_key}/{item_id} still requires intake",
                    "missing_fields": job.get("missing_fields", []),
                },
                sort_keys=True,
            )
        )
        return 1

    spec_path = spec_markdown_path(project_key, item_id)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(render_spec_markdown(job) + "\n", encoding="utf-8")

    run_id = os.environ.get("RUN_ID", f"spec-{slug(item_id)}")
    spec_id = f"spec-{slug(item_id)}"
    doc_url = build_doc_url(project_key, item_id, spec_path)
    summary = summarize_spec(job)
    spec_meta = {
        "doc_url": doc_url,
        "item_id": item_id,
        "job_id": job.get("job_id"),
        "project_key": project_key,
        "run_id": run_id,
        "session_key": job.get("session_key") or f"sdlc:{project_key}:{item_id}",
        "spec_id": spec_id,
        "spec_path": str(spec_path),
        "state": "spec_ready",
        "summary": summary,
        "title": job.get("title") or "Untitled work item",
        "updated_at": now_iso(),
    }
    atomic_write_json(spec_meta_path(project_key, item_id), spec_meta)

    job["doc_url"] = doc_url
    job["spec_id"] = spec_id
    job["spec_path"] = str(spec_path)
    job["state"] = "spec_ready"
    job["summary"] = summary
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(project_key, item_id), job)
    push_state_to_ui(job.get("owner", "sdlc-orchestrator"), "writing", f"prepared spec {spec_id}", job)
    maybe_sync_project_status(job, "spec_ready")
    record_event(
        "sdlc-spec-prepare",
        {
            "event_type": "sdlc.spec.prepared",
            "item_id": item_id,
            "project_key": project_key,
            "run_id": run_id,
            "spec_id": spec_id,
            "timestamp": now_iso(),
        },
    )
    print(
        json.dumps(
            {
                "doc_url": doc_url,
                "run_id": run_id,
                "spec_id": spec_id,
                "spec_path": str(spec_path),
                "status": "ok",
                "summary": f"prepared spec for {project_key}/{item_id}",
            },
            sort_keys=True,
        )
    )
    return 0


def publish_spec(project_key: str, item_id: str) -> int:
    spec_meta_file = spec_meta_path(project_key, item_id)
    if not spec_meta_file.exists():
        print(json.dumps({"status": "error", "summary": f"spec not prepared for {project_key}/{item_id}"}, sort_keys=True))
        return 1
    spec_meta = json.loads(spec_meta_file.read_text(encoding="utf-8"))
    approval_id = f"spec-{slug(item_id)}"
    publish_payload = dict(spec_meta)
    publish_payload["approval_id"] = approval_id
    publish_payload["session_key"] = f"approval:{approval_id}"
    result = handle_spec_review_publish(publish_payload)

    job = load_job(project_key, item_id)
    job["approval_id"] = approval_id
    job["approval_status"] = "pending"
    job["state"] = "awaiting_spec_approval"
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(project_key, item_id), job)
    push_state_to_ui(job.get("owner", "sdlc-orchestrator"), "idle", f"awaiting approval {approval_id}", job)
    maybe_sync_project_status(job, "awaiting_spec_approval")
    record_event(
        "sdlc-spec-publish",
        {
            "approval_id": result["approval_id"],
            "event_type": "sdlc.spec.ready",
            "item_id": item_id,
            "project_key": project_key,
            "run_id": result["run_id"],
            "timestamp": now_iso(),
        },
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def publish_request(payload_path: str) -> int:
    payload = load_payload(payload_path)
    print(json.dumps(handle_spec_review_publish(payload), sort_keys=True))
    return 0


def default_branch_name(job: dict) -> str:
    return f"sdlc/{slug(job.get('item_id', 'item'))}-{slug(job.get('title', 'task'))[:48]}"


def bootstrap_branch(project_key: str, item_id: str, branch_name: str | None = None) -> int:
    job = load_job(project_key, item_id)
    if job.get("approval_status") != "approved" and job.get("state") != "spec_approved":
        print(
            json.dumps(
                {
                    "status": "error",
                    "summary": f"job {project_key}/{item_id} is not approved for branch creation",
                },
                sort_keys=True,
            )
        )
        return 1
    branch = branch_name or default_branch_name(job)
    meta = {
        "branch_name": branch,
        "created_at": now_iso(),
        "item_id": item_id,
        "project_key": project_key,
        "run_id": os.environ.get("RUN_ID", f"branch-{slug(item_id)}"),
        "session_key": job.get("session_key") or f"sdlc:{project_key}:{item_id}",
        "status": "bootstrapped",
    }
    atomic_write_json(branch_meta_path(project_key, item_id), meta)
    job["branch_name"] = branch
    job["state"] = "branch_bootstrapped"
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(project_key, item_id), job)
    push_state_to_ui(job.get("owner", "sdlc-orchestrator"), "idle", f"handoff to coder-runner: {branch}", job)
    maybe_sync_project_status(job, "branch_bootstrapped")
    record_event(
        "sdlc-branch-bootstrap",
        {
            "branch_name": branch,
            "event_type": "sdlc.branch.bootstrapped",
            "item_id": item_id,
            "project_key": project_key,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"branch_name": branch, "status": "ok", "summary": f"bootstrapped branch for {project_key}/{item_id}"}, sort_keys=True))
    return 0


def record_pr(project_key: str, item_id: str, payload_path: str) -> int:
    job = load_job(project_key, item_id)
    payload = load_payload(payload_path)
    pr_number = payload.get("pr_number") or payload.get("number")
    pr_url = payload.get("pr_url") or payload.get("url")
    if not pr_number or not pr_url:
        print(json.dumps({"status": "error", "summary": "pr_number and pr_url are required"}, sort_keys=True))
        return 1
    meta = {
        "created_at": now_iso(),
        "head_sha": payload.get("head_sha") or payload.get("sha") or "",
        "item_id": item_id,
        "pr_number": int(pr_number),
        "pr_url": pr_url,
        "project_key": project_key,
        "run_id": os.environ.get("RUN_ID", f"pr-{slug(item_id)}"),
        "session_key": job.get("session_key") or f"sdlc:{project_key}:{item_id}",
        "status": payload.get("status") or "open",
        "title": payload.get("title") or job.get("title") or f"PR for {item_id}",
    }
    atomic_write_json(pr_meta_path(project_key, item_id), meta)
    job["pr_number"] = meta["pr_number"]
    job["pr_url"] = meta["pr_url"]
    job["state"] = "pr_open"
    job["updated_at"] = now_iso()
    atomic_write_json(job_path(project_key, item_id), job)
    push_state_to_ui(job.get("owner", "review-watcher"), "syncing", f"watching PR #{meta['pr_number']}", job)
    maybe_sync_project_status(job, "pr_open")
    record_event(
        "sdlc-pr-record",
        {
            "event_type": "sdlc.pr.ready",
            "item_id": item_id,
            "pr_number": meta["pr_number"],
            "project_key": project_key,
            "timestamp": now_iso(),
        },
    )
    print(json.dumps({"pr_number": meta["pr_number"], "pr_url": meta["pr_url"], "status": "ok"}, sort_keys=True))
    return 0


def prepare_pr_digest(job: dict, pr_meta: dict, ci_meta: dict) -> dict:
    run_id = os.environ.get("RUN_ID", f"pr-digest-{slug(job.get('item_id', 'item'))}")
    approval_id = f"pr-{slug(job.get('item_id', 'item'))}"
    title = pr_meta.get("title") or job.get("title") or "PR готов"
    pr_url = pr_meta.get("pr_url") or "pr-url-missing"
    ci_status = ci_meta.get("status", "unknown")
    ci_summary = ci_meta.get("summary") or "CI завершился"
    message = "\n".join(
        [
            "🔀 OpenClaw: PR готов к ревью",
            "",
            "🟢 Статус: CI прошел, нужен human review",
            f"🧩 Задача: {title}",
            f"📁 Проект: {job.get('project_key') or 'project-missing'}",
            f"🔖 Item: {job.get('item_id') or 'item-missing'}",
            f"🔗 PR: {pr_url}",
            f"✅ CI: {ci_status}",
            f"☑️ Approval: `{approval_id}`",
            f"🧵 Run: `{run_id}`",
            "",
            "📝 Кратко:",
            ci_summary,
            "",
            "👉 Правило ревью:",
            "Комментарии, замечания и requested changes оставляем в GitHub PR, не в Telegram.",
        ]
    )
    approval_state = {
        "approval_class": "explicit_approval",
        "approval_id": approval_id,
        "created_at": now_iso(),
        "delivery_route": "prs",
        "item_id": job.get("item_id"),
        "job_id": job.get("job_id"),
        "project_key": job.get("project_key"),
        "run_id": run_id,
        "session_key": f"approval:{approval_id}",
        "status": "approved" if os.environ.get("CONTROL_APPROVED", "").lower() in {"1", "true", "yes", "on"} else "pending",
        "title": pr_meta.get("title") or job.get("title") or "PR ready",
    }
    atomic_write_json(state_dir() / "approvals" / f"{slug(approval_id)}.json", approval_state)
    outbox_payload = {
        "approval_id": approval_id,
        "chat_env": "TELEGRAM_PRS_CHAT_ID",
        "chat_id_present": bool(os.environ.get("TELEGRAM_PRS_CHAT_ID")),
        "message": message,
        "route": "prs",
        "run_id": run_id,
        "timestamp": now_iso(),
    }
    atomic_write_json(state_dir() / "outbox" / "prs" / f"{slug(run_id)}.json", outbox_payload)
    record_event(
        "sdlc-pr-digest",
        {
            "approval_id": approval_id,
            "event_type": "sdlc.ci.passed",
            "item_id": job.get("item_id"),
            "project_key": job.get("project_key"),
            "run_id": run_id,
            "timestamp": now_iso(),
        },
    )
    return {"approval_id": approval_id, "run_id": run_id}


def record_ci(project_key: str, item_id: str, payload_path: str) -> int:
    job = load_job(project_key, item_id)
    pr_path = pr_meta_path(project_key, item_id)
    if not pr_path.exists():
        print(json.dumps({"status": "error", "summary": f"pr not recorded for {project_key}/{item_id}"}, sort_keys=True))
        return 1
    pr_meta = json.loads(pr_path.read_text(encoding="utf-8"))
    payload = load_payload(payload_path)
    status = str(payload.get("status") or payload.get("conclusion") or "unknown").lower()
    summary = payload.get("summary") or payload.get("description") or "CI update received"
    meta = {
        "conclusion": payload.get("conclusion") or status,
        "item_id": item_id,
        "project_key": project_key,
        "run_id": os.environ.get("RUN_ID", f"ci-{slug(item_id)}"),
        "status": status,
        "summary": summary,
        "timestamp": now_iso(),
        "workflow": payload.get("workflow") or payload.get("name") or "ci",
    }
    atomic_write_json(ci_meta_path(project_key, item_id), meta)
    job["ci_status"] = status
    job["updated_at"] = now_iso()
    if status == "passed":
        digest = prepare_pr_digest(job, pr_meta, meta)
        job["pr_digest_approval_id"] = digest["approval_id"]
        job["pr_digest_status"] = "pending"
        job["state"] = "awaiting_pr_digest_approval"
        push_state_to_ui(job.get("owner", "review-watcher"), "idle", f"CI passed, digest pending approval", job)
    else:
        job["state"] = "ci_failed"
        push_state_to_ui(job.get("owner", "review-watcher"), "error", f"CI failed: {summary[:100]}", job)
    atomic_write_json(job_path(project_key, item_id), job)
    maybe_sync_project_status(job, job["state"])
    record_event(
        "sdlc-ci-record",
        {
            "event_type": f"sdlc.ci.{status}",
            "item_id": item_id,
            "project_key": project_key,
            "timestamp": now_iso(),
            "workflow": meta["workflow"],
        },
    )
    result = {"ci_status": status, "status": "ok", "summary": f"recorded ci status {status}"}
    if status == "passed":
        result["pr_digest_approval_id"] = job["pr_digest_approval_id"]
    print(json.dumps(result, sort_keys=True))
    return 0


def status(project_key: str, item_id: str) -> int:
    job = load_job(project_key, item_id)
    spec_meta_file = spec_meta_path(project_key, item_id)
    branch_file = branch_meta_path(project_key, item_id)
    pr_file = pr_meta_path(project_key, item_id)
    ci_file = ci_meta_path(project_key, item_id)
    approval = None
    approval_id = job.get("approval_id")
    if approval_id:
        approval_path = state_dir() / "approvals" / f"{slug(approval_id)}.json"
        if approval_path.exists():
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
    pr_digest_approval = None
    pr_digest_approval_id = job.get("pr_digest_approval_id")
    if pr_digest_approval_id:
        pr_digest_approval_path = state_dir() / "approvals" / f"{slug(pr_digest_approval_id)}.json"
        if pr_digest_approval_path.exists():
            pr_digest_approval = json.loads(pr_digest_approval_path.read_text(encoding="utf-8"))
    payload = {
        "approval": approval,
        "branch": json.loads(branch_file.read_text(encoding="utf-8")) if branch_file.exists() else None,
        "ci": json.loads(ci_file.read_text(encoding="utf-8")) if ci_file.exists() else None,
        "job": job,
        "pr": json.loads(pr_file.read_text(encoding="utf-8")) if pr_file.exists() else None,
        "pr_digest_approval": pr_digest_approval,
        "spec": json.loads(spec_meta_file.read_text(encoding="utf-8")) if spec_meta_file.exists() else None,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: sdlc_ops.py <normalize-webhook|sync|from-webhook|prepare-spec|publish-spec|publish-request|publish-artifact|bootstrap-branch|run-coder|record-pr|record-ci|status> ...",
            file=sys.stderr,
        )
        return 1

    command = sys.argv[1]
    if command == "normalize-webhook":
        return normalize_webhook(sys.argv[2])
    if command == "sync":
        return sync(sys.argv[2])
    if command == "from-webhook":
        return from_webhook(sys.argv[2])
    if command == "prepare-spec":
        return prepare_spec(sys.argv[2], sys.argv[3])
    if command == "publish-spec":
        return publish_spec(sys.argv[2], sys.argv[3])
    if command == "publish-artifact":
        return publish_spec_artifact(sys.argv[2], sys.argv[3])
    if command == "publish-request":
        return publish_request(sys.argv[2])
    if command == "bootstrap-branch":
        return bootstrap_branch(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    if command == "run-coder":
        apply = "--apply" in sys.argv[4:] or bool_env("CONTROL_CODER_APPLY")
        return run_coder(sys.argv[2], sys.argv[3], apply=apply)
    if command == "record-pr":
        return record_pr(sys.argv[2], sys.argv[3], sys.argv[4])
    if command == "record-ci":
        return record_ci(sys.argv[2], sys.argv[3], sys.argv[4])
    if command == "status":
        return status(sys.argv[2], sys.argv[3])

    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
