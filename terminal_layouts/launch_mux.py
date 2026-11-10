"""Launch a tmux (tmuxp) or Zellij session straight from the manifest.

The layout is generated fresh from the manifest every time, so it can never be
stale, and written to a temporary file that is removed once the multiplexer
exits or detaches.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from typing import Any

from terminal_layouts import common, gen_tmux, gen_zellij


class MuxError(RuntimeError):
    """A missing tool or unusable layout."""


def _require(*tools: str) -> None:
    hints = {"tmux": "install tmux >= 3.4", "tmuxp": "pipx install tmuxp",
             "zellij": "see https://zellij.dev/documentation/installation"}
    for tool in tools:
        if shutil.which(tool) is None:
            raise MuxError(f"{tool} not found — {hints[tool]}")


def _run_with_layout(text: str, suffix: str, argv_for: Callable[[str], list[str]],
                     run: Callable[..., Any]) -> int:
    fd, path = tempfile.mkstemp(prefix="tl-", suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return run(argv_for(path)).returncode
    finally:
        os.unlink(path)


def launch_tmux(workflow: dict[str, Any], cwd: str, session: str, *, detach: bool = False,
                run: Callable[..., Any] = subprocess.run) -> int:
    """Load the workflow with tmuxp in `cwd` as session `session`; return its exit code."""
    _require("tmux", "tmuxp")
    wf = dict(workflow, cwd=cwd)  # windows with their own cwd keep it
    text = gen_tmux.emit_tmux(wf, common.load_defaults())

    def argv(path: str) -> list[str]:
        return ["tmuxp", "--color", "never", "load", "--no-progress", "-y", "-s", session,
                *(["-d"] if detach else []), path]

    return _run_with_layout(text, ".yaml", argv, run)


def launch_zellij(workflow: dict[str, Any], cwd: str, session: str, *,
                  run: Callable[..., Any] = subprocess.run) -> int:
    """Start a new Zellij session `session` in `cwd`; return its exit code."""
    _require("zellij")
    text = gen_zellij.emit_zellij(workflow, common.load_defaults())

    def argv(path: str) -> list[str]:
        return ["zellij", "-n", path, "-s", session, "options", "--default-cwd", cwd]

    return _run_with_layout(text, ".kdl", argv, run)
