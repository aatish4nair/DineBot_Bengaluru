# Phase 7 - UI Layer (Streamlit)

This phase provides a local UI for manual testing:
- Preference form
- Loading, error, and empty states
- Calls a backend recommendation API (configurable)
- Displays a top recommendation + rationale + alternatives

## Run locally

From the repo root:

```bash
cd Phase7
streamlit run app.py
```

The UI will be available at:
- `http://localhost:8501`

## Backend API configuration

By default the UI calls:
- Base URL: `http://127.0.0.1:8000`
- Path: `/recommend`

You can override via environment variables (or `Phase7/.env`):
- `RECOMMENDER_API_BASE_URL`
- `RECOMMENDER_API_RECOMMEND_PATH`
- `RECOMMENDER_API_TIMEOUT_S`

## Demo mode

If you do not have a backend running yet, enable **Use demo response** in the UI
to validate the UI end-to-end without an API server.

