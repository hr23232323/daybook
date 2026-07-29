"""Small contract tests for API request models and route wiring."""

import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app import api


class AdvisorApiTests(unittest.TestCase):
    def test_chat_defaults_to_balanced_thinking(self):
        body = api.ChatIn(message="Where did it go?")
        self.assertEqual(body.thinking, "medium")
        self.assertEqual(body.history, [])

    def test_chat_forwards_the_selected_thinking_level(self):
        body = api.ChatIn(message="Where did it go?", thinking="high")

        with patch("app.llm.chat", return_value="Grounded answer.") as advisor:
            result = api.chat(body)

        self.assertEqual(result, {"reply": "Grounded answer."})
        advisor.assert_called_once_with(
            "Where did it go?",
            [],
            thinking="high",
        )

    def test_chat_rejects_an_unknown_thinking_level(self):
        with self.assertRaises(ValidationError):
            api.ChatIn(message="Where did it go?", thinking="maximum")


if __name__ == "__main__":
    unittest.main()
