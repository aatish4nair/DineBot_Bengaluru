#!/bin/bash
# Run Streamlit with headless mode to skip the email prompt
cd "$(dirname "$0")"
STREAMLIT_SERVER_HEADLESS=true streamlit run Phase7/app.py
