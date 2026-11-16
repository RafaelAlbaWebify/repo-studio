# Repo Studio

**Evidence-first investigation of existing Git repositories** · Linux + Windows beta 0.9.10 · Local-first · Read-only source inspection · Human-controlled

Repo Studio is a local web application for examining committed code in legacy Git repositories and assembling traceable evidence for optional AI-assisted analysis. It does **not** upload repository content to AI services, automatically modify inspected source, or assert that a static finding is a defect.

## Understand legacy code before changing it

**Repo Studio** is a free, open-source, local-first workspace for investigating existing Git repositories. It brings source navigation, static-analysis candidates, dependency evidence, human review decisions and carefully scoped AI-ready context together in one browser interface.

**The problem:** legacy repositories often have thousands of files, overlapping analyzer findings and incomplete context. Getting oriented, confirming what an observation actually means and remembering what has already been reviewed can become its own project.

**The approach:** inspect committed code, trace an observation back to its source, record the evidence and your decision, and export only the context you deliberately select. Repo Studio does not modify the inspected repository or automatically send its contents to an AI service.

[**Download the latest beta**](https://github.com/RafaelAlbaWebify/repo-studio/releases/latest) · [**Installation guides**](#installation--omarchy-ubuntu-and-windows) · [**Security and limitations**](SECURITY.md) · [**Demonstration guide**](docs/DEMO_GUIDE.md)

### What you can do

1. **Explore:** browse committed files, Python import cycles, complexity candidates and duplication matches; follow source locations instead of treating findings as conclusions.
2. **Triage:** inspect imported professional analyzer observations, apply reversible filters and distinguish review priority from proven severity.
3. **Investigate:** examine dependency evidence, identify missing context and assemble compact or extended source excerpts under your control.
4. **Remember:** keep local SQLite-backed investigation notes, progress, human decisions and export history scoped to the repository and commit.
5. **Revalidate:** see whether recorded source evidence has changed across commits, without assuming an unchanged excerpt guarantees unchanged behavior.

<details>
<summary><strong>What Repo Studio is not</strong></summary>

It is not an autonomous refactoring agent, an all-language code-quality oracle or a hosted AI service. Python AST analysis has intentional limits; jscpd and Repowise require separate optional installation/configuration. Findings are candidates for human review. There is no demonstrated end-to-end time or token saving to claim. The beta passed automated Linux/Windows CI, but independent manual installations on every platform have not been completed.

</details>

### At a glance

| | |
| --- | --- |
| **License** | MIT |
| **Platform** | Linux (including Omarchy and Ubuntu) and Windows 10/11 |
| **Runtime** | Python 3.10+, Git, browser; no required runtime pip packages |
| **Data model** | Localhost service; reads committed Git HEAD, persists separate local review state |
| **AI integration** | Human-selected export; no automatic LLM calls or code uploads |
| **Release** | [v0.9.10 beta](https://github.com/RafaelAlbaWebify/repo-studio/releases/tag/v0.9.10) |

## Features

- Git commit-pinned source browsing, comparisons and SHA-256 evidence references.
- Python AST import-cycle and complexity candidates; conservative potential-unused detection.
- Optional jscpd clone-report scanning and Repowise indexes, using separately installed tools.
- Dependency explorer, source-linked code-health review, Context Builder and Compact/Balanced/Extended evidence exports.
- **Professional findings and triage:** normalized results from optional analyzers; review-first queues, evidence-linked source locations, progress and human decisions. Analyzer findings are not automatically classified as confirmed defects.
- **Commit-scoped coverage:** track observed source areas and missing evidence conservatively; coverage is not a correctness score.
- **Investigation Workspace:** local SQLite history, notes, review progress, human decisions, recorded exports and source-evidence revalidation between commits. It does not automatically equate findings across commits or branches.
- Help, About and in-app explanations.

## Installation — Omarchy, Ubuntu and Windows

Choose your platform guide for **fresh installation, updates, configuration, troubleshooting and rollback**:

- [Omarchy (Linux desktop)](INSTALL_OMARCHY.md) — portable installation and optional launcher; separately installed desktop managers have their own update workflow.
- [Ubuntu / Debian-based Linux](INSTALL_UBUNTU.md) — dependencies and portable startup on a standard desktop.
- [Windows 10/11](WINDOWS_INSTALL.md) — validated per-user PowerShell installer with backup and rollback.

**Portable startup on Linux (also suitable for Omarchy):**

```bash
git clone https://github.com/RafaelAlbaWebify/repo-studio.git
cd repo-studio
python3 -B studio.py --repo /absolute/path/to/your/git-repository --port 8765
```

Alternatively extract the source ZIP and run the command from its extracted application directory. A modern browser opens `http://127.0.0.1:8765`. Python 3.10+ and Git are required; no runtime pip packages or paid AI APIs are needed. The inspected repository must already be a local Git repository with a commit. The app reads committed HEAD, not uncommitted changes.

**Existing managed Omarchy installation:** use its **own** release-aware manager and compatible signed-off ZIP; do not replace application files by hand or run the updater intended for another installation. The manager used on the project owner's machine is a separate local component and is **not** bundled as a general-purpose installer. See the Omarchy guide.

**Windows:** install using `install_windows.ps1`; do not use the Linux commands. See the Windows guide for paths and rollback.

## Use the Workspace

1. Run Python analysis and select a detected finding.
2. Set review progress, a separate human conclusion and notes, then save.
3. Use the Context Builder to choose the evidence to export. Review downloaded content before sharing it externally.
4. Search/filter the history to resume work. Historical records remain tied to their original commit; evidence-file changes prompt revalidation, not an automatic new conclusion.

`jscpd` and Repowise are optional and absent unless available/configured. A missing analyzer is **not** a zero-finding result.

## Tests

```sh
python3 -B -m unittest discover -s tests -v
for js in static/*.js; do node --check "$js"; done
python3 -B tests/smoke_workspace_http.py
python3 -B tools/clean_install_smoke.py
```

For real Chromium Workspace E2E, use an isolated Python environment with `playwright` and Chromium installed:

```sh
python3 -B e2e/workspace_acceptance.py --output ./workspace-e2e-results
```

The E2E test generates a disposable Git fixture and its own local SQLite file. `e2e/README.md` documents other browser tests. Avoid committing generated outputs or evidence archives.

## What results mean

A limited internal comparison of initial context inputs exists, but **no measured end-to-end token or productivity saving has been established**. Private case data is excluded from this candidate. The repeatable benchmark protocol is in `benchmark/README.md`.

## Boundaries and security

- Localhost HTTP is not a multi-user authorization boundary; do not expose the service to the public internet.
- Exports can contain committed credentials or private code. Always inspect before uploading or sharing.
- AST and clone detections are candidates, not definitive bugs or safe refactoring instructions.
- Native Windows CI (unit, Chromium and installer smoke) passed for commit `88e4c72`. Independent manual Windows/Linux installation and full-workflow quality-matched benchmarks remain unverified.

See `SECURITY.md`, `THIRD_PARTY.md`, `PUBLICATION_CHECKLIST.md` and `RELEASE_NOTES_099.md`.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Rafael Alba.
