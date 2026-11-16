# Repo Studio 0.9.9 — Linux + Windows beta release candidate

**Status:** candidate only. No release published; no merge into `main` authorized.

## What's new
- Professional Findings: grouped analyzer observations, review-first triage queues and source-linked investigation records.
- Conservative commit-scoped coverage and evidence exports for human-controlled analysis.
- Local Investigation Workspace with notes, progress, decisions and export history; evidence remains tied to the inspected commit.
- Keyboard and modal focus improvements, responsive layout fixes and strict CSP-safe rendering.
- Optional Repowise index-backed symbol lookup and jscpd scans; missing tools or indexes are reported, not treated as no findings.

## Verification performed
- Omarchy development lab: 91 Python tests, responsive and targeted Playwright checks passed; clean portable Linux ZIP installation passed.
- GitHub Actions for commit `fbc32ed` on `rc/p0a-professional-triage-20261116`: `unit-linux`, `browser-linux` and `unit-windows` all passed (2026-11-16).
- Windows CI includes installer/update/rollback smoke and Chromium Workspace E2E. Independent manual Windows installation is still pending.

## Known limits and publication gates
- Localhost-only application. The source repository is inspected read-only; Workspace metadata is stored locally.
- Static analysis identifies investigation candidates, not proven defects or safe refactors.
- No automatic source edits, external LLM calls or demonstrated end-to-end productivity gains.
- Independent user installation checks, Omarchy in-place upgrade, privacy sign-off, release approval and demo review are not complete.

Read `README.md`, `WINDOWS_INSTALL.md`, `SECURITY.md` and `PUBLICATION_CHECKLIST.md` before distribution.
