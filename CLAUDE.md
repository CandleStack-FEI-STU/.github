# CLAUDE.md

Organization-wide files of CandleStack-FEI-STU (STU FEI team project): the organization profile,
the security policy and the shared `no-ai-signs` workflow that every repository runs as its
first CI job. See [README.md](README.md).

## Rules

- Everything in English: docs, workflows, commit messages, pull requests.
- Branch from `main` as `<area>/<topic>`; one small pull request per topic. Its title becomes
  the squash commit: imperative, sentence case, no trailing period.
- No AI attribution anywhere: no `Co-Authored-By` trailers of AI tools, no "Generated with ..."
  lines, no session links in commits or pull requests. The `no-ai-signs` check fails on them;
  `.claude/settings.json` already turns Claude Code's attribution off.
- Every path belongs to the tech lead (`.github/CODEOWNERS`): a change needs their approval to merge.
- The shared workflow is called from every repository at `@main`: a change to it takes effect
  everywhere on merge.

## Verify

There is no build. Test the comment check with `python3 -m unittest discover -s tests`. CI runs
those tests and this repository's copy of the shared checks on the pull request itself.
