# .github

Organization-wide files for [CandleStack-FEI-STU](https://github.com/CandleStack-FEI-STU).

- `profile/README.md`: the organization profile shown on the GitHub organization page.
- `profile/assets/`: images for the profile, such as the logo.
- `SECURITY.md`: the security policy, shown in the Security tab of every repository.
- `CONTRIBUTING.md`: how the team works, with the Definition of Ready and of Done; shown for every repository without its own.
- `.github/ISSUE_TEMPLATE/`: the issue forms (task, bug, spike) of every repository without its own.
- `.github/workflows/no-ai-signs.yml`: shared check that every repository runs as the first CI job.
- `.github/workflows/linked-issue.yml`: shared check that the pull request description closes an issue ("Closes #N"); the tech lead and Dependabot are exempt.
- `.github/workflows/check.yml`: runs this repository's own copy of both checks on its pull requests.
