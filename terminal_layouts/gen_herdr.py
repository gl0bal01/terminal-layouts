"""Compile a manifest into a deterministic, inert Herdr workspace plan.

Herdr is an API-backed runtime, not a static layout file. The generated JSON is
an inspectable plan; it does not open Herdr or run any user commands.
"""
from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft7Validator

from terminal_layouts import common

FORMAT = "terminal-layouts.herdr.plan"
VERSION = 1


def _pane(source: dict[str, Any]) -> dict[str, Any]:
    if common.pane_is_leaf(source):
        return {
            "id": source["id"],
            "name": common.pane_name(source),
            "cwd": source.get("cwd"),
            "command": source.get("command") or "",
            "args": source.get("args") or [],
        }
    return {
        "direction": source["direction"],
        "children": [_pane(child) for child in source["children"]],
    }


def _warnings_for(pane: dict[str, Any], path: str) -> list[str]:
    warnings: list[str] = []
    if "size" in pane:
        warnings.append(f"{path}: exact pane size is not mapped to Herdr")
    if pane.get("focus"):
        warnings.append(f"{path}: pane focus is not mapped to Herdr")
    if pane.get("close_on_exit"):
        warnings.append(f"{path}: close_on_exit is not mapped to Herdr")
    for index, child in enumerate(pane.get("children", [])):
        warnings += _warnings_for(child, f"{path}.{index}")
    return warnings


def compile_plan(workflow: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    with common.SCHEMA_FILE.open(encoding="utf-8") as f:
        Draft7Validator(json.load(f)).validate(workflow)
    tabs: list[dict[str, Any]] = []
    warnings: list[str] = []
    for tab in workflow["tabs"]:
        if tab.get("tmux_only") or tab.get("zellij_only"):
            warnings.append(f"tab {tab['id']}: excluded (multiplexer-specific)")
            continue
        for index, pane in enumerate(tab["panes"]):
            warnings += _warnings_for(pane, f"tab {tab['id']}.panes.{index}")
        tabs.append({
            "id": tab["id"],
            "label": (tab.get("emoji", "") + " " + tab["name"]).strip(),
            "focus": tab.get("focus", False),
            "cwd": common.resolve_path(tab["cwd"], defaults) if tab.get("cwd") else None,
            "panes": [_pane(pane) for pane in tab["panes"]],
        })
    if not tabs:
        raise ValueError("Herdr plan has no cross-backend tabs")
    return {
        "format": FORMAT,
        "version": VERSION,
        "id": workflow["id"],
        "label": workflow["name"],
        "cwd": common.resolve_cwd(workflow, defaults),
        "root_direction": defaults.get("defaults", {}).get("root_direction", "row"),
        "tabs": tabs,
        "warnings": warnings,
    }


def render(workflow_id: str) -> str:
    plan = compile_plan(common.load_workflow(workflow_id), common.load_defaults())
    return json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
