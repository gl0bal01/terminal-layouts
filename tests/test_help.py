"""tl help (the manual), tl -h and every `tl COMMAND -h`.

Completion of `tl help TOPIC` in bash and zsh is tested in test_shell.py.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from terminal_layouts import cli, common, manual, shell_init

REPO = Path(__file__).resolve().parent.parent


def tl(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(list(argv))
        except SystemExit as exc:  # argparse: -h and usage errors
            rc = exc.code
    return rc, out.getvalue(), err.getvalue()


def tl_process(*argv: str, env: dict | None = None, **kwargs) -> subprocess.CompletedProcess:
    full_env = {**os.environ, "PYTHONPATH": str(REPO), **(env or {})}
    return subprocess.run([sys.executable, "-m", "terminal_layouts.cli", *argv], capture_output=True,
                          text=True, env=full_env, **kwargs)


def commands() -> dict[str, argparse.ArgumentParser]:
    parser = cli.build_parser()
    return next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices


def word(text: str) -> str:
    """Regex for `text` as a whole word: tmux-kill must not match inside tmux-kill-all."""
    return rf"(?<![\w-]){re.escape(text)}(?![\w-])"


class Manual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc, cls.text, cls.err = tl("help")

    def test_every_workflow_with_directory_prefix_and_description(self):
        self.assertEqual((self.rc, self.err), (0, ""))
        flat = " ".join(self.text.split())
        rows = shell_init.workflows()
        self.assertEqual(sorted(w["id"] for w in rows), common.list_workflows())
        for w in rows:
            with self.subTest(workflow=w["id"]):
                row = re.search(rf"^  {re.escape(w['id'])} +(.+?)  +(\S+)$", self.text, re.M)
                self.assertIsNotNone(row, w["id"])
                self.assertEqual(row.groups(), (w["dir"], w["prefix"] or "-"))
                self.assertIn(" ".join(w["description"].split()), flat)

    def test_every_shell_command(self):
        for backend in shell_init.BACKENDS:
            names = [f"{backend}-{wf}" for wf in common.list_workflows()]
            names += [f"{backend}-{suffix}" for suffix, *_ in shell_init.SESSIONS[backend]]
            for name in names:
                with self.subTest(name=name):
                    self.assertRegex(self.text, word(name))
            self.assertRegex(self.text, rf"\n    {shell_init.CORE[backend]} +=")
        self.assertRegex(self.text, word("layouts"))

    def test_every_option_of_every_command_in_its_own_section(self):
        parsers = {"": cli.build_parser(), **commands()}
        for name, parser in parsers.items():
            # launch, init and install have a topic: their options must be documented there.
            section = tl("help", name)[1] if name in manual.TOPICS else self.text
            for action in parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    continue
                for option in set(action.option_strings) - {"-h", "--help"}:
                    with self.subTest(command=name or "tl", option=option):
                        self.assertRegex(section, word(option))
                for choice in action.choices or ():  # backends, shells, topics
                    with self.subTest(command=name or "tl", choice=choice):
                        self.assertRegex(section if name != "help" else self.text, word(choice))

    def test_init_environment_exit_codes_files_and_quick_start(self):
        for needle in ("QUICK START", 'eval "$(command tl init zsh)"', "TL_INIT_QUIET=1",
                       "TL_MANIFEST_DIR", "XDG_CONFIG_HOME", "EXIT STATUS\n  0   success",
                       "\n  1   failure", "\n  2   usage error",
                       "Only tl install writes to ~/.config", "~/.config/tmuxp",
                       "~/.config/zellij/layouts", "DIR, .", "--new NAME"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.text)

    def test_topics_are_sections_of_the_manual(self):
        headings = {"workflows": "WORKFLOWS", "launch": "LAUNCH", "init": "SHELL COMMANDS",
                    "herdr": "HERDR", "install": "INSTALL"}
        self.assertEqual(sorted(headings), sorted(manual.TOPICS))
        for topic in manual.TOPICS:
            with self.subTest(topic=topic):
                rc, out, _ = tl("help", topic)
                self.assertEqual(rc, 0)
                self.assertTrue(out.startswith(headings[topic] + "\n"), out[:40])
                self.assertIn(out, self.text)
        rc, out, err = tl("help", "nope")
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("invalid choice: 'nope'", err)

    def test_plain_text_79_columns_and_deterministic(self):
        self.assertTrue(self.text.endswith("\n"))
        for line in self.text.splitlines():
            self.assertLessEqual(len(line), 79, line)
        self.assertNotRegex(self.text, r"[\t\x1b\b]")
        for epilog in (cli.TL_EPILOG, cli.GEN_EPILOG, cli.LAUNCH_EPILOG, cli.INIT_EPILOG, cli.LIST_EPILOG,
                       cli.VALIDATE_EPILOG, cli.INSTALL_EPILOG, cli.HELP_EPILOG):
            for line in epilog.splitlines():
                self.assertLessEqual(len(line), 79, line)
        # Piped: no pager (even a failing one), nothing from the terminal or HOME.
        with tempfile.TemporaryDirectory() as home:
            for env in ({"COLUMNS": "40", "HOME": home, "PAGER": "false"},
                        {"COLUMNS": "250", "MANPAGER": "false", "TERM": "dumb"}):
                with self.subTest(env=env):
                    out = tl_process("help", env=env)
                    self.assertEqual((out.returncode, out.stderr), (0, ""))
                    self.assertEqual(out.stdout, self.text)

    @unittest.skipUnless(hasattr(os, "openpty"), "needs a pseudo-terminal")
    def test_a_terminal_gets_the_pager(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_less = Path(tmp, "less")  # records its flags, then "pages" with sed
            fake_less.write_text('#!/bin/sh\necho "less-flags:$*"\nexec sed s/^/paged:/\n')
            fake_less.chmod(0o755)
            path = f"{tmp}{os.pathsep}/usr/bin{os.pathsep}/bin"
            # No pager configured: less -FRX, whatever pydoc does to $LESS (3.13+ replaces it).
            out = self.on_terminal("help", "herdr", env={"PATH": path})
            self.assertIn("less-flags:-FRX", out)
            self.assertIn("paged:HERDR", out)
            # $PAGER (and $MANPAGER) are honoured as they are.
            out = self.on_terminal("help", "herdr", env={"PATH": path, "PAGER": "sed s/^/mine:/"})
            self.assertIn("mine:HERDR", out)
            self.assertNotIn("less-flags", out)
            # Terminals pydoc treats as dumb get plain text, as without tl's default.
            for term in ("dumb", "emacs"):
                out = self.on_terminal("help", "herdr", env={"PATH": path, "TERM": term})
                self.assertIn("\nHERDR\n", "\n" + out)
                self.assertNotIn("less-flags", out)

    def on_terminal(self, *argv: str, env: dict) -> str:
        import pty

        full_env = {**os.environ, "PYTHONPATH": str(REPO), "TERM": "xterm", **env}
        for name in ("MANPAGER", "PAGER"):
            if name not in env:
                full_env.pop(name, None)
        master, slave = pty.openpty()
        proc = subprocess.Popen([sys.executable, "-m", "terminal_layouts.cli", *argv],
                                stdin=slave, stdout=slave, stderr=slave, env=full_env)
        os.close(slave)
        data = b""
        try:
            while select.select([master], [], [], 30)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:  # EIO: every writer to the terminal is gone
                    break
                if not chunk:
                    break
                data += chunk
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise
        finally:
            os.close(master)
        self.assertEqual(rc, 0, data.decode(errors="replace"))
        return data.decode().replace("\r\n", "\n")

    def test_generated_from_the_manifest_in_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp, "manifest")
            shutil.copytree(REPO / "terminal_layouts" / "manifest", tree)
            text = (tree / "workflows" / "project.yaml").read_text()
            (tree / "workflows" / "zz-demo.yaml").write_text(
                text.replace("id: project", "id: zz-demo").replace('prefix: ""', 'prefix: "zz-"')
                .replace("description: Focused single-project session", "description: Demo flow"))
            long_dir = "/srv/" + "very-long-directory-name/" * 2 + "cases"  # 60: too wide for a row
            (tree / "workflows" / "zz-long.yaml").write_text(
                text.replace("id: project", "id: zz-long").replace('prefix: ""', 'prefix: "zl-"')
                .replace("cwd: $PWD", f"cwd: {long_dir}")
                .replace("description: Focused single-project session", "description: see " + "x" * 90))
            # Fits a row with its 3-character prefix, but not under the 6-character PREFIX header.
            (tree / "workflows" / "zz-mid-nineteen-chr.yaml").write_text(
                text.replace("id: project", "id: zz-mid-nineteen-chr").replace('prefix: ""', 'prefix: "rt-"')
                .replace("cwd: $PWD", "cwd: /srv/" + "m" * 44))
            (tree / "workflows" / "pentest.yaml").unlink()
            env = {"TL_MANIFEST_DIR": str(tree)}
            out = tl_process("help", env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertRegex(out.stdout, r"\n  zz-demo +current directory +zz-\n      Demo flow\n")
            self.assertIn(f"\n  zz-long\n      directory {long_dir}\n      prefix zl-\n", out.stdout)
            self.assertIn("tmux-zz-demo", out.stdout)
            self.assertIn("herdr-zz-demo", out.stdout)
            for line in out.stdout.splitlines():
                self.assertLessEqual(len(line), 79, line)
            # The generated parts follow the manifest; only labelled examples name pentest.
            self.assertNotRegex(tl_process("help", "workflows", env=env).stdout, r"\n  pentest ")
            init = tl_process("help", "init", env=env).stdout
            for backend in shell_init.BACKENDS:
                self.assertNotRegex(init, word(f"{backend}-pentest"))
            self.assertIn("Examples use the bundled workflows", out.stdout)
            # A bare `description:` is no description, not a crash (nor "None" in layouts).
            (tree / "workflows" / "zz-null.yaml").write_text(
                text.replace("id: project", "id: zz-null").replace('prefix: ""', 'prefix: "zn-"')
                .replace("description: Focused single-project session", "description:"))
            out = tl_process("help", "workflows", env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertRegex(out.stdout, r"\n  zz-null +current directory +zn-\n\n")
            self.assertNotRegex(tl_process("init", "zsh", env=env).stdout, r"zz-null .*None")
            # An id that cannot become a shell command is a clean error, as for tl init.
            (tree / "workflows" / "ls.yaml").write_text(text.replace("id: project", "id: ls"))
            out = tl_process("help", env={"TL_MANIFEST_DIR": str(tree)})
            self.assertEqual(out.returncode, 1)
            self.assertIn("error: ls: workflow id clashes", out.stderr)
            self.assertNotIn("Traceback", out.stderr)
            for topic in ("launch", "herdr", "install"):  # they list no workflow
                self.assertEqual(tl_process("help", topic, env={"TL_MANIFEST_DIR": str(tree)}).returncode, 0)


class CommandHelp(unittest.TestCase):
    def test_short_overview_with_three_examples_and_every_command(self):
        rc, out, _ = tl("-h")
        self.assertEqual(rc, 0)
        examples = re.split(r"\nexamples[^\n]*:\n", out)[1].split("\n\n")[0]
        self.assertEqual(len(re.findall(r"^  \S", examples, re.M)), 3, examples)
        for name, parser in commands().items():
            with self.subTest(command=name):
                self.assertRegex(out, rf"\n    {name} +\S")
        self.assertIn("tl help", out)
        self.assertIn("\nexamples (bundled workflows):\n", out)
        self.assertLess(len(out.splitlines()), 40)

    def test_every_command_has_description_examples_and_what_it_touches(self):
        for name, parser in commands().items():
            with self.subTest(command=name):
                rc, out, _ = tl(name, "-h")
                self.assertEqual(rc, 0)
                self.assertIn(parser.description.splitlines()[0], out)
                examples = re.split(r"\nexamples[^\n]*:\n", out)[1].split("\n\n")[0]
                self.assertIn(f"tl {name}", examples)
                self.assertRegex(out, r"\ntouches: \S")
                if re.search(word("pentest"), examples):
                    self.assertIn("\nexamples (bundled workflows):\n", out)


if __name__ == "__main__":
    unittest.main()
