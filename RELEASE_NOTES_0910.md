# Repo Studio 0.9.10 beta — installation and integrated Help update

**Maintenance beta** following the published 0.9.9 prerelease.

## Changes from v0.9.9
- Three platform-specific installation guides: `INSTALL_OMARCHY.md`, `INSTALL_UBUNTU.md`, and `WINDOWS_INSTALL.md`.
- More complete in-app Help for Professional findings, Investigation Workspace, export history, source revalidation, evidence coverage and installation.
- Expanded contextual help for Workspace and professional triage filters.
- Documentation regression tests for links, Help anchors and new control descriptions.
- In-app version label and its test updated to 0.9.10.

## Requirements and installation
- **Omarchy:** consult `INSTALL_OMARCHY.md`. New portable installs are different from existing manager-controlled installations. Do not overwrite manager-controlled code by hand.
- **Ubuntu:** consult `INSTALL_UBUNTU.md` for Python 3.10+, Git and portable execution.
- **Windows 10/11:** consult `WINDOWS_INSTALL.md` for PowerShell per-user install, updates and code rollback. Python 3.10+, Git for Windows, PowerShell and a modern browser are required.
- The core uses localhost, requires no paid AI service and does not automatically upload code.

## Evidence and limitations
- v0.9.9 passed GitHub Actions on Linux and Windows, including Chromium E2E and native Windows update/rollback smoke.
- The documentation/Help PR #2 passed all three GitHub CI jobs and was merged into `main` as `bb4c1a0`.
- This v0.9.10 branch still requires its own CI, a release artifact integrity check, and explicit publication.
- The owner's Omarchy 0.9.9 installation was observed working, but v0.9.10 has **not** yet been installed there.
- Independent manual end-user installation on Ubuntu and Windows remains unverified.
- Static findings are advisory; evidence exports may include private source. No end-to-end productivity saving has been established.

The 0.9.9 release is not modified by these updates. Refer to `RELEASE_NOTES_099.md` for historical v0.9.9 details.
