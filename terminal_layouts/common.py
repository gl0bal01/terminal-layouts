"""Shared manifest loading + path resolution for terminal-layouts generators."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
# Manifest ships inside the package (works both in-repo and installed via uvx).
# Override with TL_MANIFEST_DIR to point at an external manifest tree.
MANIFEST_DIR = Path(os.environ.get("TL_MANIFEST_DIR", PACKAGE_DIR / "manifest"))
DEFAULTS_FILE = MANIFEST_DIR / "defaults.yaml"
WORKFLOWS_DIR = MANIFEST_DIR / "workflows"
SCHEMA_FILE = MANIFEST_DIR / "schema.json"


def load_yaml(path: Path) -> Any:
    with path.open() as f:
        return yaml.safe_load(f)


def load_defaults() -> dict[str, Any]:
    return load_yaml(DEFAULTS_FILE)


def load_workflow(workflow_id: str) -> dict[str, Any]:
    path = WORKFLOWS_DIR / f"{workflow_id}.yaml"
    if not path.exists():
        sys.exit(f"error: workflow not found: {workflow_id} (looked at {path})")
    wf = load_yaml(path)
    wf.setdefault("prefix", "")
    return wf


def list_workflows() -> list[str]:
    return sorted(p.stem for p in WORKFLOWS_DIR.glob("*.yaml"))


_PATH_REF = re.compile(r"\$paths\.([a-z]+)")


def resolve_path(value: str, defaults: dict[str, Any]) -> str:
    """Resolve $paths.X references and ~ expansion."""
    if not isinstance(value, str):
        return value

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        paths = defaults.get("paths", {})
        if key not in paths:
            sys.exit(f"error: unknown $paths.{key} reference (known: {list(paths)})")
        return str(paths[key])

    value = _PATH_REF.sub(_sub, value)
    # Expand ~ using $HOME
    if value.startswith("~/"):
        value = os.path.expanduser(value)
    elif value == "~":
        value = os.path.expanduser("~")
    return value


def resolve_cwd(wf: dict[str, Any], defaults: dict[str, Any]) -> str | None:
    cwd = wf.get("cwd")
    if cwd is None:
        return None
    return resolve_path(cwd, defaults)


def pane_is_leaf(pane: dict[str, Any]) -> bool:
    return "id" in pane


def pane_name(pane: dict[str, Any]) -> str:
    return pane.get("name") or pane.get("id", "pane")


def normalize_size(size: Any) -> str:
    """Return size as a string like '70%'."""
    if size is None:
        return ""
    if isinstance(size, (int, float)):
        return f"{int(size)}%"
    return str(size)


def size_percent(size: Any) -> int | None:
    """Return size as integer percent, or None."""
    if size is None:
        return None
    if isinstance(size, (int, float)):
        return int(size)
    s = str(size)
    if s.endswith("%"):
        try:
            return int(s[:-1])
        except ValueError:
            return None
    return None
