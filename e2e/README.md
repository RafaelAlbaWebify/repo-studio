# Repo Studio — Playwright E2E suites

These tests create a **temporary synthetic Git repository** and start Repo Studio on an available local port with a separate temporary data directory. They never run against an installed Repo Studio or any user repository. The test deliberately does not execute the repository's Python code.

## Requirements (Linux / Omarchy)

- Python 3.10+, Git, Python package `playwright`, and Chromium.
- Install if needed: `python -m pip install --user playwright` and `python -m playwright install chromium`. On Arch/Omarchy where system Python is externally managed, create a venv outside this project instead.
- If using system Chromium, pass `--chromium /usr/bin/chromium` to avoid downloading a Playwright browser.

Run from the unpacked release directory:

```sh
python -B e2e/run.py --chromium /usr/bin/chromium
```

The script creates `~/Downloads/repo-studio-e2e-results/` containing `report.json`, screenshots, browser diagnostics, downloaded evidence, and `REPO_STUDIO_E2E_RESULTS.zip`. **Review exported evidence before sharing**, even when using test fixtures. The script never installs or upgrades Repo Studio.

Pass: main UI flows completed in Chromium. Fail: a check or browser failed. Blocked: environmental restriction, not a product pass. E2E does not verify the Omarchy launcher, an actual installation/update/rollback, or full security.

## E2E v2 fixes

Playwright locator assertions replace JavaScript-string `wait_for_function`, which conflicts with the app's strict CSP. A failed export test captures a screenshot and closes the modal before subsequent checks. The application CSP is intentionally unchanged. Browser console, page and HTTP errors fail the suite.

## Investigation Workspace 0.9.8

Run `python3 -B e2e/workspace_acceptance.py --output ./workspace-e2e-results` using a Python environment with Playwright/Chromium. Creates a temporary Git fixture, isolated SQLite and test-only exports; a success result covers eight Workspace UI checks.
