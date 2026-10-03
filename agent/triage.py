"""Triage (T15): does this PR make public content wrong? Grounded in Profound prompt visibility."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.facts import SONNET, call_json

log = logging.getLogger("agent.triage")

# Used only if agent/profound/client.py is not importable yet. Real Profound numbers, copied by hand
# from docs/data-notes.md "T2 results" (fetched live via MCP 2026-10-03, 30-day window). Marked in the output.
_NOTES_FALLBACK = [
    {"id": "8de94090-2f5b-41eb-b256-b652531ec36b", "topic": "Session replay, experiments & feature flags",
     "text": "What are the best free feature flag and experimentation tools for startups?", "mixpanel_visibility": 0.033},
    {"id": "6416931f-6672-482a-a12a-578a7e86cbe1", "topic": "Session replay, experiments & feature flags",
     "text": "What are the best all-in-one tools for analytics, replay, experiments, and flags?", "mixpanel_visibility": 0.533},
    {"id": "65414e9b-6faa-4ae2-aa18-a91908763b97", "topic": "Session replay, experiments & feature flags",
     "text": "What are the best tools that combine product analytics and session replay?", "mixpanel_visibility": 0.433},
    {"id": "02c54a4a-fe21-46e0-9669-89ba97ce1313", "topic": "Session replay, experiments & feature flags",
     "text": "What are the best session replay tools?", "mixpanel_visibility": 0.0},
    {"id": "d2a9a208-1ebb-4131-8b1e-56aa48befffa", "topic": "Session replay, experiments & feature flags",
     "text": "What is session replay and how do product teams use it?", "mixpanel_visibility": 0.21},
]
_FALLBACK_FETCHED = "2026-10-03"

_SYSTEM = """You triage pull requests for a product marketing manager (PMM).
Given the fact deltas extracted from a PR, decide whether the change makes PUBLIC content wrong (FAQ, pricing, docs, blog, third-party pages).
- verdict "flag": a customer-visible fact changed (plan limit, price, retention, availability). Pages stating the old value are now wrong.
- verdict "skip": nothing publicly stated became wrong (internal-only values, no customer-visible claim).
- tier "high": pricing or plan limits, i.e. a number prospects compare across vendors. tier "medium": a feature detail that is customer-visible but not a pricing or plan-limit comparison. Use "skip" only with verdict "skip".
You are also given tracked AI-engine prompts from Profound with Mixpanel's visibility on each. Pick the single prompt closest to the changed facts as `primary_prompt_id`, and up to two more in `related_prompt_ids`.
`match_quality`: "direct" if the prompt is literally about the changed fact, otherwise "topical" (same topic only).
`reasoning`: 1-2 plain sentences on why the verdict and tier, referring to the changed facts. Do not quote visibility numbers; they are added separately."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["flag", "skip"]},
        "tier": {"type": "string", "enum": ["high", "medium", "skip"]},
        "reasoning": {"type": "string"},
        "primary_prompt_id": {"type": "string"},
        "related_prompt_ids": {"type": "array", "items": {"type": "string"}},
        "match_quality": {"type": "string", "enum": ["direct", "topical"]},
        "confidence": {"type": "number"},
    },
    "required": ["verdict", "tier", "reasoning", "primary_prompt_id", "related_prompt_ids", "match_quality", "confidence"],
}


def _get_prompts(deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        from agent.profound.client import get_related_prompts  # type: ignore
    except ImportError:
        log.warning("agent.profound.client missing; using hand-copied T2 numbers from data-notes")
        return {"prompts": list(_NOTES_FALLBACK), "fetched": _FALLBACK_FETCHED,
                "origin": "data-notes.md T2 fallback (agent/profound/client.py not available)"}
    prompts = get_related_prompts(deltas)
    return {"prompts": list(prompts or []), "fetched": _fetched_stamp(prompts), "origin": "agent.profound.client"}


def _fetched_stamp(prompts: Any) -> str:
    for p in prompts or []:
        for k in ("fetched", "fetched_at"):
            if p.get(k):
                return str(p[k])
    return "unknown"


def _pct(v: Any) -> str:
    return ("%.1f" % v).rstrip("0").rstrip(".") if isinstance(v, (int, float)) else "n/a"


def _as_percent(prompts: List[Dict[str, Any]]):
    """Profound visibility is a 0-1 decimal; if the client already hands back percents (any value > 1), keep them."""
    vals = [p.get("mixpanel_visibility") for p in prompts if isinstance(p.get("mixpanel_visibility"), (int, float))]
    scale = 1.0 if vals and max(vals) > 1 else 100.0
    return lambda v: _pct(v * scale) if isinstance(v, (int, float)) else "n/a"


def triage(diff: Dict[str, Any], deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
    pr = str(diff.get("pr", ""))
    if not deltas:
        return {"pr": pr, "verdict": "skip", "tier": "skip",
                "rationale": "No product fact changed in this diff (no old value replaced by a new value), "
                             "so no public content can have become wrong.",
                "delta_ids": [], "confidence": 0.95,
                "evidence": {"topic": "", "prompts": [], "data_source": "none", "fetched": ""}}

    got = _get_prompts(deltas)
    prompts: List[Dict[str, Any]] = got["prompts"]
    by_id = {p["id"]: p for p in prompts}

    lines = ["PR title: %s" % diff.get("title", ""), "", "Fact deltas:"]
    for d in deltas:
        lines.append("- %s: %s / %s: %s -> %s (%s, line %s)" % (d["id"], d["entity"], d["attribute"], d["old"], d["new"],
                                                           d["source"]["file"], d["source"]["line"]))
    lines.append("")
    lines.append("Tracked prompts (id | text | Mixpanel visibility):")
    to_pct = _as_percent(prompts)
    for p in prompts:
        lines.append("- %s | %s | %s%%" % (p["id"], p["text"], to_pct(p.get("mixpanel_visibility"))))
    if not prompts:
        lines.append("(none matched)")

    def validate(r: Dict[str, Any]) -> None:
        if r["verdict"] == "flag" and r["tier"] == "skip":
            raise ValueError("verdict flag needs tier high or medium")
        if r["verdict"] == "skip" and r["tier"] != "skip":
            raise ValueError("verdict skip needs tier skip")
        if prompts and r["primary_prompt_id"] not in by_id:
            raise ValueError("primary_prompt_id must be one of the listed prompt ids")

    r = call_json(SONNET, _SYSTEM, "\n".join(lines), _SCHEMA, validate)

    rationale = r["reasoning"].strip()
    chosen: List[Dict[str, Any]] = []
    if prompts:
        ids = [r["primary_prompt_id"]] + [i for i in r["related_prompt_ids"] if i in by_id and i != r["primary_prompt_id"]]
        chosen = [by_id[i] for i in ids[:3]]
        top = chosen[0]
        rationale += ' Closest tracked prompt: "%s" (Mixpanel visibility %s%%).' % (top["text"], to_pct(top.get("mixpanel_visibility")))
        if r["match_quality"] == "topical":
            rationale += " Matched by topic; no tracked prompt targets this fact directly."
    else:
        rationale += " No tracked Profound prompt matched these facts."

    return {
        "pr": pr, "verdict": r["verdict"], "tier": r["tier"], "rationale": rationale,
        "delta_ids": [d["id"] for d in deltas],
        "confidence": max(0.0, min(1.0, float(r["confidence"]))),
        "evidence": {
            "topic": (chosen[0].get("topic") if chosen else "") or "",
            "prompts": [{"id": p["id"], "text": p["text"], "mixpanel_visibility": p.get("mixpanel_visibility")} for p in chosen],
            "data_source": "cached", "fetched": got["fetched"], "origin": got["origin"],
        },
    }
