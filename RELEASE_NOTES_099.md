# Repo Studio 0.9.9 — Linux + Windows beta

Repo Studio is a **local-first, evidence-first investigation tool** for existing Git repositories. This is a **beta/prerelease**, not a claim of production-grade completeness.

## Highlights
- Professional Findings: normalized analyzer diagnostics, grouped review queues and source-linked evidence.
- Commit-scoped investigation coverage, explicit missing-evidence reporting and human decisions.
- Local SQLite Investigation Workspace for notes, review status, export history and source revalidation.
- Context Builder with human-selected snippets and evidence export for optional external AI review (no automatic AI calls).
- Responsive UI, keyboard improvements and strict Content Security Policy-compatible rendering.

## Install
- **Linux / Omarchy:** use the ZIP in conjunction with the documented local launcher/manager. Requirements: Python 3.10+, Git, browser. Existing Omarchy installs use the versioned ZIP updater with backup and rollback.
- **Windows 10/11:** unpack the ZIP and follow `WINDOWS_INSTALL.md` to install per-user using `install_windows.ps1`. Requirements: Python 3.10+, Git for Windows, PowerShell and a browser.
- No admin privileges or paid API accounts are required for the core application. Optional analyzers such as jscpd/Repowise need separate configuration.

## Verification
- On commit `88e4c72`, GitHub Actions `unit-linux`, `browser-linux`, and `unit-windows` succeeded (run 43854586048). The Windows job included installer/update/rollback and browser acceptance.
- Local isolated Omarchy 0.9.8 → 0.9.9 update, synthetic SQLite persistence and rollback: six acceptance checks passed (2026-11-16).
- Actual Omarchy installation shown running version 0.9.9 at localhost:8765 with Veridra repository and analysis data (2026-11-16).
- CI for the final documentation commit and merged `main` must pass separately before this archive is published.

## Limits
- Independent hands-on end-user installation on separate Linux and Windows devices remains unverified. Automated Windows CI does not replace this.
- No independently signed-off full privacy review; scan and review source exports before external distribution or sharing.
- Static-analysis findings are review candidates, **not** confirmed defects; token counts are estimates and full-workflow time/token savings have **not** been established.
- Committed source excerpts may contain proprietary code or secrets. Review exports before sharing. The app does not automatically upload inspected code or perform refactors.

See `README.md`, `WINDOWS_INSTALL.md`, `SECURITY.md` and `PUBLICATION_CHECKLIST.md`.
