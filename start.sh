#!/usr/bin/env bash

# 1. Set the Python Path so the system can find your backend modules
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# 2. Build the frontend (so changes actually show up!)
echo "📦 Building frontend..."
cd frontend && npm run build && cd ..

# 3. Start the FastAPI server
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🚀 Starting MyAlly (Serving Frontend + Backend)..."
python3 -m uvicorn src.app.chat_api:app --host 0.0.0.0 --port ${PORT:-8000}
