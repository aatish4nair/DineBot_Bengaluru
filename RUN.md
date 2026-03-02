# How to Run the AI Restaurant Recommender

## Quick start (easiest)

From the project root, run:
```bash
./start_app.sh
```
Then open **http://localhost:8501** in your browser. Press Ctrl+C to stop.

---

## Manual start

Run these commands from the **project root** (`Project1-1`).

**Dataset:** By default the backend loads **ManikaSaini/zomato-restaurant-recommendation** from Hugging Face (full dataset). Set `USE_SAMPLE_DATASET_ONLY=1` to use built-in sample data (7 cities) only. First run may take a minute to download the dataset.

**If you get "Address already in use"** — stop the process:
```bash
lsof -i :8000
kill <PID>
```

From a subfolder like `Phase4`, first run: `cd "/Users/aatishnair/Documents/NL Prod Man/My Projects/Project1/Project1-1"`

---

## Option A: Streamlit UI (Python only, no npm)

**1. Start the backend**
```bash
cd "/Users/aatishnair/Documents/NL Prod Man/My Projects/Project1/Project1-1"
uvicorn App.backend.main:app --reload --host 0.0.0.0 --port 8000
```

**2. In a new terminal, start the Streamlit UI**

Streamlit shows an email prompt that blocks startup. Use the headless env var to skip it:

```bash
cd "/Users/aatishnair/Documents/NL Prod Man/My Projects/Project1/Project1-1"
STREAMLIT_SERVER_HEADLESS=true streamlit run Phase7/app.py
```

Or run the script: `./run_streamlit.sh`

Wait until you see: **"You can now view your Streamlit app in your browser"**

**3. Open:** http://localhost:8501

**4. Turn OFF "Use demo response"** and click **Get recommendation** to use the real backend.

---

## Option B: React frontend (requires Node.js/npm)

If you have Node.js installed:

**1. Start the backend** (same as above)

**2. Start the React frontend**
```bash
cd "/Users/aatishnair/Documents/NL Prod Man/My Projects/Project1/Project1-1/App/frontend"
npm install
npm run dev
```

**3. Open in browser:** http://localhost:5173

---

## If you don't have npm

Install Node.js from https://nodejs.org (includes npm), or use **Option A** (Streamlit) which only needs Python.
