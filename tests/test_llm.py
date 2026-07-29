"""Focused tests for the advisor's multi-round tool loop."""

import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import llm


def _tool_call(call_id="call_1"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name="get_summary", arguments="{}"),
    )


def _response(content="", tool_calls=None, reasoning_details=None):
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls or [],
        reasoning_details=reasoning_details,
        reasoning=None,
        reasoning_content=None,
    )
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeCompletions:
    def __init__(self, responder):
        self.responder = responder
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return self.responder(kwargs, len(self.calls))


class _FakeClient:
    def __init__(self, responder):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responder))


class AdvisorLoopTests(unittest.TestCase):
    def _run(self, responder, **kwargs):
        client = _FakeClient(responder)
        with (
            patch.object(llm, "OpenAI", return_value=client),
            patch.object(llm.config, "LLM_API_KEY", "test-key"),
            patch.dict(llm.TOOL_FUNCS, {"get_summary": lambda: {"count": 3}}, clear=True),
        ):
            answer = llm.chat("Where is my money going?", **kwargs)
        return answer, client.chat.completions.calls

    def test_forces_a_synthesis_after_the_tool_round_budget(self):
        def responder(request, call_number):
            if "tools" in request:
                return _response(tool_calls=[_tool_call(f"call_{call_number}")])
            return _response(content="Here is the answer from the gathered records.")

        answer, calls = self._run(
            responder,
            thinking="high",
            max_tool_rounds=3,
        )

        self.assertEqual(answer, "Here is the answer from the gathered records.")
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(call["reasoning_effort"] == "low" for call in calls[:3]))
        self.assertEqual(calls[-1]["reasoning_effort"], "high")
        self.assertTrue(all("tools" in call for call in calls[:3]))
        self.assertTrue(all(call["parallel_tool_calls"] for call in calls[:3]))
        self.assertTrue(all(call["max_completion_tokens"] == 2500 for call in calls[:3]))
        self.assertEqual(calls[-1]["max_completion_tokens"], 10000)
        self.assertNotIn("tools", calls[-1])
        self.assertIn("Research is complete", calls[-1]["messages"][-1]["content"])

    def test_preserves_reasoning_details_between_tool_calls(self):
        details = [{"type": "reasoning.encrypted", "data": "opaque-state"}]

        def responder(request, call_number):
            if call_number == 1:
                return _response(
                    tool_calls=[_tool_call()],
                    reasoning_details=details,
                )
            return _response(content="A grounded answer.")

        answer, calls = self._run(responder, thinking="medium")

        self.assertEqual(answer, "A grounded answer.")
        assistant_turn = next(
            message for message in calls[1]["messages"]
            if message["role"] == "assistant"
        )
        self.assertEqual(assistant_turn["reasoning_details"], details)

    def test_auto_uses_the_provider_default(self):
        answer, calls = self._run(
            lambda _request, _number: _response(content="Done."),
            thinking="auto",
        )

        self.assertEqual(answer, "Done.")
        self.assertNotIn("reasoning_effort", calls[0])
        self.assertNotIn("reasoning_effort", calls[-1])

    def test_returns_non_sensitive_timing_and_tool_metadata(self):
        def responder(request, call_number):
            if call_number == 1:
                return _response(tool_calls=[_tool_call()])
            return _response(content="Grounded answer.")

        result, _calls = self._run(
            responder,
            thinking="medium",
            with_meta=True,
        )
        answer, meta = result

        self.assertEqual(answer, "Grounded answer.")
        self.assertEqual(meta["thinking"], "medium")
        self.assertEqual(meta["tool_rounds"], 1)
        self.assertEqual(meta["tool_calls"], 1)
        self.assertGreaterEqual(meta["elapsed_ms"], 0)

    def test_rejects_an_unknown_thinking_level(self):
        with (
            patch.object(llm.config, "LLM_API_KEY", "test-key"),
            self.assertRaisesRegex(ValueError, "Unsupported thinking level"),
        ):
            llm.chat("Hello", thinking="maximum")


if __name__ == "__main__":
    unittest.main()
