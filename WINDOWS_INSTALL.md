# Windows installation (candidate — native Windows validation pending)

**Requirements:** Windows 10/11, Python 3.10+ (`py -3` or `python`), Git for Windows, PowerShell 5.1 or newer, and a browser. No admin rights or Python runtime pip packages required.

1. Extract the public source ZIP to a directory outside your Git repositories.
2. In PowerShell run:

```powershell
cd 'C:\path\to\extracted\repo-studio'
.\install_windows.ps1 -Repository 'C:\path\to\your\repository'
```

If script execution is restricted, follow your organization’s PowerShell policy rather than changing system-wide settings.
3. Launch `%LOCALAPPDATA%\Programs\RepoStudio\launch_windows.cmd` and open `http://127.0.0.1:8765`. Press Ctrl+C to stop the server. If port 8765 is occupied, configure `PORT` for the launch session.

**Config:** `%APPDATA%\repo-studio\launch.json` (JSON, `repo` and optional `jscpd_bin`, `repowise_bin`, `jscpd_report`, `repowise_index`). **State:** `%LOCALAPPDATA%\RepoStudio\data`. Neither goes into the examined Git repository. Paths to external tools are not installed automatically.

**Updates:** close Repo Studio, then run `install_windows.ps1` from the newer extracted release. It preserves config and state and retains a previous-release code backup under `%LOCALAPPDATA%\RepoStudio\backup\previous-release`. It refuses to replace an existing rollback backup. To restore the previous code (without removing newer state), run `install_windows.ps1 -Rollback`. No automated database downgrade is asserted.

**Scope of validation:** Python tests and simulated Windows paths can run on Linux; actual process launching, installation, PowerShell scripts and UI must pass the GitHub Actions Windows runner before calling Windows supported. A clean Windows user test remains desirable.

**Native installer QA:** `.github/workflows/ci.yml` runs `python -B tools/windows_installer_smoke.py` on `windows-latest`, covering fresh install, update, backup protection, rollback, user configuration and state retention. Until that workflow runs successfully on Windows, native installer support remains unverified.
