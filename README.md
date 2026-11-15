# Repo Studio

**Evidence-first investigation of existing Git repositories** · Linux + Windows beta candidate 0.9.8 · Local-first · Read-only source inspection · Human-controlled

Repo Studio is a local web application for examining committed code in legacy Git repositories and assembling traceable evidence for optional AI-assisted analysis. It does **not** upload repository content to AI services, automatically modify inspected source, or assert that a static finding is a defect.

## Features

- Git commit-pinned source browsing, comparisons and SHA-256 evidence references.
- Python AST import-cycle and complexity candidates; conservative potential-unused detection.
- Optional jscpd clone-report scanning and Repowise indexes, using separately installed tools.
- Dependency explorer, source-linked code-health review, Context Builder and Compact/Balanced/Extended evidence exports.
- **Investigation Workspace:** local SQLite history, notes, review progress, human decisions, recorded exports and source-evidence revalidation between commits. It does not automatically equate findings across commits or branches.
- Help, About and in-app explanations.

## Local launch (portable/development)

Requirements: Linux or Windows 10/11, Python 3.10+, Git and a modern browser. No additional Python **runtime** packages required. From this directory:

```sh
python3 -B studio.py --repo /absolute/path/to/git-repository --port 8765
```

Open `http://127.0.0.1:8765` (localhost only). The repository's committed files are inspected; its working tree is not edited. The application's local database and exports should be kept outside the inspected repository. Consult `python3 studio.py --help` for optional analyzer and data paths.

**Windows installation/update:** see [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) for a per-user PowerShell installer, configuration and rollback. Windows support remains a candidate until native Windows CI and browser acceptance pass.

**Omarchy installation/update:** use the separately verified controlled installer; do not overwrite an active installation manually. The clean-profile portable smoke test passes in an isolated Linux container, but a separate machine/profile acceptance and the in-place Omarchy 0.9.8 upgrade remain publication gates.

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
- Native Windows CI and actual Windows installer/browser acceptance, an independent Linux install, and full-workflow quality-matched benchmarks remain unverified.

See `SECURITY.md`, `THIRD_PARTY.md`, `PUBLICATION_CHECKLIST.md` and `RELEASE_NOTES_098.md`.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Rafael Alba.
