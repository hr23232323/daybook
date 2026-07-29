"""The advisor. A model/provider-agnostic tool-calling loop.

Speaks the OpenAI-compatible API, so LLM_BASE_URL can be OpenRouter (default),
OpenAI, a local Ollama, or your own proxy — no code change, just config.

Privacy: only the user's question and the RESULTS of read-only queries the model
chooses to run are sent to the endpoint. There is no tool that can write data.
"""
import datetime
import json
import time

from openai import OpenAI

from . import config, queries

THINKING_LEVELS = {"auto", "low", "medium", "high"}

# The model can only ever call these read-only functions.
TOOL_FUNCS = {
    "list_accounts": queries.list_accounts,
    "get_transactions": queries.get_transactions,
    "get_summary": queries.get_summary,
    "spending_by_category": queries.spending_by_category,
    "spending_by_month": queries.spending_by_month,
    "top_merchants": queries.top_merchants,
}

_DATE = {"type": "string", "description": "ISO date YYYY-MM-DD (optional)"}

TOOLS = [
    {"type": "function", "function": {
        "name": "list_accounts",
        "description": "List all accounts with balance, type, and transaction count.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_summary",
        "description": "Totals for a period: income, spending, net, count.",
        "parameters": {"type": "object", "properties": {"start": _DATE, "end": _DATE}},
    }},
    {"type": "function", "function": {
        "name": "spending_by_category",
        "description": "Total spending grouped by category, largest first.",
        "parameters": {"type": "object", "properties": {"start": _DATE, "end": _DATE}},
    }},
    {"type": "function", "function": {
        "name": "spending_by_month",
        "description": "Income vs spending per month.",
        "parameters": {"type": "object", "properties": {"start": _DATE, "end": _DATE}},
    }},
    {"type": "function", "function": {
        "name": "top_merchants",
        "description": "Merchants/payees you spent the most at.",
        "parameters": {"type": "object", "properties": {
            "start": _DATE, "end": _DATE,
            "limit": {"type": "integer", "description": "How many (default 10)"}}},
    }},
    {"type": "function", "function": {
        "name": "get_transactions",
        "description": "List individual transactions matching filters, newest first.",
        "parameters": {"type": "object", "properties": {
            "start": _DATE, "end": _DATE,
            "category": {"type": "string"},
            "search": {"type": "string", "description": "Match payee/description text"},
            "min_amount": {"type": "number"}, "max_amount": {"type": "number"},
            "limit": {"type": "integer"}}},
    }},
]


def _system_prompt() -> str:
    today = datetime.date.today().isoformat()
    return (
        f"You are a sharp, candid personal finance advisor. Today is {today}.\n"
        "The user's real transaction data lives in a local database you can query "
        "with the provided read-only tools. ALWAYS call a tool to get real numbers "
        "before making any claim — never invent or estimate figures. Amounts are "
        "signed: positive = money in, negative = money out. Transactions categorized "
        "'Transfers' are internal moves between the user's own accounts (savings "
        "transfers, credit-card payments) — don't count them as spending or income.\n"
        "Be concise and direct. Cite actual dollar figures and dates from the tools. "
        "Proactively point out patterns, wasteful or recurring spending, and things "
        "worth questioning — like a good advisor reviewing someone's statements. "
        "Call independent tools together when useful. Once you have enough evidence, "
        "stop researching and answer the question. If the data can't answer something, "
        "say so plainly."
    )


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    return t.strip()


def complete_json(system: str, user: str, schema: dict, max_tokens: int = 10000) -> dict:
    """Structured output: ask for a JSON schema and return the parsed object.

    Uses the OpenAI-compatible `response_format` when the provider supports it,
    and falls back to plain JSON parsing when it doesn't.
    """
    if not config.llm_configured():
        raise RuntimeError("No LLM key set.")
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    kwargs = dict(
        model=config.LLM_MODEL, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    try:
        resp = client.chat.completions.create(**kwargs, response_format={
            "type": "json_schema",
            "json_schema": {"name": "insights", "strict": True, "schema": schema},
        })
    except Exception:
        resp = client.chat.completions.create(**kwargs)  # provider lacks structured output
    return json.loads(_strip_fences(resp.choices[0].message.content or "{}"))


def complete(system: str, user: str, max_tokens: int = 10000) -> str:
    """One-shot completion (no tools). Used by the coach tier to narrate facts.

    The budget is deliberately large: reasoning models (Gemini, o-series, ...)
    spend most of it on hidden reasoning before writing a word, and a truncated
    read is far worse than a few extra tokens.
    """
    if not config.llm_configured():
        raise RuntimeError("No LLM key set.")
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    resp = client.chat.completions.create(
        model=config.LLM_MODEL, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()


def _reasoning_context(msg) -> dict:
    """Keep provider reasoning state intact across tool-calling turns."""
    details = getattr(msg, "reasoning_details", None)
    if details:
        return {
            "reasoning_details": [
                item.model_dump(exclude_none=True) if hasattr(item, "model_dump") else item
                for item in details
            ]
        }
    reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
    return {"reasoning": reasoning} if reasoning else {}


def chat(message: str, history: list | None = None, thinking: str = "medium",
         max_tool_rounds: int = 10, with_meta: bool = False):
    if not config.llm_configured():
        raise RuntimeError(
            "No LLM key set. Add LLM_API_KEY to your .env (OpenRouter by default) "
            "to use the advisor. Everything else works without it."
        )
    if thinking not in THINKING_LEVELS:
        raise ValueError(f"Unsupported thinking level: {thinking}")

    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    messages = [{"role": "system", "content": _system_prompt()}]
    messages += history or []
    messages.append({"role": "user", "content": message})

    started = time.monotonic()
    tool_rounds = 0
    tool_call_count = 0

    def finish(text: str):
        if not with_meta:
            return text
        return text, {
            "thinking": thinking,
            "tool_rounds": tool_rounds,
            "tool_calls": tool_call_count,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }

    research_instruction = {
        "role": "system",
        "content": (
            "You are in the research phase. Do not answer the user yet. Call every "
            "read-only tool you still need, grouping independent calls in parallel. "
            "If the existing results are sufficient, respond only RESEARCH_COMPLETE."
        ),
    }

    for _ in range(max_tool_rounds):
        research_kwargs = {
            "model": config.LLM_MODEL,
            "messages": [*messages, research_instruction],
            # Tool routing is deliberately cheap; the user's selected effort is
            # reserved for the synthesis where deeper reasoning adds real value.
            "max_completion_tokens": 2500,
            "tools": TOOLS,
            "tool_choice": "auto",
            "parallel_tool_calls": True,
        }
        if thinking != "auto":
            research_kwargs["reasoning_effort"] = "low"
        resp = client.chat.completions.create(**research_kwargs)
        msg = resp.choices[0].message

        assistant = {"role": "assistant", "content": msg.content or ""}
        assistant.update(_reasoning_context(msg))
        if msg.tool_calls:
            assistant["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        messages.append(assistant)

        if not msg.tool_calls:
            break

        tool_rounds += 1
        tool_call_count += len(msg.tool_calls)
        for tc in msg.tool_calls:
            fn = TOOL_FUNCS.get(tc.function.name)
            try:
                args = json.loads(tc.function.arguments or "{}")
                result = fn(**args) if fn else {"error": "unknown tool"}
            except Exception as e:  # surface tool errors to the model, don't crash
                result = {"error": str(e)}
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, default=str)})

    synthesis_messages = [
        *messages,
        {
            "role": "system",
            "content": (
                "Research is complete. Answer the user's original question now using "
                "the tool results above. Do not mention the research process or ask "
                "them to narrow the question unless the available data genuinely "
                "cannot answer it. Use clear Markdown with short sections and lists."
            ),
        },
    ]
    synthesis_kwargs = {
        "model": config.LLM_MODEL,
        "messages": synthesis_messages,
        "max_completion_tokens": 10000,
    }
    if thinking != "auto":
        synthesis_kwargs["reasoning_effort"] = thinking
    final = client.chat.completions.create(**synthesis_kwargs)
    return finish(final.choices[0].message.content or "")
