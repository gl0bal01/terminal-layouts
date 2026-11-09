#!/usr/bin/env python3
"""tl — terminal-layouts CLI.

Subcommands:
    tl gen tmux <workflow>      emit tmuxp YAML to stdout
    tl gen zellij <workflow>    emit Zellij KDL to stdout
    tl gen herdr <workflow>     emit the inert Herdr JSON plan to stdout
    tl launch herdr <workflow>  create the workspace in a running Herdr server
    tl list                     list available workflows
    tl validate                 validate all manifests against the schema
    tl install                  write all layouts into the tmuxp/zellij config dirs
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from terminal_layouts import __version__, common, gen_tmux, gen_zellij, gen_herdr, launch_herdr, validate


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _cmd_gen(args: argparse.Namespace) -> int:
    if args.target == "tmux":
        sys.stdout.write(gen_tmux.render(args.workflow))
    elif args.target == "zellij":
        sys.stdout.write(gen_zellij.render(args.workflow))
    else:
        sys.stdout.write(gen_herdr.render(args.workflow))
    return 0


def _cmd_launch(args: argparse.Namespace) -> int:
    workflow = common.load_workflow(args.workflow)
    plan = gen_herdr.compile_plan(workflow, common.load_defaults())
    label, cwd, made = args.label, args.cwd, None
    if args.new is not None:
        # Same convention as the tmux/zellij *-new helpers: <workflow dir>/<name>,
        # workspace named <prefix><name>.
        if not args.new or args.new in (".", "..") or os.sep in args.new:
            print(f"error: --new needs a plain directory name, got {args.new!r}", file=sys.stderr)
            return 2
        cwd = os.path.join(launch_herdr._cwd(plan["cwd"]) or os.getcwd(), args.new)
        made = None if os.path.isdir(cwd) else cwd
        try:
            os.makedirs(cwd, exist_ok=True)
        except OSError as exc:
            print(f"error: cannot create {cwd}: {exc.strerror}", file=sys.stderr)
            return 1
        label = label or workflow.get("prefix", "") + args.new
    if cwd is not None:
        cwd = os.path.abspath(os.path.expanduser(cwd))
        if not os.path.isdir(cwd):
            print(f"error: --cwd {cwd} is not a directory", file=sys.stderr)
            return 2
        plan["cwd"] = cwd
        label = label or os.path.basename(cwd) or plan["label"]
    if label:
        plan["label"] = label
    for warning in plan["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    for missing in launch_herdr.missing_dirs(plan):
        print(f"warning: directory {missing} does not exist; Herdr will open those panes in $HOME",
              file=sys.stderr)
    try:
        workspace_id = launch_herdr.launch(plan, run_commands=args.run_commands)
    except launch_herdr.HerdrError as exc:
        print(f"error: {exc}", file=sys.stderr)
        if made:  # do not leave an empty --new directory behind
            try:
                os.rmdir(made)
            except OSError:
                pass
        return 1
    print(f"Herdr workspace created: {workspace_id}")
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
    gen.add_argument("target", choices=["tmux", "zellij", "herdr"], help="output format")
    gen.add_argument("workflow", help="workflow id (see `tl list`)")
    gen.set_defaults(func=_cmd_gen)

    launch = sub.add_parser("launch", help="explicitly create a Herdr workspace")
    launch.add_argument("target", choices=["herdr"])
    launch.add_argument("workflow", help="workflow id")
    launch.add_argument("--run-commands", action="store_true",
                        help="also execute pane commands from manifest (opt-in)")
    where = launch.add_mutually_exclusive_group()
    where.add_argument("--cwd", metavar="DIR",
                       help="run the workflow in DIR (tabs with their own cwd keep it); "
                            "workspace label defaults to DIR's name")
    where.add_argument("--new", metavar="NAME",
                       help="create <workflow dir>/NAME and launch there, labelled <prefix>NAME")
    launch.add_argument("--label", metavar="TEXT", help="Herdr workspace label")
    launch.set_defaults(func=_cmd_launch)

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
