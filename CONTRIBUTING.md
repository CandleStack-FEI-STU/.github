# Contributing

How the team works in every repository of CandleStack-FEI-STU. A repository's own
`CONTRIBUTING.md` or `README.md` adds its commands and checks.

## Issues and the board

- Work is tracked as issues on the project board
  [CandleStack](https://github.com/orgs/CandleStack-FEI-STU/projects/1): Backlog, To Do,
  In Progress, Review, Done. Sprints last two weeks.
- Open an issue from a form: **Task** for work, **Bug** for something broken, **Spike** for
  timeboxed research. Security issues go to the [security policy](SECURITY.md) instead.

## Definition of Ready

Only a ready issue moves from Backlog to To Do, into a sprint. It is ready when:

- its acceptance criteria are a checklist a reviewer can verify;
- its size is S or M; a bigger one is split into sub-issues first;
- it has no open questions;
- "Where to start" names the files and existing code to copy.

## Definition of Done

An issue is done when its pull request is merged, and the pull request:

- links the issue with "Closes #N" in its description (the required check
  `linked-issue / Linked issue`);
- has green CI;
- adds or updates tests at the lowest level that proves the change;
- updates the docs the change affects;
- shows a screenshot or a short demo when something visible changes;
- passed review, with every thread resolved.

## Checks

Every repository runs [pre-commit](https://pre-commit.com) hooks from its `.pre-commit-config.yaml`
on each commit and, on every file, in CI. Install them once per clone:

```sh
uvx pre-commit install
uvx pre-commit run --all-files  # the whole repository, as CI does
```

The shared hooks: whitespace and line endings, valid YAML/JSON/TOML, secrets (gitleaks), typos,
`.editorconfig`, Markdown (markdownlint), actionlint and zizmor on the workflows, and the comment
check: a TODO/FIXME/XXX/HACK names its issue, as in `TODO(#123): ...`, and no commented-out
code. The comment check only warns on changelog wording in comments ("previously", "no longer")
and on functions longer than 40 lines. Each repository adds its own linters and tests.

Every pull request also runs the shared checks `no-ai-signs`, `linked-issue` and `pr-hygiene`
(title and branch name as below; a warning above 1000 changed lines).

## Branches and pull requests

- Branch from `main` as `<area>/<topic>` in lowercase, e.g. `backend/candles-endpoint`; one small
  pull request per topic, squash-merged.
- The pull request title becomes the commit on `main`: imperative, sentence case, no trailing
  period, at most 72 characters, no `feat:`-style prefix, e.g. "Add the candles endpoint".
- Everything in English. No AI attribution in commits or pull requests; the `no-ai-signs`
  check fails on it.
