#!/bin/bash
# Quick list script - Display saved models
# Usage: ./list.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/.venv/bin/activate"

exec python -m copilot_fetcher list
