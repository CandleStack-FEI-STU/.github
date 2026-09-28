"""Unit tests for scripts/check_comments.py: python3 -m unittest discover -s tests."""

import contextlib
import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_comments  # noqa: E402


class CheckTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)

    def write(self, name: str, src: str) -> Path:
        path = self.root / name
        path.write_text(textwrap.dedent(src).lstrip("\n"), encoding="utf-8")
        return path

    def rules(self, name: str, src: str) -> list[tuple[int, str, bool]]:
        findings = check_comments.check_file(self.write(name, src))
        return [(f.line, f.rule, f.error) for f in findings]


class TodoTest(CheckTestCase):
    def test_todo_without_issue_is_an_error_in_every_language(self) -> None:
        cases = {
            "a.py": "x = 1  # TODO: tidy up\n",
            "a.ts": "// FIXME handle errors\nexport const x = 1;\n",
            "a.sh": "#!/bin/sh\n# HACK around the proxy\n",
            "a.yml": "on: push # XXX pin this\n",
            "a.css": "/* TODO: dark theme */\n",
            "a.html": "<!-- TODO: add the footer -->\n",
            "a.astro": "---\n// TODO: fetch\n---\n",
        }
        for name, src in cases.items():
            with self.subTest(name=name):
                found = self.rules(name, src)
                self.assertIn("todo-issue", [rule for _, rule, _ in found])
                self.assertTrue(all(error for _, rule, error in found if rule == "todo-issue"))

    def test_todo_with_an_issue_passes(self) -> None:
        self.assertEqual(self.rules("a.py", "# TODO(#12): split this\n"), [])
        self.assertEqual(self.rules("a.ts", "// FIXME(CandleStack-FEI-STU/ops#3): retry\n"), [])
        self.assertEqual(self.rules("a.sh", "# HACK (#7) until the image is fixed\n"), [])

    def test_lowercase_words_and_strings_are_not_todos(self) -> None:
        self.assertEqual(self.rules("a.py", 'x = "TODO"  # a todo list label\n'), [])
        self.assertEqual(self.rules("a.ts", 'const label = "TODO";\n'), [])

    def test_ignore_marker_skips_the_line(self) -> None:
        self.assertEqual(self.rules("a.py", "# TODO: sample text  check-comments: ignore\n"), [])

    def test_reports_the_right_line(self) -> None:
        self.assertEqual(self.rules("a.py", "x = 1\n\n# TODO later\n"), [(3, "todo-issue", True)])


class CommentedCodeTest(CheckTestCase):
    def test_commented_out_statements_are_errors(self) -> None:
        for line in [
            "// const total = items.length;",
            "// let x = 1",
            "// if (ready) {",
            "// return value;",
            "// import { foo } from './foo';",
            "// console.log(data);",
            "// await fetch(url);",
            "// function render(page) {",
            "// }",
            "// count += 1;",
            "// items.map((item) => {",
            "/* export default config; */",
        ]:
            with self.subTest(line=line):
                self.assertEqual(self.rules("a.ts", line + "\n"), [(1, "commented-code", True)])

    def test_commented_out_markup_in_astro(self) -> None:
        src = "<main>\n  <!-- <Header title={title} /> -->\n</main>\n"
        self.assertEqual(self.rules("a.astro", src), [(2, "commented-code", True)])

    def test_prose_is_not_code(self) -> None:
        src = """
        // if the user is signed out, show the login link
        // for each candle we keep the close price
        // return early when the cache is warm
        // See https://developers.cloudflare.com/workers/ for the limits.
        // Keeps the list sorted (newest first).
        // eslint-disable-next-line no-console
        // @ts-expect-error the types lag behind the runtime
        /// <reference types="astro/client" />
        export const x = 1; // trailing note: x = 1;
        """
        self.assertEqual(self.rules("a.ts", src), [])

    def test_jsdoc_examples_are_documentation(self) -> None:
        src = """
        /**
         * Formats a price.
         * @example
         * const text = format(1.5);
         */
        export function format(n: number): string {
          return n.toFixed(2);
        }
        """
        self.assertEqual(self.rules("a.ts", src), [])

    def test_python_and_css_are_not_checked_for_code(self) -> None:
        self.assertEqual(self.rules("a.py", "# x = compute(1)\n"), [])
        self.assertEqual(self.rules("a.css", "/* color: red; */\n"), [])

    def test_urls_in_code_are_not_comments(self) -> None:
        self.assertEqual(self.rules("a.ts", 'const url = "https://x.test/a";\n'), [])


class ChangelogTest(CheckTestCase):
    def test_changelog_wording_is_a_warning(self) -> None:
        for name, src in {
            "a.py": "# previously this returned None\n",
            "b.py": 'def f():\n    """No longer caches the result."""\n',
            "a.ts": "// now uses the v2 endpoint\n",
            "a.yml": "# refactored out of ci.yml\n",
        }.items():
            with self.subTest(name=name):
                found = self.rules(name, src)
                self.assertEqual([rule for _, rule, _ in found], ["changelog"])
                self.assertFalse(found[0][2])

    def test_ordinary_wording_passes(self) -> None:
        self.assertEqual(self.rules("a.py", "# the key used to sign the token\n"), [])


class LongFunctionTest(CheckTestCase):
    @staticmethod
    def function(body_lines: int, docstring: bool = False) -> str:
        doc = '    """Summary."""\n' if docstring else ""
        return "def f():\n" + doc + "".join(f"    x{i} = {i}\n" for i in range(body_lines))

    def test_body_over_the_limit_is_a_warning(self) -> None:
        self.assertEqual(self.rules("a.py", self.function(41)), [(1, "long-function", False)])

    def test_body_at_the_limit_passes(self) -> None:
        self.assertEqual(self.rules("a.py", self.function(40)), [])

    def test_docstring_does_not_count(self) -> None:
        self.assertEqual(self.rules("a.py", self.function(40, docstring=True)), [])

    def test_async_and_nested_functions(self) -> None:
        src = "async def outer():\n    def inner():\n" + "".join(
            f"        y{i} = {i}\n" for i in range(41)
        )
        found = self.rules("a.py", src)
        self.assertEqual(sorted(line for line, _, _ in found), [1, 2])

    def test_typescript_is_left_to_oxlint(self) -> None:
        src = "export function f() {\n" + "  let a = 1;\n" * 60 + "}\n"
        self.assertEqual(self.rules("a.ts", src), [])


class FileHandlingTest(CheckTestCase):
    def test_unknown_and_binary_files_are_skipped(self) -> None:
        self.assertEqual(self.rules("a.md", "TODO: write docs\n"), [])
        path = self.root / "a.png"
        path.write_bytes(b"\x89PNG\xff\xfe")
        self.assertEqual(check_comments.check_file(path), [])

    def test_python_syntax_error_is_reported(self) -> None:
        self.assertEqual(self.rules("a.py", "def (:\n"), [(1, "syntax", True)])

    def test_dockerfile_comments(self) -> None:
        self.assertEqual(self.rules("Dockerfile", "# TODO pin\nFROM x\n")[0][1], "todo-issue")


class MainTest(CheckTestCase):
    def run_main(self, files: list[Path], actions: bool) -> tuple[int, str]:
        out = io.StringIO()
        env = {"GITHUB_ACTIONS": "true"} if actions else {}
        with (
            mock.patch.dict(os.environ, env, clear=True),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = check_comments.main([str(f) for f in files])
        return code, out.getvalue()

    def test_warnings_only_exit_zero(self) -> None:
        path = self.write("a.py", "# previously slow\n")
        code, out = self.run_main([path], actions=False)
        self.assertEqual(code, 0)
        self.assertIn(f"{path}:1: warning changelog:", out)

    def test_errors_exit_one(self) -> None:
        path = self.write("a.py", "# TODO fix\n")
        code, _ = self.run_main([path], actions=False)
        self.assertEqual(code, 1)

    def test_clean_files_exit_zero_silently(self) -> None:
        code, out = self.run_main([self.write("a.py", "x = 1\n")], actions=False)
        self.assertEqual((code, out), (0, ""))

    def test_annotations_in_github_actions(self) -> None:
        warn = self.write("a.py", "# previously slow\n")
        err = self.write("b.ts", "// TODO\n")
        code, out = self.run_main([warn, err], actions=True)
        self.assertEqual(code, 1)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith(f"::warning file={warn},line=1,title=changelog::"))
        self.assertTrue(lines[1].startswith(f"::error file={err},line=1,title=todo-issue::"))


if __name__ == "__main__":
    unittest.main()
