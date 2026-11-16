# Install Repo Studio on Ubuntu (and related Debian-based desktops)

**Repo Studio 0.9.9 beta** is a localhost-only app using Python 3.10+, Git and a modern browser. The core application requires no Python runtime pip packages or AI account.

## 1. Prerequisites

```bash
sudo apt update
sudo apt install python3 git
python3 --version
git --version
```

Make sure `python3` is **3.10 or newer**. Ubuntu versions with older Python need a supported Python upgrade; do not replace the system Python blindly.

## 2. Download and start

```bash
git clone https://github.com/RafaelAlbaWebify/repo-studio.git ~/repo-studio
cd ~/repo-studio
python3 -B studio.py --repo "$HOME/path/to/your/existing-git-repository" --port 8765
```

Replace the example repository path with the **absolute path** to an existing local Git repository containing at least one commit. Alternatively download the source ZIP from [GitHub Releases](https://github.com/RafaelAlbaWebify/repo-studio/releases), extract it and run the same `studio.py` command from the extracted application directory (often named `repo_studio_f1_mvp`).

Open `http://127.0.0.1:8765` in the browser; use Ctrl+C to stop. If the port is occupied, pass `--port 8767` and open that address. Do not bind the service to the public network.

## 3. Normal use and updates

Run the same command to reopen the app. Optional tools `jscpd` and Repowise are not installed automatically. They require separate installations and paths; missing analyzers are reported as unavailable.

To update a portable installation, **first back up** the application directory, any launcher configuration (`~/.config/repo-studio/launch.json`), and Workspace state (typically `~/.local/state/repo-studio`; confirm using `/api/status`). Stop the server, obtain the newer public source tree, and restart. Do not overwrite a separately manager-controlled Omarchy installation this way. For rollback, restore the earlier source tree and retained state backup; database downgrades are not guaranteed.

## 4. Troubleshooting and removal

- `Repository not configured`: specify a real absolute Git repository path; uncommitted files are not inspected.
- `Address already in use`: choose another local port or stop the existing instance.
- Empty investigation history: check the active data directory returned by `/api/status`, not the source checkout.
- Missing jscpd / Repowise: optional tool, not an installation failure.
- Remove the portable application directory when finished. Keep the separate state directory if you want to preserve existing investigations.

The Linux clean-profile installation and browser acceptance were exercised in automated CI. Installation on an independent Ubuntu end-user machine remains unverified.
