## 0.9.8 (beta candidate, 2026-11-14)
- Investigation Workspace integrated with source-linked finding navigation, persistent reviews, recorded exports, historical filters and conservative commit-specific revalidation.
- Tested with 76 Python unit cases and 8 Chromium/Playwright Workspace checks on Omarchy (user-observed); final packaging/installation pending.
- No cross-commit decision inheritance, remote AI calls or automatic code edits.

## 0.9.5 (candidate) — persistent investigation history

- Bounded, filtered, read-only cross-commit review ledger; conservative identity.
- HTTP integration smoke and 67 Python tests; Omarchy validation pending.

## 0.9.3 — evidence transparency and context benchmark
- Explicit missing target source-line ranges for truncated evidence.
- Human-controlled retrieval of missing committed lines in bounded 120-line requests.
- Reproducible initial-context comparison with full relevant Git files.
- No inferred end-to-end token savings; optional tokenizer-specific counts.

## 0.9.2 (candidate)
- Added vector RS monogram, favicon, PNG Linux icon and horizontal wordmark.
- Expanded E2E export assertions to Compact/Balanced/Extended, provenance, omitted fragments and invalidation.
- No changes to analyzed repositories or automatic AI calls.

## 0.9.1 — UX & documentation candidate
- Clarified the two analysis actions.
- Added honest running indicators to Python and jscpd scans.
- Added delayed on-hover/focus contextual help, indexed in-app Help, About, and synthetic screenshots.
- No new analyzer or remote behavior.

## 0.9.0 — Human-controlled investigation beta candidate
- Context Builder: select source anchors, specify approximate token budget, mark omissions, copy/download Markdown.
- Commit-pinned evidence, exact source SHA-256, stale selection invalidation; no AI calls.
- Matched benchmark protocol with empty 10-case measurement template and quality gate.
- Publication/CI preparation. No measured token savings, native Windows verification or public release yet.

## 0.8.4 — Dependency explorer and evidence coverage
- Dedicated investigation workspace; compact Overview unchanged.
- Read-only SVG cycle graph showing only detected Python AST edges, with exact-source drilldowns.
- On-demand evidence coverage from the existing commit-pinned /api/evidence endpoint.
- Compact, Balanced, Extended source-anchor and cycle-edge coverage with missing-evidence warnings.
- No inferred safety verdicts or complete-dependency claims.
- New E2E case and visual regression checks.

## 0.8.3 — Responsive dashboard layout
- Desktop-first density and layout improvements at 1366px, 1440px, and larger displays.
- Removed redundant hero copy; preserved all indicators and drill-down actions.
- Eliminated unnecessary fixed panel heights, reduced spacing, and improved empty states.
- Secondary repository settings remain in collapsed details.
- No analyzer or source mutation changes.

## 0.8.2
- Compact Overview layout: core dashboard fits more comfortably above the fold.
- Moved repository switching and verbose tool details into a collapsible details panel.
- Added last-analysis and toolchain summary indicators to the command bar.
- Preserved dashboard drilldowns, evidence export and read-only guarantees.

# Changelog

## 0.8.0 — stabilization candidate (2026-11-13)
- Auto-reconnect included in versioned JS; Manager must not modify release files.
- Local Host allowlist for HTTP requests and stricter POST Origin matching.
- Added security tests for cross-origin and DNS-rebinding requests.
- No automated refactoring or external telemetry.

## 0.7.0
- Evidence anchored to detected imports, cloning spans and complexity findings.

### 0.8 RC2 — evidence coverage and pinned source reads
- Evidence exports include explicit per-anchor coverage, import-edge completeness and source SHA-256 hashes.
- Git file and analysis reads use the selected commit rather than moving HEAD refs.
- Adds three evidence coverage regression tests; no new runtime dependencies.

### 0.8 RC3 — conservative potentially unused code review
- Detect undecorated, private top-level Python functions with no name reference in fully parsed committed sources.
- Suppress detection on partial scans or common dynamic introspection; external consumers remain unknown.
- Add Code health filter and evidence export for candidates; never suggest automatic deletion.

### 0.8 RC4 — code-health triage UX
- Search by path, module or symbol, category filter and reproducible sort order.
- Progressive rendering in batches of 60 instead of hiding everything after 120 findings.
- Show explicit coverage summary in evidence preview.
- Invalidate stale code-health results on repository switch in the UI.
- Add regression checks for triage control wiring.

### 0.8 validation build
- Repository file listing and source viewer pinned to selected commit, with explicit stale HEAD rejection.
- Repowise context rejects changed HEAD; does not claim index freshness when selecting a repository.
- Added regression coverage for commit drift.

## 0.8 Dashboard validation candidate (2026-11-13)
- Added a measured-only repository intelligence dashboard: AST findings distribution, source-file hotspots, analyzer coverage and drill-down actions.
- Unavailable jscpd results now say **Not analyzed** rather than showing misleading zero matches.
- Unused-code candidates say **N/A / Not eligible** when the static scan cannot support a conclusion.
- Added dashboard E2E coverage; no new JS dependencies, external services or repository mutations.
- Dashboard displays the selected committed snapshot only; no longitudinal history or severity score is implied.

## Dashboard Sprint 1 candidate (2026-11-13)

- Interactive measured-only donut for AST finding categories; jscpd matches explicitly separated.
- File complexity hotspots with source drilldowns and a deterministic investigation queue.
- More compact wide-screen layout inspired by the approved concept without invented metrics or severities.
- Refreshed duplicate KPI/queue on audit completion and reset on repository changes.
- Added regression contracts and extended Playwright dashboard assertions.
