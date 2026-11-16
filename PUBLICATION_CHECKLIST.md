# Publication gates — Linux + Windows beta 0.9.9

- [x] Owner selected `RafaelAlbaWebify/repo-studio` and MIT license.
- [x] MIT license file, public documentation, optional-tool disclosure and Workspace browser CI workflow staged.
- [x] Public ZIP built from an allowlisted source tree, without private evidence packs.
- [ ] Manual independent privacy/security review of source and assets; sign off flagged content.
- [ ] Repeat Playwright after trace-cleanup on Omarchy and ensure no runtime warning.
- [x] 0.9.9 observed in Omarchy Apps with configured analyzers; isolated upgrade/rollback and synthetic SQLite persistence passed. Full live rollback intentionally not performed.
- [x] Automated portable launch with an empty Linux HOME, disposable Git fixture, localhost UI/API and restart.
- [ ] Independent clean Linux installation on a separate machine/profile (not yet observed).
- [x] GitHub Actions unit, Chromium Playwright and Windows jobs passed at `88e4c72` (run 43854586048). Final docs commit and merged main are release gates.
- [ ] Produce and approve screenshots/demo from synthetic data only.
- [x] Owner authorized release workflow on 2026-11-16; LinkedIn announcement remains separately publishable once release URL exists.

Windows installation support IS a beta-release requirement. A full-workflow tokens-saved claim is NOT supported and must not be implied.

- [x] Windows runner passed unit, clean-profile, HTTP and Chromium Playwright acceptance for `88e4c72` (2026-11-16)
- [x] Windows per-user PowerShell installation and rollback checked on GitHub-hosted Windows runner for `88e4c72`
- [ ] Independent Windows end-user installation and interactive acceptance
