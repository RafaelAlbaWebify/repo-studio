# Linux clean-install verification — 0.9.8 beta

Repo Studio has a portable entrypoint (`python3 -B studio.py --repo /absolute/path --port 8765`) requiring Python 3.10+ and Git. It must not be exposed beyond localhost.

The automated test `python3 -B tools/clean_install_smoke.py` **does not install globally**. It copies the public code into a temporary location, creates an empty HOME/XDG profile, an isolated committed Git fixture, a fresh `launch.json`, and launches the **real `launcher.py`**. It checks that localhost UI/API work, optional analyzers are correctly marked unavailable, state data stays under HOME and outside the fixture, a restart works, and the Git fixture remains unchanged. It removes its temporary files on completion.

This tests portable launch and basic persistence setup, **not** a desktop integration, distro package, or a full machine-level clean installation. The user's previous Omarchy 0.9.2 installation remains the verified baseline; upgrade to 0.9.8 still requires acceptance. Playwright browser E2E and optional external analyzer integration are separate gates.

Manual independent install checklist:

1. On a fresh Linux user/profile with Git and Python 3.10+, extract the public source archive.
2. Create a small **non-private** Git repository with at least one commit.
3. Run `python3 -B studio.py --repo /absolute/path/to/fixture --port 8765`.
4. Open `http://127.0.0.1:8765`, verify Python analysis and saving a Workspace note.
5. Stop/restart and verify the note remains; confirm the fixture `git status --porcelain` stays empty.
6. Validate that missing jscpd/Repowise is displayed as unavailable, not as zero findings.
7. Record OS/Python/Git versions and result before clearing this gate.

No GitHub release should be described as independently clean-install verified before this manual gate is completed.

Windows: `python -B tools/clean_install_smoke.py` is configured for APPDATA/LOCALAPPDATA when run on Windows. CI must confirm it on windows-latest.
