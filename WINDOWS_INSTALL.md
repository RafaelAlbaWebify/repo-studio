# Windows installation (0.9.10 beta — CI validated)

**Requirements:** Windows 10/11, Python 3.10+ (`py -3` or `python`), Git for Windows, PowerShell 5.1 or newer, and a browser. No admin rights or Python runtime pip packages required.

1. Download the public source ZIP from [GitHub Releases](https://github.com/RafaelAlbaWebify/repo-studio/releases), then extract it outside your Git repositories. Open the extracted directory containing `install_windows.ps1` (it may be called `repo_studio_f1_mvp`). Alternatively use a clean Git checkout.
2. In PowerShell run:

```powershell
cd 'C:\path\to\extracted\repo-studio'
.\install_windows.ps1 -Repository 'C:\path\to\your\repository'
```

If script execution is restricted, follow your organization’s PowerShell policy rather than changing system-wide settings.
3. Launch `%LOCALAPPDATA%\Programs\RepoStudio\launch_windows.cmd` and open `http://127.0.0.1:8765`. Press Ctrl+C to stop the server. If port 8765 is occupied, configure `PORT` for the launch session.

**Config:** `%APPDATA%\repo-studio\launch.json` (JSON, `repo` and optional `jscpd_bin`, `repowise_bin`, `jscpd_report`, `repowise_index`). **State:** `%LOCALAPPDATA%\RepoStudio\data`. Neither goes into the examined Git repository. Paths to external tools are not installed automatically.

**Updates:** close Repo Studio, then run `install_windows.ps1` from the newer extracted release. It preserves config and state and retains a previous-release code backup under `%LOCALAPPDATA%\RepoStudio\backup\previous-release`. It refuses to replace an existing rollback backup. To restore the previous code (without removing newer state), run `install_windows.ps1 -Rollback`. No automated database downgrade is asserted.

**Scope of validation:** The GitHub Actions `unit-windows` job passed on commit `88e4c72` (2026-11-16), covering unit tests, portable installation, HTTP/SQLite smoke, installer backup/rollback and Chromium Workspace acceptance. A clean, independent Windows end-user installation and interactive manual acceptance are still pending.

**Native installer QA:** `.github/workflows/ci.yml` runs `python -B tools/windows_installer_smoke.py` on `windows-latest`, covering fresh install, update, backup protection, rollback, user configuration and state retention. This workflow passed on commit `88e4c72`; that is automated CI evidence, not a substitute for independent end-user installation.


## Troubleshooting, verification and removal

- Check `py -3 --version` (or `python --version`) and `git --version` before installing; use Python 3.10+.
- A PowerShell script execution-policy restriction is not a reason to disable system-wide security settings. Use the process or user policy your organization permits.
- To confirm startup, open `http://127.0.0.1:8765` and use **About** to check the version. If port 8765 is taken, choose a different `PORT` for the launch session.
- A missing jscpd/Repowise capability is expected unless you separately install and configure that tool.
- For rollback, close the application, preserve a copy of `%LOCALAPPDATA%\RepoStudio\data`, then run `install_windows.ps1 -Rollback` from the installer directory. Restoring old code does not guarantee database-schema downgrade compatibility.
- To remove a per-user installation, close the application and remove the installed program directory and shortcuts. Keep `%APPDATA%\repo-studio` and `%LOCALAPPDATA%\RepoStudio\data` if you want to retain your repository configuration and saved investigations.

**Validation limit:** native automated Windows CI passes, but independent user-interface installation testing on another Windows machine is still pending.
