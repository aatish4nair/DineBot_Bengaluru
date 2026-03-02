from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
phase7_dir = ROOT / 'Phase7'
if str(phase7_dir) not in sys.path:
    sys.path.insert(0, str(phase7_dir))

# Importing Phase7/app.py executes the Streamlit UI defined there
# so that 'streamlit run streamlit_app.py' works as the entrypoint.
import app  # noqa: F401

