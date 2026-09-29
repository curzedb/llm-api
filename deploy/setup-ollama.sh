#!/usr/bin/env bash
# ==============================================================================
# 1-Click Ollama CPU-Only Docker Setup for Ubuntu Server VM (10.100.11.38)
# ==============================================================================

set -e

echo "=== [1/4] Verifying Docker Installation ==="
if ! command -v docker &> /dev/null; then
    echo "[INFO] Docker not found. Installing Docker CE..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "[INFO] Docker installed successfully."
fi

echo "=== [2/4] Starting Ollama CPU Container via Docker Compose ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

echo "=== [3/4] Pulling qwen2.5:14b Model (approx. 9 GB) ==="
echo "Note: This might take a few minutes depending on network bandwidth."
docker exec -it ollama-cpu ollama pull qwen2.5:14b

echo "=== [4/4] Configuring UFW Firewall ==="
if command -v ufw &> /dev/null; then
    sudo ufw allow 11434/tcp
    sudo ufw reload
    echo "[INFO] Firewall rule added: port 11434/tcp allowed."
fi

echo "=================================================================="
echo "🎉 SUCCESS: Ollama CPU server is ready at http://10.100.11.38:11434"
echo "Model 'qwen2.5:14b' is loaded and ready for client queries!"
echo "=================================================================="
