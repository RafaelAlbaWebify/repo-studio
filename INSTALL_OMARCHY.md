# Install Repo Studio on Omarchy (Linux)

**Repo Studio 0.9.9 beta** runs locally using Python 3.10+, Git and a browser. No paid AI provider, administrator account or runtime pip packages are required.

## 1. First-time portable installation

Install Python and Git using your normal Omarchy/Arch package-management workflow if they are not already installed. Verify with `python3 --version` and `git --version`. On an Arch-based system, the package names are `python` and `git`; installing/updating OS packages may require administrator privileges.

```bash
git clone https://github.com/RafaelAlbaWebify/repo-studio.git ~/repo-studio
cd ~/repo-studio
python3 -B studio.py --repo "$HOME/path/to/your/existing-git-repository" --port 8765
```

**Replace the sample repository path** with the real absolute path to a local Git repository. Alternatively extract the ZIP from [GitHub Releases](https://github.com/RafaelAlbaWebify/repo-studio/releases), enter its application directory and run the Python command. The ZIP folder may be named `repo_studio_f1_mvp`.

Open `http://127.0.0.1:8765`. Stop the foreground process with Ctrl+C. If port 8765 is busy, use `--port 8767` and open that port instead. The service binds to localhost only.

## 2. Optional Omarchy Apps entry

The portable installation does **not** automatically register an Omarchy launcher. For the simplest desktop setup, create your own `~/.local/share/applications/repo-studio.desktop` pointing to a small launcher script that invokes `studio.py` with your repository path. Do not replace an existing desktop entry or manager-managed installation. Test the portable command first.

## 3. Existing managed Omarchy installation — update

Some earlier Repo Studio Omarchy installations use a **separately installed** `~/.local/share/repo-studio-manager/manager.py` and desktop updater. That manager is not included in the public portable source package.

If your installation has this manager, **do not follow the fresh-installation commands to overwrite its application directory**. The verified owner setup uses a ZIP with `release.json`, per-file SHA-256 hashes, and the `repo_studio_f1_mvp/` archive prefix. The manager stages and validates the release before stopping the known local server, preserves the previous application directory, and rolls back code if startup fails. Use the manager's documented `update <release-zip>` operation only with a compatible package and a copy of user data. Its `latest` action selects a newer compatible ZIP from Downloads and asks for confirmation; it does not download releases from GitHub automatically.

The owner's 0.9.8 → 0.9.9 update, isolated upgrade/rollback and live application startup have been observed. This is **not** a claim that every Omarchy machine has that manager.

## 4. Configuration and persistent data

The portable `launcher.py` uses `~/.config/repo-studio/launch.json` for repository/tool paths when launched via `launch_omarchy.sh`. Running `studio.py --repo ...` directly uses the explicit CLI arguments. Workspace notes, decisions and history are persisted under the user's Repo Studio state directory (by default `~/.local/state/repo-studio`); inspect `/api/status` for the actual active data path. Back up this state, the launcher configuration and any custom tool paths before a managed upgrade or removal. Do not copy them into a public ZIP.

## 5. Troubleshooting / rollback / removal

- **No repository configured:** provide an absolute path to an existing Git checkout containing a commit.
- **Port occupied:** choose another port for a portable launch; the managed Omarchy launcher expects 8765.
- **Missing jscpd or Repowise:** these analyzers are optional and must be installed/configured separately. Missing analysis is not zero findings.
- **Wrong version after update:** check the actual served UI and the installed `static/index.html`, not just a source checkout.
- **Rollback:** for a managed installation, follow your manager's backup path and rollback procedure; keep your SQLite state backed up separately. Portable installations can restore a previous extracted source directory. Database schema downgrades are **not** guaranteed.
- **Removal:** delete only your chosen portable application directory and personal desktop entry, if any. Keep `~/.local/state/repo-studio` unless you intentionally want to erase the investigation history.

This is beta software. Automated Linux checks and one observed Omarchy installation do not establish independent acceptance across all machines.
