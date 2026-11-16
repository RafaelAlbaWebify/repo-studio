# Repo Studio — public demo and screenshot guide

This guide is for preparing **public, synthetic-data** images and a short demonstration of the beta. Do **not** use confidential repositories, client names, credentials, proprietary code or private investigation exports.

## Suggested public media

Use a consistent 16:9 browser capture (for example 1600×900) with a clean browser window and readable UI. Use the same synthetic Git fixture for all captures, and verify every visible path, note and report before publishing.

| Frame | View | What to demonstrate | Suggested caption |
| --- | --- | --- | --- |
| 1 | Overview | Repository summary, Python analysis, analyzer availability | *Start with an evidence-first overview of a committed Git snapshot.* |
| 2 | Dependency explorer | Import-cycle graph and source evidence | *Follow static relationships to the source; do not confuse candidates with defects.* |
| 3 | Investigation Workspace | Human-entered progress, decision and notes | *Record what was reviewed and why, locally and per commit.* |
| 4 | Investigation history | Review/export-status filters and source revalidation | *Resume investigations without silently transferring conclusions across commits.* |
| 5 | Professional findings | Imported analyzer report and review queues | *Organize external diagnostics; validate each finding against source context.* |

**Prefer 3 images for the launch:** Overview, Investigation Workspace, and Dependency explorer. Use the history and professional-findings frames in a follow-up post or demo.

## Synthetic fixture

Create a disposable Git repository containing only invented sample files. Example:

```bash
TMP=$(mktemp -d)
git -C "$TMP" init -q
cat > "$TMP/alpha.py" <<'PY'
import beta

def process_item(value):
    return beta.normalize(value)
PY
cat > "$TMP/beta.py" <<'PY'
import alpha

def normalize(value):
    return str(value).strip().lower()
PY
git -C "$TMP" add .
git -C "$TMP" -c user.name=Demo -c user.email=demo@example.invalid commit -qm 'Synthetic demo fixture'
echo "Synthetic repository: $TMP"
```

Open Repo Studio against this repository in a **separate instance/port** if your normal application is running; do not switch or reset a real investigation Workspace to take marketing screenshots. The exact command depends on whether you use a portable checkout or a managed Omarchy installation. A portable checkout can be launched with:

```bash
python3 -B studio.py --repo "$TMP" --port 8767
```

The script above is illustrative and is not a guaranteed screenshot-ready benchmark: some dashboards and professional triage views require additional synthetic reports or analysis and optional tools.

## 45–60-second demo outline

1. **0–10s:** “Investigating legacy code means more than collecting warnings.” Show Overview.
2. **10–23s:** Select an import cycle or code-health candidate and open the relevant committed source.
3. **23–38s:** Show evidence selection in Context Builder; explain missing evidence and explicit export choices.
4. **38–50s:** Save a review decision and demonstrate Investigation history.
5. **50–60s:** Show the GitHub beta download and three installation guides.

Record **only after** completing a manual privacy check. Hide browser extensions, account information, absolute home paths and any repository that was not deliberately created for the demo. Use synthetic data in exported snippets as well.

## Publication checklist

- [ ] Screenshots show **BETA 0.9.10**.
- [ ] No real customer code, Veridra identifiers, usernames, private file paths, tokens or credentials appear.
- [ ] Actual observed UI, not a fabricated product mockup; any illustrative composite is clearly labeled.
- [ ] No promises of automated refactoring, confirmed defects or measured time/token savings.
- [ ] Link points to [v0.9.10 beta](https://github.com/RafaelAlbaWebify/repo-studio/releases/tag/v0.9.10).
- [ ] Alt text briefly describes each image for accessibility.

## Suggested alternative text

- Overview: “Repo Studio Overview showing analysis summary and analyzer availability for a synthetic Git repository.”
- Workspace: “Repo Studio Investigation Workspace showing locally saved review progress, a human decision and export-history filters.”
- Dependency explorer: “Repo Studio dependency explorer showing a static Python import relationship and evidence inspection controls.”
