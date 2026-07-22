#!/bin/sh
#
# This script is used to run your program on CodeCrafters
#
# This runs after .codecrafters/compile.sh
#
# Learn more: https://codecrafters.io/program-interface

set -e # Exit on failure

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec uv run --quiet --project "$SCRIPT_DIR" -m app.shell "$@"
