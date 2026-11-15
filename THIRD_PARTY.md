# External tools and test dependencies

Repo Studio's standard runtime uses the Python standard library and Git. The optional external analyzers **jscpd** and **Repowise** are not distributed in this repository or binary release. Install and license these independently according to their upstream terms.

Chromium and the Python `playwright` package are optional development/test dependencies, not distributed here. The GitHub Actions workflow installs them in a disposable runner. Verify upstream licenses and your distribution obligations before repackaging third-party binaries.
