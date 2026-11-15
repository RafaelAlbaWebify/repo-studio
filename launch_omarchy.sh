#!/usr/bin/env bash
# Repo Studio launcher: versioned code, user-specific configuration outside the release.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python3}" -B "$HERE/launcher.py" "$@"
