#!/usr/bin/env bash
# ==============================================================================
# Ollama CLI Chatbot Client - Linux / macOS Launcher Script
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python3 availability
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found in PATH. Please install Python 3.10+."
    exit 1
fi

# Setup Virtual Environment if missing
if [ ! -f ".venv/bin/activate" ]; then
    echo "[INFO] Creating virtual environment (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "[INFO] Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Launch CLI Chatbot with interactive model selection
python3 -m cli_chat.main -s "$@"
