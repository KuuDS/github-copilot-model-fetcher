#!/bin/bash
# Quick auth script
# Usage: ./auth.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/set_env.sh"
source "$COPILOT_FETCHER_VENV/bin/activate"

exec python -m copilot_fetcher auth
