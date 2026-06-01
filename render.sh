#!/usr/bin/env bash
# exit on error
set -o errexit

# --- 1. Build Frontend ---
echo "Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# --- 2. Build Backend ---
echo "Installing Backend dependencies..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r backend/requirements.txt
else
    python3 -m pip install -r backend/requirements.txt
fi

# --- 3. Prep Data (Build Vector Index) ---
# We run the index builder to ensure the database is ready.
# We set PYTHONPATH to include 'backend' so imports like 'src.rag' work.
echo "Initializing RAG index..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
if [ -d ".venv" ]; then
    python3 database/build_rag_index.py
else
    python3 database/build_rag_index.py
fi

echo "Build complete!"
