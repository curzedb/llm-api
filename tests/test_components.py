"""
Unit tests for Ollama CLI Chatbot Client components.
Tests configuration, session history, Markdown export, and client parsing.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from cli_chat.client import (
    ChatChunk,
    InferenceMetrics,
    OllamaClient,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from cli_chat.config import Config
from cli_chat.session import ChatSession


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = Config()
        self.assertEqual(cfg.host, "http://10.100.11.38:11434")
        self.assertEqual(cfg.model, "qwen2.5:14b")
        self.assertEqual(cfg.timeout, 120.0)
        self.assertEqual(cfg.connect_timeout, 10.0)

    def test_normalize_host(self):
        cfg = Config.load(host="10.100.11.38:11434/")
        self.assertEqual(cfg.host, "http://10.100.11.38:11434")

        cfg_https = Config.load(host="https://ollama.internal:11434")
        self.assertEqual(cfg_https.host, "https://ollama.internal:11434")

    def test_overrides(self):
        cfg = Config.load(
            host="http://192.168.1.50:11434",
            model="llama3:8b",
            timeout=60.0,
            system_prompt="Test persona",
        )
        self.assertEqual(cfg.host, "http://192.168.1.50:11434")
        self.assertEqual(cfg.model, "llama3:8b")
        self.assertEqual(cfg.timeout, 60.0)
        self.assertEqual(cfg.system_prompt, "Test persona")


class TestSession(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("./tmp_test_sessions")
        self.session = ChatSession(
            model="qwen2.5:14b",
            system_prompt="You are a helpful assistant.",
            host="http://10.100.11.38:11434",
            sessions_dir=self.tmp_dir,
        )

    def tearDown(self):
        if self.tmp_dir.exists():
            for f in self.tmp_dir.iterdir():
                f.unlink()
            self.tmp_dir.rmdir()

    def test_turn_management(self):
        self.assertEqual(self.session.turn_count, 0)
        self.session.add_user_message("Hello Ollama")
        self.session.add_assistant_message("Hello human")
        self.assertEqual(self.session.turn_count, 2)
        self.assertEqual(self.session.user_turn_count, 1)

        api_msgs = self.session.get_api_messages()
        self.assertEqual(len(api_msgs), 3)  # system + user + assistant
        self.assertEqual(api_msgs[0]["role"], "system")
        self.assertEqual(api_msgs[1]["role"], "user")
        self.assertEqual(api_msgs[2]["role"], "assistant")

    def test_clear_session(self):
        self.session.add_user_message("Test")
        self.session.clear()
        self.assertEqual(self.session.turn_count, 0)
        self.assertEqual(self.session.system_prompt, "You are a helpful assistant.")

    def test_export_markdown(self):
        self.session.add_user_message("Write python code")
        self.session.add_assistant_message("```python\nprint('test')\n```")
        out_file = self.session.export_markdown()
        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("# 🤖 Ollama Chat Transcript", content)
        self.assertIn("qwen2.5:14b", content)
        self.assertIn("Write python code", content)

    def test_export_json(self):
        self.session.add_user_message("Question")
        self.session.add_assistant_message("Answer")
        out_file = self.session.export_json()
        self.assertTrue(out_file.exists())
        data = json.loads(out_file.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "qwen2.5:14b")
        self.assertEqual(len(data["turns"]), 2)


class TestMetrics(unittest.TestCase):
    def test_inference_metrics(self):
        metrics = InferenceMetrics(
            total_duration_ns=5_000_000_000,
            load_duration_ns=100_000_000,
            prompt_eval_count=20,
            prompt_eval_duration_ns=500_000_000,
            eval_count=100,
            eval_duration_ns=4_000_000_000,
        )
        self.assertAlmostEqual(metrics.total_duration_sec, 5.0)
        self.assertAlmostEqual(metrics.eval_duration_sec, 4.0)
        self.assertAlmostEqual(metrics.tokens_per_second, 25.0)


if __name__ == "__main__":
    unittest.main()
