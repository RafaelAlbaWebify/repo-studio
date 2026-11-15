# Windows release gate — candidate 0.9.8

This release is **not published**. Windows native acceptance has **not** been executed here (Linux environment).

## Verification added

`tools/windows_installer_smoke.py` runs from the `unit-windows` job on GitHub Actions and covers:

1. Fresh installation under a disposable LOCALAPPDATA/APPDATA profile.
2. An injected failure after new code has been staged into place but before configuration is committed. The test checks that the old code, original configuration, state, and free backup slot are recovered.
3. A successful update, backup, and rollback.
4. Refusal to overwrite an existing rollback backup.

`install_windows.ps1` uses distinct staging paths for code and configuration. It preserves `%LOCALAPPDATA%\RepoStudio\data` across operations. The QA failure-injection switch is an environment variable (`REPO_STUDIO_QA_FAIL_BEFORE_CONFIG_COMMIT=1`); do not set it during normal installation.

## Publishing gates still open

- Run `unit-windows` on `windows-latest`, inspect job logs and browser artifacts, and correct any Windows-only defects.
- Verify successful installation/update/rollback with a regular Windows user account, preferably separately from CI.
- Confirm controlled Omarchy update to 0.9.8 preserving configured tools and local state.
- Complete final manual public-content review and obtain explicit publication authorization.

The prior 8/8 Playwright result applies to the Omarchy Workspace workflow; it is not evidence for the changed Windows installer.
