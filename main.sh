#!/usr/bin/env bash
set -euo pipefail

# Run from the repo root regardless of where this script is invoked from,
# so uv finds pyproject.toml / uv.lock.
cd "$(dirname "$0")"

# uv installs to ~/.local/bin, which isn't on PATH in every shell.
if ! command -v uv >/dev/null 2>&1; then
    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        [ -x "$candidate" ] && { PATH="$(dirname "$candidate"):$PATH"; break; }
    done
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "main.sh: uv not found. Install it, or add its directory to PATH." >&2
    exit 127
fi

exec uv run main.py
