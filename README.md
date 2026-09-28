# .github

Organization-wide files for [CandleStack-FEI-STU](https://github.com/CandleStack-FEI-STU).

- `profile/README.md`: the organization profile shown on the GitHub organization page.
- `profile/assets/`: images for the profile, such as the logo.
- `SECURITY.md`: the security policy, shown in the Security tab of every repository.
- `CONTRIBUTING.md`: how the team works, with the Definition of Ready and of Done; shown for every repository without its own.
- `.github/ISSUE_TEMPLATE/`: the issue forms (task, bug, spike) of every repository without its own.
- `.github/workflows/no-ai-signs.yml`: shared check that every repository runs as the first CI job.
- `.github/workflows/linked-issue.yml`: shared check that the pull request description closes an issue ("Closes #N"); the tech lead and Dependabot are exempt.
- `scripts/check_comments.py`: the comment check other repositories run through pre-commit (hook `comments` in `.pre-commit-hooks.yaml`, pinned to a commit SHA of this repository). It fails on a TODO/FIXME/XXX/HACK without an issue, such as `TODO(#123): ...`, and on commented-out code in TypeScript, JavaScript and Astro; it warns on changelog wording in comments and on Python functions longer than 40 lines. Tests in `tests/`.
- `.github/workflows/pr-hygiene.yml`: shared check of the pull request: the title is the squash commit (sentence case, imperative, no trailing period, at most 72 characters, no `type:` prefix) and the branch is `<area>/<topic>`; above 1000 changed lines (lockfiles, fixtures and generated snapshots aside) it only warns. Callers grant `pull-requests: read` and run it again on `edited`.
- `.github/workflows/check.yml`: runs this repository's own copy of the shared checks, the tests and the pre-commit hooks on its pull requests.
- `.pre-commit-config.yaml`, `.editorconfig`, `.editorconfig-checker.json`, `.markdownlint-cli2.jsonc`, `.github/zizmor.yml`: this repository's hooks and their settings, also the template for the other repositories. Install them once per clone with `uvx pre-commit install`.
