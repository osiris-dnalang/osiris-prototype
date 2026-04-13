OSIRIS — Quickstart (Concise)

Overview
OSIRIS is an experimental, modular AI execution framework for local, inspectable agent workflows. This quickstart shows a deterministic offline demo and how to invoke the prototype CLI.

Requirements
- Python 3.9+ (recommended)
- Optional: virtualenv (recommended for isolation)

Offline demo (fast, recommended)
1. Make demo executable (if needed):
   chmod +x ./osiris-demo
2. Run the offline demo (no network required):
   ./osiris-demo

Explore the CLI
- Show commands and help:
   ./osiris --help
- Run a built-in campaign (will use local mock/QVM if IBM token is not set):
   ./osiris run --campaign week1_foundation

Optional: create a virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r osiris-cli/requirements.txt

Notes
- The demo is deterministic and offline to avoid external dependencies and security concerns.
- The lightweight root launcher (`./osiris`) imports the `osiris-cli` package located at `./osiris-cli`.
- For pitch materials and the implementation plan, see the session plan file:
  /home/enki/.copilot/session-state/6770598d-a18b-4ea5-9b7c-9d6b3f660e00/plan.md

Contact
Repo owner: devin@agiledefensesystems.com
