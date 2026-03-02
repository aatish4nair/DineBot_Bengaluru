#!/bin/bash
# Start both backend and Streamlit for AI Restaurant Recommender
cd "$(dirname "$0")"

cleanup() {
  echo ""
  echo "Stopping..."
  pkill -f "uvicorn App.backend" 2>/dev/null
  pkill -f "streamlit run Phase7" 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "=== Stopping any existing processes ==="
pkill -f "uvicorn App.backend" 2>/dev/null
pkill -f "streamlit run Phase7" 2>/dev/null
sleep 2

echo ""
echo "=== Starting backend on port 8000 (ManikaSaini/zomato-restaurant-recommendation, 30 places) ==="
# Run 'python scripts/seed_hf_cache.py' once if App/data/restaurants.json is missing
RESTAURANT_LOAD_FROM_CACHE=1 python -m uvicorn App.backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 3

echo ""
echo "=== Starting Streamlit on port 8501 ==="
echo ""
echo "=============================================="
echo "  Backend:  http://127.0.0.1:8000"
echo "  App UI:   http://localhost:8501"
echo "=============================================="
echo ""
echo "Open http://localhost:8501 in your browser."
echo "Turn OFF 'Use demo response' and click 'Get recommendation'."
echo ""
echo "Press Ctrl+C to stop."
echo ""

# Run Streamlit in foreground (blocks until Ctrl+C)
STREAMLIT_SERVER_HEADLESS=true streamlit run Phase7/app.py --server.port 8501
