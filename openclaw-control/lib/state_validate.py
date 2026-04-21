#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_type(expected: str, value) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validate_format(fmt: str, value: str) -> bool:
    if fmt != "date-time":
        return True
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_payload(schema_name: str, payload_path: Path) -> list[str]:
    schema = load_json(SCHEMA_DIR / f"{schema_name}.json")
    payload = load_json(payload_path)
    errors = []
    for key in schema.get("required", []):
        if key not in payload:
            errors.append(f"missing required key: {key}")
    properties = schema.get("properties", {})
    for key, rule in properties.items():
        if key not in payload:
            continue
        value = payload[key]
        expected_type = rule.get("type")
        if expected_type and not validate_type(expected_type, value):
            errors.append(f"{key}: expected {expected_type}")
            continue
        if expected_type == "array" and "items" in rule:
            item_type = rule["items"].get("type")
            if item_type:
                for idx, item in enumerate(value):
                    if not validate_type(item_type, item):
                        errors.append(f"{key}[{idx}]: expected {item_type}")
        if "enum" in rule and value not in rule["enum"]:
            errors.append(f"{key}: unexpected value {value!r}")
        if "pattern" in rule and isinstance(value, str) and re.search(rule["pattern"], value) is None:
            errors.append(f"{key}: does not match {rule['pattern']}")
        if "format" in rule and isinstance(value, str) and not validate_format(rule["format"], value):
            errors.append(f"{key}: invalid format {rule['format']}")
    return errors


def main() -> int:
    if len(sys.argv) < 3 or len(sys.argv[1:]) % 2 != 0:
        print(
            "usage: oc-state-validate <schema_name> <json_path> [<schema_name> <json_path> ...]",
            file=sys.stderr,
        )
        return 1
    pairs = zip(sys.argv[1::2], sys.argv[2::2])
    failures = 0
    for schema_name, payload in pairs:
        payload_path = Path(payload)
        errors = validate_payload(schema_name, payload_path)
        if errors:
            failures += 1
            print(f"[state-validate] {schema_name} {payload_path}: FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[state-validate] {schema_name} {payload_path}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
