"""The docs stay in step with what `tl init` defines.

docs/usage.md lists every workflow and launch option, each backend tutorial its session commands
and its own option. Something new without its line fails here, and so does a link, image or
#anchor that leads nowhere in any page.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from terminal_layouts import common, shell_init

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
OPTIONS = {"tmux": ["-d"], "zellij": [], "herdr": ["--run-commands"]}  # one backend each
SHARED = ["--new", "--label", "--cwd"]


def word(text: str) -> str:
    return rf"(?<![\w-]){re.escape(text)}(?![\w-])"


def slugs(markdown: str) -> set[str]:
    """GitHub heading anchors: lowercase, punctuation dropped, spaces to hyphens."""
    out = set()
    markdown = re.sub(r"^```.*?^```", "", markdown, flags=re.M | re.S)  # `# comment` is no heading
    for heading in re.findall(r"^#{1,6} +(.+?) *$", markdown, re.M):
        out.add(re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-"))
    return out


class Docs(unittest.TestCase):
    def test_usage_lists_every_workflow_and_shared_option(self):
        text = (DOCS / "usage.md").read_text()
        for wf in common.list_workflows():
            with self.subTest(workflow=wf):
                self.assertRegex(text, rf"(?m)^\| `{re.escape(wf)}` \|")
        for option in SHARED + [o for options in OPTIONS.values() for o in options]:
            with self.subTest(option=option):
                self.assertRegex(text, word(option))

    def test_tutorials_list_their_session_commands_and_option(self):
        for backend in shell_init.BACKENDS:
            text = (DOCS / f"{backend}.md").read_text()
            self.assertIn("](usage.md)", text)
            for suffix, *_ in shell_init.SESSIONS[backend]:
                with self.subTest(backend=backend, command=suffix):
                    self.assertRegex(text, word(f"{backend}-{suffix}"))
            self.assertIn(f"| `{shell_init.CORE[backend]}` | `{backend}` |", text)
            for option in OPTIONS[backend]:
                with self.subTest(backend=backend, option=option):
                    self.assertRegex(text, word(option))

    def test_links_images_and_anchors_resolve(self):
        readme = (REPO / "README.md").read_text()
        for backend in shell_init.BACKENDS:
            self.assertIn(f"](docs/{backend}.md)", readme)
        for page in [*sorted(DOCS.glob("*.md")), REPO / "README.md"]:
            text = page.read_text()
            for target in re.findall(r"\]\(([^)\s]+)\)", text):
                if re.match(r"https?://", target):
                    continue
                path, _, anchor = target.partition("#")
                dest = (page.parent / path).resolve() if path else page
                with self.subTest(page=page.name, link=target):
                    self.assertTrue(dest.exists(), dest)
                    if anchor:
                        self.assertIn(anchor, slugs(dest.read_text()))


if __name__ == "__main__":
    unittest.main()
