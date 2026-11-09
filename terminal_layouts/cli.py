#!/usr/bin/env python3
"""tl — terminal-layouts CLI.

Subcommands:
    tl gen tmux <workflow>      emit tmuxp YAML to stdout
    tl gen zellij <workflow>    emit Zellij KDL to stdout
    tl gen herdr <workflow>     emit the inert Herdr JSON plan to stdout
    tl launch herdr|tmux|zellij <workflow> [DIR]
                                open the workflow (Herdr workspace, tmux/Zellij session)
    tl init zsh|bash            print shell commands (tmux-pentest, ...) + tab completion
    tl list                     list available workflows
    tl validate                 validate all manifests against the schema
    tl install                  write all layouts into the tmuxp/zellij config dirs
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from terminal_layouts import (__version__, common, gen_herdr, gen_tmux, gen_zellij, launch_herdr,
                              launch_mux, validate)


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


def _err(message: str, code: int) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def _cmd_launch(args: argparse.Namespace) -> int:
    workflow = common.load_workflow(args.workflow)
    defaults = common.load_defaults()
    if args.run_commands and args.target != "herdr":
        return _err("--run-commands is Herdr-only (tmux and Zellij always run pane commands)", 2)
    if args.detach and args.target != "tmux":
        return _err("--detach is tmux-only", 2)
    if sum(x is not None for x in (args.dir, args.cwd, args.new)) > 1:
        return _err("give only one of DIR, --cwd or --new", 2)

    manifest_cwd = common.resolve_cwd(workflow, defaults)
    base = launch_herdr._cwd(manifest_cwd) or os.getcwd()
    label, cwd, made = args.label, args.dir or args.cwd, None
    if cwd is None and args.new is None and manifest_cwd == "$PWD":
        cwd = base  # "here" workflows (ai-agents, project) are named after the directory
    if args.new is not None:
        # <workflow dir>/<name>, session/workspace named <prefix><name>.
        if not args.new or args.new in (".", "..") or os.sep in args.new:
            return _err(f"--new needs a plain directory name, got {args.new!r}", 2)
        cwd = os.path.join(base, args.new)
        made = None if os.path.isdir(cwd) else cwd
        try:
            os.makedirs(cwd, exist_ok=True)
        except OSError as exc:
            return _err(f"cannot create {cwd}: {exc.strerror}", 1)
        label = label or workflow.get("prefix", "") + args.new
    if cwd is not None:
        cwd = os.path.abspath(os.path.expanduser(cwd))
        if not os.path.isdir(cwd):
            return _err(f"{cwd} is not a directory", 2)
        label = label or workflow.get("prefix", "") + os.path.basename(cwd)

    rc = _launch_target(args, workflow, defaults, cwd or base, cwd is not None, label)
    if rc and made:  # do not leave an empty --new directory behind
        try:
            os.rmdir(made)
        except OSError:
            pass
    return rc


def _launch_target(args: argparse.Namespace, workflow: dict, defaults: dict, cwd: str,
                   cwd_given: bool, label: str | None) -> int:
    if args.target == "herdr":
        plan = gen_herdr.compile_plan(workflow, defaults)
        if cwd_given:
            plan["cwd"] = cwd
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
            return _err(str(exc), 1)
        print(f"Herdr workspace created: {workspace_id}")
        return 0

    if not os.path.isdir(cwd):
        return _err(f"directory {cwd} does not exist (create it, or launch with DIR, '.' or --new NAME)", 1)
    plan = gen_herdr.compile_plan(workflow, defaults)  # same directory rules for every backend
    plan["cwd"] = cwd
    for missing in launch_herdr.missing_dirs(plan):
        print(f"warning: directory {missing} does not exist; {args.target} will open those panes in $HOME",
              file=sys.stderr)
    session = label or workflow["id"]
    try:
        if args.target == "tmux":
            # tmux silently stores "." and ":" as "_", which breaks re-attaching by name.
            session = session.replace(".", "_").replace(":", "_")
            return launch_mux.launch_tmux(workflow, cwd, session, detach=args.detach)
        return launch_mux.launch_zellij(workflow, cwd, session)
    except launch_mux.MuxError as exc:
        return _err(str(exc), 1)


def _cmd_init(args: argparse.Namespace) -> int:
    from terminal_layouts import shell_init

    backends = [b.strip() for b in args.backends.split(",") if b.strip()] if args.backends else None
    unknown = sorted(set(backends or []) - set(shell_init.BACKENDS))
    if unknown:
        return _err(f"unknown backend(s) {', '.join(unknown)} (choose from tmux, zellij, herdr)", 2)
    try:
        script = shell_init.render(args.shell, backends, force=args.force)
    except ValueError as exc:
        return _err(str(exc), 1)
    sys.stdout.write(script)
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

    launch = sub.add_parser("launch", help="open a workflow: Herdr workspace, tmux or Zellij session")
    launch.add_argument("target", choices=["herdr", "tmux", "zellij"])
    launch.add_argument("workflow", help="workflow id (see `tl list`)")
    launch.add_argument("dir", nargs="?", metavar="DIR",
                        help="run in DIR ('.' = here) instead of the manifest directory; "
                             "named <prefix><DIR name> unless --label")
    launch.add_argument("--cwd", metavar="DIR", help="same as DIR")
    launch.add_argument("--new", metavar="NAME",
                        help="create <workflow dir>/NAME and launch there, named <prefix>NAME")
    launch.add_argument("--label", metavar="NAME",
                        help="Herdr workspace label / tmux or Zellij session name")
    launch.add_argument("--run-commands", action="store_true",
                        help="Herdr only: also run the manifest pane commands (opt-in)")
    launch.add_argument("-d", "--detach", action="store_true",
                        help="tmux only: create the session without attaching")
    launch.set_defaults(func=_cmd_launch)

    init = sub.add_parser("init", help="print shell commands (tmux-pentest, ...) + tab completion",
                          description='Add  eval "$(command tl init zsh)"  (or bash) to your shell rc.')
    init.add_argument("shell", choices=["zsh", "bash"])
    init.add_argument("--backends", metavar="LIST",
                      help="comma-separated subset of tmux,zellij,herdr (default: all)")
    init.add_argument("--force", action="store_true",
                      help="replace existing commands/aliases that have the same names")
    init.set_defaults(func=_cmd_init)

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
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    # argparse cannot take the optional DIR after options (`tl launch tmux pentest -d .`).
    if extra and args.command == "launch" and args.dir is None and len(extra) == 1 \
            and not extra[0].startswith("-"):
        args.dir, extra = extra[0], []
    if extra:
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
