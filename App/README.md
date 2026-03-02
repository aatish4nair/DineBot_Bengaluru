# AI Restaurant Recommender

## Quick start

### 1. Backend (sample dataset only, no Hugging Face)

```bash
cd App
USE_SAMPLE_DATASET_ONLY=1 uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. React frontend

```bash
cd App/frontend
npm install
npm run dev
```

Open http://localhost:5173

### 3. Alternative: Streamlit UI (Phase 7)

```bash
cd Phase7
streamlit run app.py
```

## API

- `GET /health` — Health check
- `POST /recommend` — Get recommendation (JSON body: place, price_range, min_rating, cuisines)

## Environment

- `USE_SAMPLE_DATASET_ONLY=1` — Use built-in sample data only (recommended for testing)
- `MAX_DATASET_RECORDS` — Limit HF dataset size (default 20000)
- `GROQ_API_KEY` — Optional, for AI-generated rationale
