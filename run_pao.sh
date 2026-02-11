#!/usr/bin/env bash
set -euo pipefail

# Always run from the script's directory
cd "$(dirname "${BASH_SOURCE[0]}")"

# Activate virtual environment
if [ -d ".venv" ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
else
  echo "Virtualenv .venv not found. Create it with:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# Run the PAO agent against the main list
python email-company.py \
  --contacts-csv data/paolist.csv \
  --sent-log pao_sent_log.csv

