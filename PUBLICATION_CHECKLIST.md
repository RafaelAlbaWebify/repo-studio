# Publication gates — Linux + Windows beta 0.9.9

- [x] Owner selected `RafaelAlbaWebify/repo-studio` and MIT license.
- [x] MIT license file, public documentation, optional-tool disclosure and Workspace browser CI workflow staged.
- [x] Public ZIP built from an allowlisted source tree, without private evidence packs.
- [ ] Manual independent privacy/security review of source and assets; sign off flagged content.
- [ ] Repeat Playwright after trace-cleanup on Omarchy and ensure no runtime warning.
- [ ] Verify installed 0.9.9 from Omarchy Apps, analyzer configuration, backup and rollback.
- [x] Automated portable launch with an empty Linux HOME, disposable Git fixture, localhost UI/API and restart.
- [ ] Independent clean Linux installation on a separate machine/profile (not yet observed).
- [x] GitHub Actions unit and Playwright jobs passed for commit `fbc32ed` on the review branch (2026-11-16). Re-check after documentation/version changes.
- [ ] Produce and approve screenshots/demo from synthetic data only.
- [ ] Explicit authorization to publish repo/release and LinkedIn post (not yet given).

Windows installation support IS a beta-release requirement. A full-workflow tokens-saved claim is NOT supported and must not be implied.

- [x] Windows runner passed unit, clean-profile, HTTP and Chromium Playwright acceptance for `fbc32ed` (2026-11-16)
- [x] Windows per-user PowerShell installation and rollback checked on GitHub-hosted Windows runner for `fbc32ed`
- [ ] Independent Windows end-user installation and interactive acceptance
