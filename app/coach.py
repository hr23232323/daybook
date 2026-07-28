"""Tier 2 — the LLM coach.

Tier 1 (discover.py) already computes the obvious findings. This tier hands the
model the *raw material behind them* — every merchant with its counts and date
range, the monthly spend-by-category series, and the biggest transactions — and
asks for 3-5 insights that are genuinely NOT in the findings already shown:
cross-merchant redundancies, timing correlations, concentration, behavioral
tells. Fewer-but-novel beats padding with restatements.

Data note: with a key set, this sends merchant names and transaction samples to
the configured endpoint (the user opted into "anything and everything"). Figures
must be quoted from the facts or summed from them — never invented — so the
guardrail against fabricated numbers holds even though the model now sees data.
"""
import json

from . import analysis, config, db, discover, llm, queries

SYSTEM = (
    "You are a sharp financial analyst who finds non-obvious patterns a person wouldn't spot "
    "themselves. You are reviewing FACTS computed exactly from someone's transactions: the "
    "deterministic findings ALREADY SHOWN to them, plus the raw material behind them — every "
    "merchant with count/total/category/date-range, monthly spend by category, and their biggest "
    "transactions.\n\n"
    "Return 3 to 5 insights that are genuinely NOVEL — NOT already stated in the findings shown. "
    "Return FEWER (even 2) rather than pad with restatements or filler. An empty answer beats a "
    "generic one.\n\n"
    "GREAT insights (be this specific — name merchants, months, amounts):\n"
    "- Redundancy: \"3 food-delivery services (DoorDash, Uber Eats, Grubhub) total $X/mo.\"\n"
    "- Timing/correlation: \"Dining jumped from $X to $Y in March and stayed there.\"\n"
    "- Concentration: \"68% of your shopping is a single merchant, Amazon.\"\n"
    "- Behavioral tells: a merchant that started or stopped; a category that tracks another.\n"
    "- Cross-finding math the findings didn't state.\n\n"
    "BANNED — never do these:\n"
    "- Restating a finding already shown (if a 'subscriptions' finding exists, don't say 'you have "
    "subscriptions').\n"
    "- Generic advice ('consider reducing discretionary spending', 'watch your budget').\n"
    "- Alarmism about normal numbers. Do NOT flag the overall net or margin as concerning — it is "
    "usually an artifact and not actionable.\n"
    "- Vague hedging.\n"
    "Weak examples to avoid: \"Dining and shopping are your top discretionary categories\" "
    "(restates). \"Your margins are thin, keep an eye on it\" (alarmist + generic).\n\n"
    "Rules:\n"
    "- Every figure must be copied verbatim from the facts, or a sum/difference of figures that "
    "appear in the facts. Never estimate or invent a number.\n"
    "- headline: under 60 characters, concrete and specific. detail: one or two plain sentences.\n"
    "- metric: the single most relevant figure, exactly as written (e.g. $756/mo), or an empty "
    "string. Never wrap figures in quotation marks.\n"
    "- kind: 'pattern' (recurring behaviour), 'opportunity' (worth changing), 'watch' (keep an eye "
    "on), 'observation' (neutral context).\n"
    "- Calm and non-judgmental. A trip or a big purchase is not a problem to be fixed."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "detail": {"type": "string"},
                    "metric": {"type": "string"},
                    "kind": {"type": "string",
                             "enum": ["observation", "pattern", "opportunity", "watch"]},
                },
                "required": ["headline", "detail", "metric", "kind"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["insights"],
    "additionalProperties": False,
}

_cache = {}


def _rows(sql, params=()):
    with db.get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _fingerprint():
    r = _rows("SELECT COUNT(*) c, COALESCE(MAX(date),'') m FROM transactions")[0]
    return f"{r['c']}:{r['m']}:{config.LLM_MODEL}"


def facts():
    """Everything the model may reason over. All dollar figures are pre-formatted."""
    s = queries.get_summary()
    merchants = _rows(
        "SELECT payee, category, COUNT(*) n, ROUND(SUM(-amount),2) total, MIN(date) f, MAX(date) l "
        "FROM transactions WHERE amount < 0 AND category != 'Transfers' AND payee != '' "
        "GROUP BY LOWER(payee) HAVING total > 0 ORDER BY total DESC LIMIT 90")
    ot = analysis.category_over_time(top=8)
    big = _rows(
        "SELECT date, payee, category, ROUND(-amount,2) amt FROM transactions "
        "WHERE amount < 0 AND category != 'Transfers' ORDER BY amount ASC LIMIT 30")
    return {
        "totals_all_time": {
            "money_in": f"${s['income']:,.0f}",
            "money_out": f"${abs(s['spending']):,.0f}",
            "net": f"${s['net']:,.0f}",
            "transactions": s["count"],
        },
        "findings_already_shown_do_not_restate": [
            {"headline": d["title"], "detail": d["summary"]} for d in discover.discoveries()],
        "every_merchant": [
            f"{m['payee']} · {m['n']}x · ${m['total']:,.0f} total · {m['category']} · {m['f']}→{m['l']}"
            for m in merchants],
        "monthly_spend_by_category": {
            "months": ot["months"],
            "series": {sr["name"]: [f"${v:,.0f}" for v in sr["data"]] for sr in ot["series"]},
        },
        "biggest_transactions": [
            f"{b['date']} · {b['payee']} · ${b['amt']:,.0f} · {b['category']}" for b in big],
    }


def _clean(insight):
    out = {k: (v.replace('"', "").strip() if isinstance(v, str) else v) for k, v in insight.items()}
    if out.get("kind") not in ("observation", "pattern", "opportunity", "watch"):
        out["kind"] = "observation"
    return out


def read(force: bool = False):
    if not config.llm_configured():
        return {"available": False, "insights": [], "model": None}
    fp = _fingerprint()
    if not force and fp in _cache:
        return {"available": True, "insights": _cache[fp], "model": config.LLM_MODEL}
    try:
        data = llm.complete_json(SYSTEM, json.dumps(facts(), indent=1), SCHEMA)
        insights = [_clean(i) for i in data.get("insights", []) if i.get("headline")][:5]
    except Exception as e:
        return {"available": True, "insights": [], "model": config.LLM_MODEL, "error": str(e)}
    _cache.clear()
    _cache[fp] = insights
    return {"available": True, "insights": insights, "model": config.LLM_MODEL}
