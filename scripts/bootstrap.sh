#!/bin/bash
# First-run bootstrap for a fresh WSL machine that only has WSL + Python 3.12.
#
# Installs Docker Engine (if missing), creates the venv, brings up the data/model
# services, builds the app images, ingests the docs, and runs the smoke test.
#
# Usage: bash scripts/bootstrap.sh
set -euo pipefail
cd "$(dirname "$0")/.."

log() { printf '\n==> %s\n' "$1"; }

# --- 1. Docker Engine + Compose plugin ---------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    log "Docker not found; installing Docker Engine (requires sudo)"
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "Added $USER to the docker group. Log out/in (or run 'newgrp docker') if the next step fails with a permission error."
fi

if ! docker info >/dev/null 2>&1; then
    log "Starting the Docker daemon"
    sudo service docker start
    sleep 2
fi

if ! docker compose version >/dev/null 2>&1; then
    log "Docker Compose plugin not found; installing"
    sudo apt-get update -y
    sudo apt-get install -y docker-compose-plugin
fi

# --- 1b. NVIDIA Container Toolkit (GPU access for Ollama) ---------------------
# ollama's docker-compose.yml reservation only works once Docker has the
# nvidia runtime; skipped entirely if there is no NVIDIA GPU on this machine.
if command -v nvidia-smi >/dev/null 2>&1; then
    if ! docker info 2>/dev/null | grep -qi 'Runtimes:.*nvidia'; then
        log "NVIDIA GPU detected; installing the NVIDIA Container Toolkit"
        distribution=$(. /etc/os-release; echo "$ID$VERSION_ID")
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
            | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
        curl -fsSL "https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list" \
            | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' \
            | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
        sudo apt-get update -y
        sudo apt-get install -y nvidia-container-toolkit
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo service docker restart
    fi
else
    log "No NVIDIA GPU detected (nvidia-smi missing); Ollama will run on CPU"
fi

# --- 2. Python 3.12 venv ------------------------------------------------------
if [ ! -x .venv/bin/python ]; then
    log "Creating Python 3.12 virtualenv"
    if ! python3.12 -m venv .venv 2>/tmp/venv_err; then
        grep -qi ensurepip /tmp/venv_err && sudo apt-get install -y python3.12-venv
        python3.12 -m venv .venv
    fi
fi
log "Installing project (dev + models extras)"
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e ".[dev,models]" -q

# --- 3. Environment file -------------------------------------------------------
if [ ! -f .env ]; then
    log "Creating .env from .env.example"
    cp .env.example .env
fi

# --- 4. Data + model services ---------------------------------------------------
log "Starting postgres, redis"
docker compose up -d postgres redis

log "Starting Ollama and pulling local models (qwen3-embedding, qwen3)"
make models   # GPU-aware: applies docker-compose.gpu.yml when nvidia-smi is present

# --- 5. Build and start the app images -----------------------------------------
log "Building orchestrator + ingestion images"
make build

log "Starting the orchestrator"
docker compose up -d orchestrator

# --- 6. Ingest the docs corpus --------------------------------------------------
log "Running ingestion (docs -> embeddings -> pgvector)"
make ingest

# --- 7. Smoke test ---------------------------------------------------------------
log "Running the end-to-end smoke test"
make smoke

log "Bootstrap complete."
