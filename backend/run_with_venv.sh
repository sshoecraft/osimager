#!/bin/bash
# Run API server with the correct virtual environment

set -e

# Get the venv directory from OSImager settings
VENV_DIR="$HOME/.venv"
API_VENV="$VENV_DIR/api"

if [ ! -d "$API_VENV" ]; then
    echo "❌ API virtual environment not found at: $API_VENV"
    echo "💡 Run: python3 -m venv $API_VENV && $API_VENV/bin/pip install -r requirements.txt"
    exit 1
fi

echo "🐍 Using virtual environment: $API_VENV"
source "$API_VENV/bin/activate"

# Check if packages are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Installing API dependencies..."
    pip install -r requirements.txt
fi

echo "🚀 Starting OSImager API server..."
python3 run_server.py "$@"
