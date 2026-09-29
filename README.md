# ⚡ Ollama CLI Chatbot Client

A production-grade, interactive terminal chatbot client designed to connect seamlessly to a self-hosted **Ollama** LLM instance running on an on-premise Ubuntu VM (`<YOUR_UBUNTU_VM_IP>`).

Built with **Python 3.10+**, **`rich`**, **`prompt_toolkit`**, and **`httpx`**.

---

## 📋 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [System Specifications](#-system-specifications)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [Windows (PowerShell / CMD)](#windows-powershell--cmd)
  - [Linux & macOS](#linux--macos)
- [Configuration (.env)](#-configuration-env)
- [Running the Application](#-running-the-application)
- [Slash Commands & Keybindings](#-slash-commands--keybindings)
- [On-Premise Ubuntu VM Setup & Docker Deployment](#-on-premise-ubuntu-vm-setup--docker-deployment)
- [Development & Testing](#-development--testing)

---

## 🌟 Overview & Architecture

This client is engineered for reliability, responsiveness, and developer ergonomics when interfacing with self-hosted large language models (such as `qwen2.5:14b`) over a local area network or VPN.

```
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│        Local Workstation        │                 │     On-Premise Ubuntu VM        │
│   (Windows / Linux / macOS)     │                 │      (<YOUR_UBUNTU_VM_IP>)      │
│                                 │                 │                                 │
│  ┌───────────────────────────┐  │   HTTP Stream   │  ┌───────────────────────────┐  │
│  │     PromptSession         │  │ ──────────────> │  │   Ollama Container (CPU)  │  │
│  │ (History, Autocomplete)   │  │   /api/chat     │  │   (Listening on 0.0.0.0)  │  │
│  └─────────────┬─────────────┘  │   NDJSON Chunks │  └─────────────┬─────────────┘  │
│                │                │ <────────────── │                │                │
│  ┌─────────────▼─────────────┐  │                 │  ┌─────────────▼─────────────┐  │
│  │     Live Markdown         │  │                 │  │        Active Model       │  │
│  │ (Typewriter, Monokai CSS) │  │                 │  │       (qwen2.5:14b)       │  │
│  └───────────────────────────┘  │                 │  └───────────────────────────┘  │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

---

## ⚙️ System Specifications

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| **Backend Host IP** | `<YOUR_UBUNTU_VM_IP>` | On-premise Ubuntu VM hosting Ollama |
| **Backend API Endpoint**| `http://<YOUR_UBUNTU_VM_IP>:11434` | Ollama HTTP REST API |
| **Active Default Model**| `qwen2.5:14b` | High-capability 14B Qwen2.5 instruction model |
| **Inference Read Timeout**| `120.0s` | Accommodates 14B inference on CPU or modest GPU |
| **Connection Timeout** | `10.0s` | Diagnostic pre-flight check and fail-fast |
| **Supported Client OS** | Windows, Linux, macOS | PowerShell 5.1/7+, CMD, Bash, Zsh |

---

## ✨ Features

1. **Interactive Terminal UI**:
   - **Live Token Streaming**: Smooth typewriter effect via `rich.live.Live` with sub-second token buffering.
   - **Syntax-Highlighted Markdown**: Code snippets, markdown tables, bold/italic, and bullet points styled with the `monokai` syntax theme.
   - **Inference Metrics Footer**: Reports token speed (`⚡ 22.4 tokens/s`), generated tokens count, and total latency after each response.
   - **Cross-Session Input History**: Arrow keys (Up/Down) cycle through previous inputs persisted to `~/.ollama_cli_history`.
   - **Multi-Line Mode**: Toggle via `/multiline` or insert newlines with `Esc+Enter` / `Alt+Enter`.

2. **Session & State Management**:
   - **Multi-Turn Context**: Preserves conversational memory across the active session in local memory.
   - **Dynamic Personas**: Update the system instructions on the fly (`/system <new_prompt>`).
   - **Model Switching**: Inspect and switch between pulled models on the server (`/model`).
   - **Export Capabilities**:
     - Export to GitHub-flavored Markdown document with turn timestamps (`/save`).
     - Export raw conversation JSON structure (`/json`).

3. **Production-Grade Resilience**:
   - **Pre-flight Health Diagnostics**: Automatic check against `http://<YOUR_UBUNTU_VM_IP>:11434/api/tags` on boot.
   - **Intuitive Troubleshooting Card**: Clear instructions on network reachability, `OLLAMA_HOST` binding, and UFW firewall rules if unreachable.
   - **Graceful Cancellation (`Ctrl+C`)**: Pressing `Ctrl+C` during response streaming halts model generation immediately without closing the application or corrupting session history.

---

## 📂 Project Structure

```
llm-api/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI workflow (Python 3.10-3.12)
├── cli_chat/
│   ├── __init__.py           # Package indicator and versioning
│   ├── client.py             # Ollama HTTP streaming client using httpx
│   ├── config.py             # Settings, environment loader, and defaults
│   ├── main.py               # Application entrypoint & prompt_toolkit loop
│   ├── session.py            # Turn management, state tracking & export
│   └── ui.py                 # Rich theme, banners, tables, and renderers
├── deploy/
│   ├── docker-compose.yml    # Optimized Docker Compose for Ubuntu (CPU-Only)
│   └── setup-ollama.sh       # 1-Click setup script for the Ubuntu VM
├── sessions/
│   └── .gitkeep              # Session output folder (Markdown/JSON transcripts)
├── tests/
│   └── test_components.py    # Unit test suite
├── .env.example              # Template environment configuration file
├── .gitignore                # Exclusion list (virtualenvs, cache, chat history)
├── requirements.txt          # Python dependencies
├── run.bat                   # 1-click Windows launcher
├── run.sh                    # 1-click Linux/macOS launcher
└── README.md                 # Complete documentation
```

---

## 📦 Prerequisites

- **Python 3.10, 3.11, or 3.12+**
- Network access to the Ubuntu VM at port `11434` (Direct LAN or VPN)

---

## 🚀 Installation

### Windows (PowerShell / CMD)

1. Clone or navigate to the project directory:
   ```powershell
   git clone https://github.com/curzedb/llm-api.git
   cd llm-api
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If running in standard CMD, use `.\.venv\Scripts\activate.bat`)*

3. Install required packages:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

*(Alternatively, just double-click or run `.\run.bat`, which automatically sets up `.venv` and dependencies.)*

---

### Linux & macOS

1. Navigate to the project directory:
   ```bash
   git clone https://github.com/curzedb/llm-api.git
   cd llm-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Make launcher executable:
   ```bash
   chmod +x run.sh
   ```

---

## 🔧 Configuration (.env)

Customize connection settings without modifying code by copying the provided `.env.example`:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Edit `.env` to point to your Ubuntu VM:

```ini
# Ollama Remote Instance Configuration
OLLAMA_HOST=http://<YOUR_UBUNTU_VM_IP>:11434
OLLAMA_MODEL=qwen2.5:14b

# Request Timeouts (in seconds)
# Default read timeout is 120s to accommodate 14B model CPU inference
OLLAMA_TIMEOUT=120.0
OLLAMA_CONNECT_TIMEOUT=10.0

# Initial System Persona
OLLAMA_SYSTEM_PROMPT=You are an expert, helpful AI assistant. Provide concise, accurate, and well-structured answers with code syntax highlighting where appropriate.

# History and Session Output Directories
OLLAMA_HISTORY_FILE=~/.ollama_cli_history
OLLAMA_SESSIONS_DIR=./sessions
```

---

## 🎮 Running the Application

### 1. Interactive Mode (Default)

Launch the full interactive chat interface:

```powershell
# Using the active virtual environment:
python -m cli_chat.main

# Or using the launcher:
.\run.bat        # Windows
./run.sh         # Linux / macOS
```

### 2. Runtime Parameter Overrides

Pass CLI arguments to override settings on the fly:

```bash
# Connect to a different model or server:
python -m cli_chat.main --host http://<YOUR_UBUNTU_VM_IP>:11434 --model llama3:8b

# Extend timeout for large prompts:
python -m cli_chat.main --timeout 180.0

# Set a custom system prompt:
python -m cli_chat.main --system "You are a senior DevOps engineer reviewing Kubernetes manifests."
```

### 3. Single-Shot Mode (Non-interactive)

Execute a query directly from the shell without entering the REPL loop:

```bash
python -m cli_chat.main -p "Explain how Python asyncio event loops work in 3 bullet points."
```

---

## ⌨️ Slash Commands & Keybindings

Inside the interactive chat interface, use the following commands:

| Command | Description |
| :--- | :--- |
| `/help` or `/?` | Display the interactive command reference table. |
| `/clear` or `/c` | Reset conversational memory while keeping active model and system prompt. |
| `/system [prompt]` | Display or update the active system persona dynamically. |
| `/model [name]` | Switch model, or list all models downloaded on the Ollama host if no name given. |
| `/history` | View a table of turns and user queries submitted in the current session. |
| `/save [filepath]` | Export conversation to a formatted Markdown file in `./sessions/`. |
| `/json [filepath]` | Export conversation state as raw JSON. |
| `/status` | Display connection details, active model, token statistics, and memory turns. |
| `/multiline` | Toggle multi-line input mode (`Esc+Enter` to submit). |
| `/exit` or `/quit` | Gracefully exit the application. |

### Keyboard Shortcuts

- **`Up / Down Arrow`**: Navigate through previous input history (persisted across sessions).
- **`Ctrl + C`**: Interrupt active streaming generation without exiting or crashing.
- **`Ctrl + D`**: Exit application cleanly (EOF).
- **`Tab`**: Auto-complete slash commands.

---

## 🛠️ On-Premise Ubuntu VM Setup & Docker Deployment

To run Ollama on your **Ubuntu VM** in **CPU-Only** mode using Docker:

### 1. Run Ollama via Docker Compose (Recommended)

Copy the `deploy/` directory to your Ubuntu VM and run:

```bash
cd deploy/
docker compose up -d
```

Or run via `docker run` directly:

```bash
docker run -d \
  --name ollama-cpu \
  --restart always \
  -p 11434:11434 \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  -e OLLAMA_KEEP_ALIVE=24h \
  -e OLLAMA_NUM_PARALLEL=1 \
  -v ollama_storage:/root/.ollama \
  ollama/ollama
```

### 2. Pull the 14B Model into the Container

```bash
docker exec -it ollama-cpu ollama pull qwen2.5:14b
```

### 3. Open Firewall Port (UFW)

```bash
sudo ufw allow 11434/tcp
sudo ufw reload
```

### 4. Test Connectivity from Client Workstation

From your Windows workstation (PowerShell):

```powershell
# Test network reachability:
Test-Connection <YOUR_UBUNTU_VM_IP> -Count 2

# Test HTTP API response:
curl http://<YOUR_UBUNTU_VM_IP>:11434/api/tags
```

---

## 🧪 Development & Testing

Run the included automated unit tests:

```bash
# Run tests
python -m unittest discover tests

# Output example:
# .....
# ----------------------------------------------------------------------
# Ran 5 tests in 0.012s
# OK
```

---

## 📄 License

MIT License. Designed and maintained for production-grade self-hosted LLM deployments.
