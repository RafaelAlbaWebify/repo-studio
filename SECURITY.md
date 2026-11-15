# Security and privacy

- Repo Studio is intended for **local-only** use on a trusted machine. Do not forward or expose its HTTP port.
- The backend reads committed files at the selected Git commit, and refuses stale HEAD when detected. Do not assume optional indexes match that commit; verify provenance.
- GET endpoints allow local clients to read the selected repository. The service is **not a multiuser authorization boundary**. No credentials or external HTTP uploads are required.
- Repo Studio does not execute repository Python modules. Optional analyzers are third-party software and should be considered separately.
- AI investigation exports and Playwright screenshots can contain private source, file paths, or credentials. Review them before distribution.
- SHA-256 release manifests detect accidental or malicious ZIP tampering relative to their manifests, but are **not digital publisher signatures**. Do not auto-download or trust unsigned remote releases.
- The Context Builder treats code as untrusted content, preserves missing evidence warnings and never attempts to certify edits as safe.

For security reports, do not publish secrets or exploit details in public issues. The project owner must select a private reporting channel before public launch.
