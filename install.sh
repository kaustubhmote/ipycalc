#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
    echo "IPyCalc development requires uv: https://docs.astral.sh/uv/" >&2
    exit 1
fi

uv sync --group dev
echo "Development environment ready. Run: uv run ipycalc --check"
