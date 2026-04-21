#!/bin/bash
# Universal launcher for GitHub Copilot Model Fetcher
# Usage: ./run.sh <command> [options]
#
# Commands:
#   auth         Authenticate with GitHub OAuth
#   fetch        Fetch and save Copilot models
#   list         List fetched models
#   raw          Show raw JSON data
#   clear        Clear stored authentication and data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment configuration
if ! source "$SCRIPT_DIR/set_env.sh" 2>/dev/null; then
    exit 1
fi

# Activate virtual environment and run
source "$COPILOT_FETCHER_VENV/bin/activate"
exec python -m copilot_fetcher "$@"
