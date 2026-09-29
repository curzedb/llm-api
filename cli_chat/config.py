"""
Configuration Module for Ollama CLI Chatbot Client.
Handles environment variables, default settings, and runtime configuration overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Automatically load environment variables from .env file if present
load_dotenv()


def _normalize_host(url: str) -> str:
    """Normalize and validate the Ollama host URL."""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


@dataclass
class Config:
    """Application configuration container."""

    host: str = field(
        default_factory=lambda: _normalize_host(
            os.getenv("OLLAMA_HOST", "http://10.100.11.38:11434")
        )
    )
    model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:14b").strip()
    )
    timeout: float = field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
    )
    connect_timeout: float = field(
        default_factory=lambda: float(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10.0"))
    )
    system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "OLLAMA_SYSTEM_PROMPT",
            "You are an expert, helpful AI assistant. Provide concise, accurate, "
            "and well-structured answers with code syntax highlighting where appropriate.",
        ).strip()
    )
    history_file: Path = field(
        default_factory=lambda: Path(
            os.getenv("OLLAMA_HISTORY_FILE", str(Path.home() / ".ollama_cli_history"))
        ).expanduser()
    )
    sessions_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("OLLAMA_SESSIONS_DIR", "./sessions")
        ).resolve()
    )

    def __post_init__(self) -> None:
        self.host = _normalize_host(self.host)
        # Ensure sessions directory exists
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    @classmethod
    def load(
        cls,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> Config:
        """Create a Config instance with optional runtime parameter overrides."""
        cfg = cls()
        if host:
            cfg.host = _normalize_host(host)
        if model:
            cfg.model = model.strip()
        if timeout is not None:
            cfg.timeout = float(timeout)
        if system_prompt is not None:
            cfg.system_prompt = system_prompt.strip()
        return cfg
