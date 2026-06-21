#!/usr/bin/env python3
"""tl — terminal-layouts CLI.

Subcommands:
    tl gen tmux <workflow>      emit tmuxp YAML to stdout
    tl gen zellij <workflow>    emit Zellij KDL to stdout
    tl list                     list available workflows
    tl validate                 validate all manifests against the schema
    tl install                  write all layouts into the tmuxp/zellij config dirs
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from terminal_layouts import __version__, common, gen_tmux, gen_zellij, validate


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _cmd_gen(args: argparse.Namespace) -> int:
    if args.target == "tmux":
        sys.stdout.write(gen_tmux.render(args.workflow))
    else:
        sys.stdout.write(gen_zellij.render(args.workflow))
    return 0


def _cmd_list(_args: argparse.Namespace) -> int:
    for wf_id in common.list_workflows():
        print(wf_id)
    return 0


def _cmd_validate(_args: argparse.Namespace) -> int:
    return validate.main()


def _cmd_install(args: argparse.Namespace) -> int:
    cfg = _config_home()
    tmuxp_dir = Path(args.tmuxp_dir) if args.tmuxp_dir else cfg / "tmuxp"
    zellij_dir = Path(args.zellij_dir) if args.zellij_dir else cfg / "zellij" / "layouts"
    do_tmux = not args.zellij_only
    do_zellij = not args.tmux_only

    written: list[Path] = []
    for wf_id in common.list_workflows():
        if do_tmux:
            dst = tmuxp_dir / f"{wf_id}.yaml"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(gen_tmux.render(wf_id))
            written.append(dst)
        if do_zellij:
            dst = zellij_dir / f"{wf_id}.kdl"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(gen_zellij.render(wf_id))
            written.append(dst)

    for path in written:
        print(f"installed: {path}")
    print(f"\n{len(written)} file(s) written.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tl", description="terminal-layouts generator")
    p.add_argument("--version", action="version", version=f"terminal-layouts {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="generate a layout")
    gen.add_argument("target", choices=["tmux", "zellij"], help="output format")
    gen.add_argument("workflow", help="workflow id (see `tl list`)")
    gen.set_defaults(func=_cmd_gen)

    lst = sub.add_parser("list", help="list available workflows")
    lst.set_defaults(func=_cmd_list)

    val = sub.add_parser("validate", help="validate manifests against the schema")
    val.set_defaults(func=_cmd_validate)

    inst = sub.add_parser("install", help="write all layouts into the config dirs")
    grp = inst.add_mutually_exclusive_group()
    grp.add_argument("--tmux-only", action="store_true", help="install tmuxp layouts only")
    grp.add_argument("--zellij-only", action="store_true", help="install Zellij layouts only")
    inst.add_argument("--tmuxp-dir", help="override tmuxp dir (default: $XDG_CONFIG_HOME/tmuxp)")
    inst.add_argument(
        "--zellij-dir", help="override Zellij layouts dir (default: $XDG_CONFIG_HOME/zellij/layouts)"
    )
    inst.set_defaults(func=_cmd_install)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
