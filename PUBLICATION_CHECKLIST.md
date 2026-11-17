# Publication acceptance — Repo Studio v0.9.10 beta

## Distribution and automated evidence

- [x] Public MIT repository and release `v0.9.10` with downloadable `REPO_STUDIO_0.9.10_PUBLIC.zip` (owner confirmed via `gh release view`).
- [x] Three platform installation guides: `INSTALL_OMARCHY.md`, `INSTALL_UBUNTU.md`, `WINDOWS_INSTALL.md`.
- [x] In-app Help for Professional findings, Investigation Workspace, export history and source revalidation, observed in the actual 0.9.10 Omarchy install (five version/help checks passed).
- [x] Real Omarchy Apps instance observed running v0.9.10 at localhost:8765. Separately, isolated 0.9.8→0.9.9 update and rollback preserved synthetic SQLite data.
- [x] **Independent automated Ubuntu runner:** GitHub Actions `unit-linux` performs a clean-profile portable install, Python unit/API/SQLite checks; `browser-linux` performs Chromium Playwright E2E against a disposable synthetic Git fixture. These are independent ephemeral CI environments, not a manual end-user acceptance.
- [x] **Independent automated Windows runner:** `unit-windows` performs clean portable install, PowerShell per-user installer/update/backup/rollback, HTTP/SQLite and Chromium Playwright E2E. This is independent hosted Windows CI, not an interactive end-user acceptance.
- [x] Captures produced by genuine Playwright Chromium E2E on the 0.9.10 codebase (run `43940558223`, artifact `14261533731`): initial analysis, saved review, recorded export and historical revalidation, all with synthetic sources.
- [x] PR #4 product introduction and demo guide merged into `main` as `b2b6ddc`.

## Remaining optional/manual acceptance

- [ ] **Manual independent Ubuntu end-user install**, outside GitHub Actions, using only the published package and public guide.
- [ ] **Manual independent Windows end-user install**, outside GitHub Actions, using only the published package and public guide.
- [ ] Owner review and selection of screenshots before attaching to public GitHub documentation/LinkedIn; inspect names, source snippets, notes and file paths.
- [ ] Final independent privacy/security sign-off for all public materials and assets; automated secret-pattern checks alone are not a security audit.
- [ ] Publish approved announcement on LinkedIn.

## Boundaries

- Repo Studio is local-first and reads committed Git source; the local Workspace stores investigation metadata. Source exports can contain confidential code.
- Static findings are investigation candidates, not confirmed defects or safe fixes. No measured end-to-end time or token saving is claimed.
- Native CI verifies fresh runner environments; do not describe CI as independent **manual** acceptance.
- Existing releases must not be silently replaced; significant changes should have a new version.
