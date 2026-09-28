#!/usr/bin/env python3
"""Check comments and function length in the files given on the command line.

Errors (exit code 1):
  todo-issue      TODO/FIXME/XXX/HACK without an issue reference such as (#123).
  commented-code  Commented-out code in TypeScript, JavaScript and Astro files. Python is
                  left to ruff's ERA rules.
Warnings (never change the exit code):
  changelog       Changelog wording in a comment: history belongs in the commit message.
  long-function   A Python function body longer than 40 lines. TypeScript and JavaScript are
                  left to oxlint's max-lines-per-function.

Inside GitHub Actions the findings are also printed as annotations. A line whose comment
contains "check-comments: ignore" is skipped. Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

MAX_FUNCTION_LINES = 40
IGNORE = "check-comments: ignore"

TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
ISSUE_REF = re.compile(r"\((?:[\w.-]+/[\w.-]+)?#\d+\)")
CHANGELOG = re.compile(
    r"\b(previously|originally|no longer|old version|used to (?:be|return|use|call|have)|"
    r"was changed|we changed|changed from|refactored|now (?:uses|returns|does)|"
    r"instead of the old|(?:added|fixed) in #\d+)\b",
    re.IGNORECASE,
)
DIRECTIVE = re.compile(
    r"^\s*(?:eslint|oxlint|prettier|@ts-|istanbul|c8|v8|biome|global\b|jshint|#region|#endregion)"
    r"|^\s*(?:<reference|/\s*<reference)"
)
# Comment text that reads as a statement rather than prose.
CODE_LIKE = [
    re.compile(r"^(?:const|let|var)\s+[\w${}\[\], ]+\s*[=:;]"),
    re.compile(r"^(?:if|for|while|switch|catch)\s*\(.*\)\s*\{?$"),
    re.compile(r"^(?:\}\s*)?else\b.*\{$"),
    re.compile(r"^return\b.*;$"),
    re.compile(r"^(?:import|export)\s.*(?:\bfrom\s+['\"]|[{;]$)|^export\s+default\s"),
    re.compile(r"^(?:async\s+)?function\s*\*?\s*[\w$]*\s*\("),
    re.compile(r"^await\s+[\w$.]+\("),
    re.compile(r"^[\w$]+(?:\.[\w$]+)+\(.*\);?$"),
    re.compile(r"^[\w$.\[\]]+\s*(?:[-+*/]?=|\+\+|--)\s*.*;$"),
    re.compile(r"^[\w$.]+\(.*\);$"),
    re.compile(r"=>\s*\{?$|^\(.*\)\s*=>"),
    re.compile(r"^[})\]]+[;,]?$"),
]
MARKUP_LIKE = re.compile(r"^</?[A-Za-z][\w.-]*(?:\s[^>]*)?/?>")

C_LIKE = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".astro", ".css", ".html"}
CODE_CHECKED = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".astro"}
HASH = {".sh", ".bash", ".yml", ".yaml", ".toml", ".cfg", ".ini"}


@dataclass(frozen=True)
class Comment:
    line: int
    text: str
    own_line: bool = True


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str
    error: bool

    def plain(self) -> str:
        level = "error" if self.error else "warning"
        return f"{self.path}:{self.line}: {level} {self.rule}: {self.message}"

    def annotation(self) -> str:
        level = "error" if self.error else "warning"
        text = self.plain().replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        path = self.path.replace("%", "%25").replace(",", "%2C").replace(":", "%3A")
        return f"::{level} file={path},line={self.line},title={self.rule}::{text}"


def _outside_quotes(before: str) -> bool:
    return all(before.count(q) % 2 == 0 for q in ("'", '"', "`"))


def python_comments(src: str) -> list[Comment]:
    comments = []
    lines = src.splitlines()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            row, col = tok.start
            own = not lines[row - 1][:col].strip()
            comments.append(Comment(row, tok.string[1:].strip(), own))
    return comments


def python_docstrings(tree: ast.AST) -> list[Comment]:
    docs = []
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not (isinstance(body, list) and body and isinstance(body[0], ast.Expr)):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for offset, text in enumerate(value.value.splitlines()):
                docs.append(Comment(value.lineno + offset, text.strip()))
    return docs


def hash_comments(src: str) -> list[Comment]:
    comments = []
    for n, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#!") and n == 1:
            continue
        if stripped.startswith("#"):
            comments.append(Comment(n, stripped.lstrip("#").strip()))
            continue
        match = re.search(r"\s#\s", line)
        if match and _outside_quotes(line[: match.start()]):
            comments.append(Comment(n, line[match.end() :].strip(), own_line=False))
    return comments


def c_like_comments(src: str) -> list[Comment]:
    """Own-line // and /* */ comments, HTML comments and trailing // comments."""
    comments = []
    block_end: str | None = None
    for n, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if block_end:
            text = stripped.split(block_end)[0].lstrip("*").strip()
            comments.append(Comment(n, text))
            if block_end in stripped:
                block_end = None
            continue
        for opener, closer in (("/*", "*/"), ("<!--", "-->")):
            if stripped.startswith(opener):
                body = stripped[len(opener) :]
                if closer not in body:
                    block_end = closer
                comments.append(Comment(n, body.split(closer)[0].lstrip("*").strip()))
                break
        else:
            if stripped.startswith("//"):
                comments.append(Comment(n, stripped.lstrip("/").strip()))
                continue
            match = re.search(r"(?<![:\\])//\s", line)
            if match and _outside_quotes(line[: match.start()]):
                comments.append(Comment(n, line[match.end() :].strip(), own_line=False))
    return [c for c in comments if c.text]


def jsdoc_lines(src: str) -> set[int]:
    """Lines inside /** ... */ blocks: examples there are documentation, not dead code."""
    inside, lines = False, set()
    for n, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("/**"):
            inside = "*/" not in stripped[3:]
            lines.add(n)
        elif inside:
            lines.add(n)
            inside = "*/" not in stripped
    return lines


def looks_like_code(text: str, suffix: str) -> bool:
    if DIRECTIVE.search(text):
        return False
    if suffix == ".astro" and MARKUP_LIKE.search(text):
        return True
    return any(p.search(text) for p in CODE_LIKE)


def long_functions(tree: ast.AST) -> list[tuple[int, str, int]]:
    """(line, name, body length) of each function whose body, docstring aside, is too long."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and len(body) > 1:
            first = body[1]
        length = (node.end_lineno or node.lineno) - first.lineno + 1
        if length > MAX_FUNCTION_LINES:
            found.append((node.lineno, node.name, length))
    return found


def parse(path: Path, src: str) -> tuple[list[Comment], list[Comment], list[Finding]] | None:
    """(comments, text checked for changelog wording, function findings); None if unsupported."""
    name, suffix = str(path), path.suffix
    if suffix in {".py", ".pyi"}:
        try:
            tree = ast.parse(src)
            comments = python_comments(src)
        except (SyntaxError, tokenize.TokenError):
            return (
                [],
                [],
                [Finding(name, 1, "syntax", "cannot parse the file, fix the syntax first", True)],
            )
        functions = [
            Finding(
                name,
                line,
                "long-function",
                f"{func}() has a {length}-line body (guideline {MAX_FUNCTION_LINES}): "
                "split it into smaller functions",
                False,
            )
            for line, func, length in long_functions(tree)
        ]
        return comments, comments + python_docstrings(tree), functions
    if suffix in C_LIKE:
        comments = c_like_comments(src)
    elif suffix in HASH or path.name.startswith("Dockerfile"):
        comments = hash_comments(src)
    else:
        return None
    return comments, comments, []


def comment_findings(
    name: str, suffix: str, comments: list[Comment], jsdoc: set[int]
) -> list[Finding]:
    findings = []
    for c in comments:
        todo = TODO.search(c.text)
        if todo and not ISSUE_REF.search(c.text):
            word = todo.group(1)
            message = (
                f"{word} without an issue: write '{word}(#123): ...' with a real issue, "
                "or remove it"
            )
            findings.append(Finding(name, c.line, "todo-issue", message, True))
        if (
            suffix in CODE_CHECKED
            and c.own_line
            and c.line not in jsdoc
            and looks_like_code(c.text, suffix)
        ):
            message = "commented-out code: delete it, git keeps the history"
            findings.append(Finding(name, c.line, "commented-code", message, True))
    return findings


def changelog_findings(name: str, texts: list[Comment]) -> list[Finding]:
    findings = []
    for c in texts:
        match = CHANGELOG.search(c.text)
        if match:
            message = (
                f"history in a comment ('{match.group(0)}'): describe the code as it is now, "
                "the history belongs in the commit message"
            )
            findings.append(Finding(name, c.line, "changelog", message, False))
    return findings


def check_file(path: Path) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    parsed = parse(path, src)
    if parsed is None:
        return []
    comments, texts, findings = parsed
    name, suffix = str(path), path.suffix
    jsdoc = jsdoc_lines(src) if suffix in CODE_CHECKED else set()
    findings = (
        findings + comment_findings(name, suffix, comments, jsdoc) + changelog_findings(name, texts)
    )
    ignored = {n for n, line in enumerate(src.splitlines(), 1) if IGNORE in line}
    return sorted((f for f in findings if f.line not in ignored), key=lambda f: (f.line, f.rule))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    findings = [f for path in args.files for f in check_file(path)]
    for f in findings:
        print(f.annotation() if in_actions else f.plain())
    errors = sum(f.error for f in findings)
    warnings = len(findings) - errors
    if findings:
        print(f"check-comments: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
