"""
Session and Conversation State Management.
Handles multi-turn memory, system personas, and Markdown/JSON export.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ChatTurn:
    """Represents a single conversational turn."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ChatSession:
    """Manages the current interactive session state and memory."""

    def __init__(
        self,
        model: str,
        system_prompt: str,
        host: str = "http://10.100.11.38:11434",
        sessions_dir: Optional[Path] = None,
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.host = host
        self.sessions_dir = sessions_dir or Path("./sessions")
        self.created_at = datetime.now()
        self.turns: List[ChatTurn] = []

        # Ensure export directory exists
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    @property
    def turn_count(self) -> int:
        """Total number of user + assistant turns."""
        return len(self.turns)

    @property
    def user_turn_count(self) -> int:
        """Number of user prompts in this session."""
        return sum(1 for t in self.turns if t.role == "user")

    def add_user_message(self, content: str) -> None:
        """Append a user message to conversation history."""
        self.turns.append(ChatTurn(role="user", content=content.strip()))

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant response to conversation history."""
        self.turns.append(ChatTurn(role="assistant", content=content.strip()))

    def remove_last_user_message(self) -> Optional[ChatTurn]:
        """Remove the most recent user turn (e.g. if request failed or was cancelled)."""
        if self.turns and self.turns[-1].role == "user":
            return self.turns.pop()
        return None

    def set_system_prompt(self, new_prompt: str) -> None:
        """Update system persona prompt on the fly."""
        self.system_prompt = new_prompt.strip()

    def set_model(self, new_model: str) -> None:
        """Switch active Ollama model."""
        self.model = new_model.strip()

    def clear(self) -> None:
        """Clear conversation memory while preserving active model and system prompt."""
        self.turns.clear()

    def get_api_messages(self) -> List[Dict[str, str]]:
        """
        Build message payload for Ollama /api/chat.
        Prepends the system prompt if present, followed by all session turns.
        """
        messages: List[Dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for turn in self.turns:
            messages.append({"role": turn.role, "content": turn.content})

        return messages

    def get_history_summary(self) -> List[Dict[str, Any]]:
        """Return formatted summary of past turns for UI history view."""
        summary = []
        user_idx = 0
        for turn in self.turns:
            if turn.role == "user":
                user_idx += 1
                snippet = turn.content.replace("\n", " ")
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                summary.append(
                    {
                        "turn": user_idx,
                        "role": "User",
                        "preview": snippet,
                        "time": turn.timestamp.strftime("%H:%M:%S"),
                        "full_length": len(turn.content),
                    }
                )
        return summary

    def export_markdown(self, filepath: Optional[str] = None) -> Path:
        """
        Export current chat transcript to a nicely formatted Markdown document.

        Args:
            filepath: Optional custom file path. If omitted, generates a timestamped file
                      in the sessions directory.

        Returns:
            Resolved Path of the saved Markdown file.
        """
        if filepath:
            out_path = Path(filepath).resolve()
        else:
            safe_model = self.model.replace(":", "-").replace("/", "-")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{safe_model}_{timestamp}.md"
            out_path = (self.sessions_dir / filename).resolve()

        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            "# 🤖 Ollama Chat Transcript",
            "",
            "| Metadata | Value |",
            "| :--- | :--- |",
            f"| **Host** | `{self.host}` |",
            f"| **Model** | `{self.model}` |",
            f"| **Started At** | {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| **Exported At** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| **Total Turns** | {len(self.turns)} |",
            "",
            "## 🎭 System Prompt",
            f"> {self.system_prompt or '*(Default)*'}",
            "",
            "---",
            "",
            "## 💬 Conversation History",
            "",
        ]

        turn_counter = 1
        for turn in self.turns:
            time_str = turn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if turn.role == "user":
                lines.extend(
                    [
                        f"### 👤 User (Query #{turn_counter})",
                        f"*{time_str}*",
                        "",
                        turn.content,
                        "",
                    ]
                )
                turn_counter += 1
            else:
                lines.extend(
                    [
                        f"### 🤖 Assistant (`{self.model}`)",
                        f"*{time_str}*",
                        "",
                        turn.content,
                        "",
                        "---",
                        "",
                    ]
                )

        content = "\n".join(lines)
        out_path.write_text(content, encoding="utf-8")
        return out_path

    def export_json(self, filepath: Optional[str] = None) -> Path:
        """Export session state as raw JSON for programmatic reuse."""
        if filepath:
            out_path = Path(filepath).resolve()
        else:
            safe_model = self.model.replace(":", "-").replace("/", "-")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{safe_model}_{timestamp}.json"
            out_path = (self.sessions_dir / filename).resolve()

        out_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "host": self.host,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "exported_at": datetime.now().isoformat(),
            "system_prompt": self.system_prompt,
            "turns": [t.to_dict() for t in self.turns],
        }

        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path
