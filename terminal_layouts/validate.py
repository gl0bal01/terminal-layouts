#!/usr/bin/env python3
"""validate.py — validate all workflow manifests against schema.json.

Exits non-zero on any validation error.
"""
from __future__ import annotations

import json

from terminal_layouts import common


def main() -> int:
    from jsonschema import Draft7Validator

    with common.SCHEMA_FILE.open() as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)

    workflows = common.list_workflows()
    if not workflows:
        print("error: no workflows found in manifest/workflows/")
        return 1

    errors = 0
    for wf_id in workflows:
        wf = common.load_workflow(wf_id)
        errs = sorted(validator.iter_errors(wf), key=lambda e: list(e.path))
        if errs:
            errors += 1
            print(f"FAIL: {wf_id}")
            for e in errs:
                path = ".".join(str(p) for p in e.path) or "<root>"
                print(f"  {path}: {e.message}")
        else:
            print(f"OK: {wf_id}")

    from terminal_layouts import shell_init

    # Ids become shell commands (tmux-<id>, ...): they must not shadow tmux-ls & co.
    for wf_id in workflows:
        if wf_id in shell_init.RESERVED:
            errors += 1
            print(f"FAIL: {wf_id}: workflow id clashes with a session command (<backend>-{wf_id})")

    # Sessions launched from a directory are named <prefix><dir>: prefixes must
    # be unique, or two workflows opened from one directory would share a session.
    owners: dict[str, str] = {}
    for wf_id in workflows:
        prefix = common.load_workflow(wf_id).get("prefix", "")
        if prefix in owners:
            errors += 1
            print(f"FAIL: {wf_id}: prefix {prefix!r} already used by {owners[prefix]}")
        else:
            owners[prefix] = wf_id

    if errors:
        print(f"\n{errors} workflow(s) failed validation")
        return 1
    print(f"\nAll {len(workflows)} workflow(s) valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
