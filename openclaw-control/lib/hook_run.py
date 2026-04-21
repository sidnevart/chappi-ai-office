#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

from state_validate import validate_payload


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "hooks" / "registry.yaml"


def load_registry() -> dict[str, dict]:
    hooks = {}
    current = None
    for raw in REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if text in {"version: 1", "hooks:"}:
            continue
        if indent == 2 and text.startswith("- id:"):
            hook_id = text.split(":", 1)[1].strip()
            current = {"id": hook_id}
            hooks[hook_id] = current
            continue
        if current and indent == 4 and ":" in text:
            key, value = text.split(":", 1)
            current[key.strip()] = value.strip()
    return hooks


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("usage: oc-hook-run <hook-id> [payload.json]", file=sys.stderr)
        return 1
    hook_id = sys.argv[1]
    payload_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    hooks = load_registry()
    hook = hooks.get(hook_id)
    if not hook:
        print(json.dumps({"status": "error", "summary": f"unknown hook id: {hook_id}"}))
        return 1

    if payload_path:
        schema_name = hook.get("input_schema")
        if schema_name:
          errors = validate_payload(schema_name, payload_path)
          if errors:
              print(json.dumps({"status": "error", "summary": f"schema validation failed for {hook_id}", "errors": errors}))
              return 1
    handler = ROOT / hook["handler"]
    env = os.environ.copy()
    env.setdefault("RUN_ID", f"hook-{hook_id}")
    command = [str(handler)]
    if payload_path:
        command.append(str(payload_path))
    completed = subprocess.run(command, capture_output=True, text=True, env=env)
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
