"""Pytest conftest: add all phase src directories to sys.path for integration tests."""

import sys
from pathlib import Path

# Project root (parent of Integration/)
ROOT = Path(__file__).resolve().parents[2]

for phase in ["Phase1", "Phase2", "Phase3", "Phase4", "Phase5", "Phase6"]:
    src = ROOT / phase / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
