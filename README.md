# ⚡ Ollama CLI Chatbot Client

A production-grade, interactive terminal chatbot client designed to connect seamlessly to a self-hosted **Ollama** LLM instance running on an on-premise Ubuntu VM (`10.100.11.38`).

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
- [On-Premise Ubuntu VM Setup & Troubleshooting](#-on-premise-ubuntu-vm-setup--troubleshooting)
- [Development & Testing](#-development--testing)

---

## 🌟 Overview & Architecture

This client is engineered for reliability, responsiveness, and developer ergonomics when interfacing with self-hosted large language models (such as `qwen2.5:14b`) over a local area network or VPN.

```
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│        Local Workstation        │                 │     On-Premise Ubuntu VM        │
│   (Windows / Linux / macOS)     │                 │        (10.100.11.38)           │
│                                 │                 │                                 │
│  ┌───────────────────────────┐  │   HTTP Stream   │  ┌───────────────────────────┐  │
│  │     PromptSession         │  │ ──────────────> │  │       Ollama Daemon       │  │
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
| **Backend Host IP** | `10.100.11.38` | On-premise Ubuntu VM hosting Ollama |
| **Backend API Endpoint**| `http://10.100.11.38:11434` | Ollama HTTP REST API |
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
   - **Pre-flight Health Diagnostics**: Automatic check against `http://10.100.11.38:11434/api/tags` on boot.
   - **Intuitive Troubleshooting Card**: Clear instructions on network reachability, `OLLAMA_HOST` binding, and UFW firewall rules if unreachable.
   - **Graceful Cancellation (`Ctrl+C`)**: Pressing `Ctrl+C` during response streaming halts model generation immediately without closing the application or corrupting session history.

---

## 📂 Project Structure

```
llm-api/
├── cli_chat/
│   ├── __init__.py           # Package indicator and versioning
│   ├── client.py             # Ollama HTTP streaming client using httpx
│   ├── config.py             # Settings, environment loader, and defaults
│   ├── main.py               # Application entrypoint & prompt_toolkit loop
│   ├── session.py            # Turn management, state tracking & export
│   └── ui.py                 # Rich theme, banners, tables, and renderers
├── tests/
│   └── test_components.py    # Unit test suite
├── .env.example              # Template environment configuration file
├── requirements.txt          # Python dependencies
├── run.bat                   # 1-click Windows launcher
├── run.sh                    # 1-click Linux/macOS launcher
└── README.md                 # Complete documentation
```

---

## 📦 Prerequisites

- **Python 3.10, 3.11, or 3.12+**
- Network access to the Ubuntu VM at `10.100.11.38:11434` (Direct LAN or VPN)

---

## 🚀 Installation

### Windows (PowerShell / CMD)

1. Clone or navigate to the project directory:
   ```powershell
   cd c:\Users\jafar\Documents\App\llm-api
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   py -m venv .venv
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
   cd ~/llm-api
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

You can customize the connection settings without modifying code by creating a `.env` file from the provided `.env.example`:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Edit `.env` to match your environment:

```ini
# Ollama Remote Instance Configuration
OLLAMA_HOST=http://10.100.11.38:11434
OLLAMA_MODEL=qwen2.5:14b

# Request Timeouts (in seconds)
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

You can pass CLI arguments to override settings on the fly:

```bash
# Connect to a different model or server:
python -m cli_chat.main --host http://10.100.11.38:11434 --model llama3:8b

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

## 🛠️ On-Premise Ubuntu VM Setup & Troubleshooting

If the startup health check reports that `http://10.100.11.38:11434` is unreachable, follow these steps on the **Ubuntu VM (`10.100.11.38`)**:

### 1. Enable External Network Access (OLLAMA_HOST)
By default, Ollama binds **strictly to `127.0.0.1` (localhost only)**, refusing connections from other machines on the LAN.

To allow access from your client machine:

```bash
# 1. Edit the systemd service configuration
sudo systemctl edit ollama.service

# 2. In the editor that opens, paste the following lines:
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"

# 3. Save and exit, then reload systemd and restart Ollama:
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 4. Verify that Ollama is now listening on 0.0.0.0:11434:
ss -tulpn | grep 11434
# Expected output: tcp LISTEN 0 ... 0.0.0.0:11434
```

*If running Ollama via Docker on Ubuntu:*
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 -e OLLAMA_HOST=0.0.0.0 --name ollama ollama/ollama
```

---

### 2. Configure Ubuntu Firewall (UFW)
Ensure Ubuntu's firewall allows incoming connections on port `11434`:

```bash
sudo ufw allow 11434/tcp
sudo ufw reload
sudo ufw status
```

---

### 3. Verify Model Availability
Ensure `qwen2.5:14b` has been pulled on the VM:

```bash
# List pulled models:
ollama list

# If qwen2.5:14b is missing, pull it:
ollama pull qwen2.5:14b
```

---

### 4. Test Connectivity from Your Client Machine

From your client workstation (Windows PowerShell or terminal):

```powershell
# Test network ping:
Test-Connection 10.100.11.38 -Count 2

# Test HTTP port response:
curl http://10.100.11.38:11434/api/tags
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
