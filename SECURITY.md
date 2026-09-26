# Security policy

This policy covers every repository of CandleStack-FEI-STU.

## Reporting a vulnerability

Please report security issues privately, never in a public issue or pull request: open the
**Security** tab of the affected repository and choose **Report a vulnerability**.

Include what is affected (repository, URL or API endpoint), the steps to reproduce it and the
impact you expect. We acknowledge a report within 7 days and keep you updated until it is fixed.
Please give us reasonable time to fix the issue before you disclose it.

## Scope

- The code in the CandleStack-FEI-STU repositories.
- The public deployment at https://app.candlestack.tech (the web app, the API and its reference).

Out of scope: the team-only environments (stage, previews, ops), third-party services (GitHub,
Cloudflare, Binance, Alpaca), denial-of-service or load testing, and social engineering. Please do
not run automated scanners against production: it runs on a single small server.

## Supported versions

Only the latest release, the one running on https://app.candlestack.tech, receives fixes.
