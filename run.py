#!/usr/bin/env python3
"""
Run the agent from the project root. Ensures the local `src` package is used.

Always use this to run so your edits are picked up:
  python run.py
  python run.py samples/sample_architecture.md

If you run main.py directly or use "arch-review-agent", Python may use an
installed copy of the package instead of your local source.
"""
import sys
from pathlib import Path

# Must run from project root (where run.py lives). Prepend src first so
# "arch_review_agent" loads from ./src/arch_review_agent, not site-packages.
_root = Path(__file__).resolve().parent
_src = _root / "src"
sys.path.insert(0, str(_src))

import arch_review_agent

# Show which code is running (so you can confirm it's from this repo)
_resolved = Path(arch_review_agent.__file__).resolve()
print(f"[run.py] Loading from: {_resolved}", flush=True)
if "site-packages" in str(_resolved):
    print("[run.py] WARNING: Loaded from site-packages, not src. Use 'python run.py' from project root.", flush=True)

from arch_review_agent.main import main

if __name__ == "__main__":
    main()
