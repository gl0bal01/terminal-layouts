#!/usr/bin/env python3
"""validate.py — validate all workflow manifests against schema.json.

Exits non-zero on any validation error.
"""
from __future__ import annotations

import json
import sys

from jsonschema import Draft7Validator

from terminal_layouts import common


def main() -> int:
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

    if errors:
        print(f"\n{errors} workflow(s) failed validation")
        return 1
    print(f"\nAll {len(workflows)} workflow(s) valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
