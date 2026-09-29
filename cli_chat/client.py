"""
Ollama HTTP Client with Streaming Support.
Provides robust HTTP communication with on-premise Ollama instances using httpx.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

import httpx

from cli_chat.config import Config


@dataclass
class InferenceMetrics:
    """Inference execution metrics returned by Ollama on stream completion."""

    total_duration_ns: int = 0
    load_duration_ns: int = 0
    prompt_eval_count: int = 0
    prompt_eval_duration_ns: int = 0
    eval_count: int = 0
    eval_duration_ns: int = 0

    @property
    def total_duration_sec(self) -> float:
        return self.total_duration_ns / 1e9

    @property
    def eval_duration_sec(self) -> float:
        return self.eval_duration_ns / 1e9

    @property
    def tokens_per_second(self) -> float:
        if self.eval_duration_sec > 0:
            return self.eval_count / self.eval_duration_sec
        return 0.0


@dataclass
class ChatChunk:
    """A streaming text chunk and optional terminal metrics."""

    content: str
    is_done: bool = False
    metrics: Optional[InferenceMetrics] = None


@dataclass
class HealthCheckResult:
    """Health check diagnosis result."""

    is_healthy: bool
    status_code: Optional[int] = None
    available_models: List[str] = None  # type: ignore[assignment]
    error_message: Optional[str] = None
    troubleshooting_advice: Optional[str] = None

    def __post_init__(self) -> None:
        if self.available_models is None:
            self.available_models = []


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""


class OllamaConnectionError(OllamaClientError):
    """Raised when the Ollama host is unreachable."""


class OllamaTimeoutError(OllamaClientError):
    """Raised when an API request times out."""


class OllamaModelNotFoundError(OllamaClientError):
    """Raised when the requested model does not exist on the server."""


class OllamaClient:
    """Synchronous HTTP client for Ollama LLM API with streaming support."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._timeout = httpx.Timeout(
            read=self.config.timeout,
            connect=self.config.connect_timeout,
            write=30.0,
            pool=10.0,
        )

    def _get_client(self) -> httpx.Client:
        """Create a fresh configured httpx.Client."""
        return httpx.Client(
            base_url=self.config.host,
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )

    def check_health(self) -> HealthCheckResult:
        """
        Ping the remote Ollama server via GET /api/tags.
        Verifies connectivity and collects list of pulled models.
        """
        tags_url = f"{self.config.host}/api/tags"
        try:
            with self._get_client() as client:
                response = client.get("/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return HealthCheckResult(
                        is_healthy=True,
                        status_code=200,
                        available_models=models,
                    )

                return HealthCheckResult(
                    is_healthy=False,
                    status_code=response.status_code,
                    error_message=f"HTTP {response.status_code}: {response.text}",
                    troubleshooting_advice=(
                        f"Ollama server responded with unexpected status {response.status_code} "
                        f"at {tags_url}."
                    ),
                )

        except httpx.ConnectTimeout:
            return HealthCheckResult(
                is_healthy=False,
                error_message=f"Connection timed out while connecting to {self.config.host}",
                troubleshooting_advice=(
                    "1. Verify that your machine is connected to the same LAN or active VPN as the Ubuntu VM (10.100.11.38).\n"
                    "2. Ensure the Ubuntu VM is running and port 11434 is open.\n"
                    "3. Check if Ubuntu UFW or external firewall is blocking incoming traffic on port 11434.\n"
                    "4. On the Ubuntu host, verify Ollama is bound to 0.0.0.0 (OLLAMA_HOST=0.0.0.0:11434)."
                ),
            )

        except (httpx.ConnectError, httpx.NetworkError) as e:
            return HealthCheckResult(
                is_healthy=False,
                error_message=f"Cannot reach Ollama host at {self.config.host} ({type(e).__name__})",
                troubleshooting_advice=(
                    "1. Network Unreachable: Check if 10.100.11.38 responds to ping (`ping 10.100.11.38`).\n"
                    "2. Service Status: On the Ubuntu VM, run: `systemctl status ollama` or check `docker ps`.\n"
                    "3. Binding Configuration: By default, Ollama binds only to 127.0.0.1. Ensure systemd service has:\n"
                    "   Environment=\"OLLAMA_HOST=0.0.0.0:11434\"\n"
                    "4. Ubuntu Firewall: Run `sudo ufw allow 11434/tcp` on the server."
                ),
            )

        except httpx.TimeoutException:
            return HealthCheckResult(
                is_healthy=False,
                error_message=f"Request timed out while contacting {self.config.host}",
                troubleshooting_advice=(
                    "Server received request but did not reply within connect timeout. "
                    "The VM might be under heavy load or routing packet loss."
                ),
            )

        except Exception as e:
            return HealthCheckResult(
                is_healthy=False,
                error_message=f"Unexpected error contacting {self.config.host}: {str(e)}",
                troubleshooting_advice="Check client network configuration and DNS/proxy settings.",
            )

    def list_models(self) -> List[Dict[str, Any]]:
        """Fetch list of all models registered on the remote Ollama server."""
        try:
            with self._get_client() as client:
                response = client.get("/api/tags")
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except httpx.RequestError as exc:
            raise OllamaConnectionError(f"Failed to fetch models from {self.config.host}: {exc}") from exc

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[ChatChunk, None, None]:
        """
        Stream chat completions from Ollama /api/chat.

        Args:
            messages: List of chat messages [{"role": "user"|"assistant"|"system", "content": "..."}]
            model: Model name override (defaults to config.model)
            temperature: Sampling temperature

        Yields:
            ChatChunk containing incremental text pieces and final inference metrics.

        Raises:
            OllamaModelNotFoundError: If requested model is not found on server
            OllamaTimeoutError: If response read times out
            OllamaConnectionError: If network error occurs during streaming
        """
        active_model = model or self.config.model
        payload = {
            "model": active_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            with self._get_client() as client:
                with client.stream("POST", "/api/chat", json=payload) as response:
                    if response.status_code == 404:
                        error_body = response.read().decode("utf-8", errors="ignore")
                        raise OllamaModelNotFoundError(
                            f"Model '{active_model}' was not found on remote Ollama server ({self.config.host}). "
                            f"Server message: {error_body}\n"
                            f"Tip: Pull it on the Ubuntu VM via: ollama pull {active_model}"
                        )

                    response.raise_for_status()

                    for line in response.iter_lines():
                        if not line:
                            continue

                        try:
                            chunk_data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Extract message content if present
                        msg = chunk_data.get("message", {})
                        delta = msg.get("content", "")
                        is_done = chunk_data.get("done", False)

                        metrics: Optional[InferenceMetrics] = None
                        if is_done:
                            metrics = InferenceMetrics(
                                total_duration_ns=chunk_data.get("total_duration", 0),
                                load_duration_ns=chunk_data.get("load_duration", 0),
                                prompt_eval_count=chunk_data.get("prompt_eval_count", 0),
                                prompt_eval_duration_ns=chunk_data.get("prompt_eval_duration", 0),
                                eval_count=chunk_data.get("eval_count", 0),
                                eval_duration_ns=chunk_data.get("eval_duration", 0),
                            )

                        yield ChatChunk(content=delta, is_done=is_done, metrics=metrics)

        except httpx.ReadTimeout as exc:
            raise OllamaTimeoutError(
                f"Inference timed out after {self.config.timeout:.0f}s. "
                "The 14B model may need more CPU/GPU compute time. "
                "You can increase timeout via OLLAMA_TIMEOUT env var or --timeout flag."
            ) from exc

        except httpx.ConnectTimeout as exc:
            raise OllamaConnectionError(
                f"Connection to Ollama host at {self.config.host} timed out."
            ) from exc

        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise OllamaConnectionError(
                f"Network connection interrupted while streaming from {self.config.host}: {exc}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise OllamaClientError(
                f"Ollama server returned error status {exc.response.status_code}: {exc.response.text}"
            ) from exc
