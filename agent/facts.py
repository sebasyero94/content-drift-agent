"""Fact-delta extraction (T14): read a PR diff and return the product facts it changes.

Also hosts the small Anthropic helper (`call_json`) shared by triage.py and scan.py.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("agent.facts")

SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-4-5-20251001"

_client = None


class LLMError(RuntimeError):
    pass


def _get_client():
    global _client
    if _client is None:
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        except ImportError:
            pass
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise LLMError("ANTHROPIC_API_KEY is not set (put it in .env)")
        import anthropic
        _client = anthropic.Anthropic()
    return _client


def call_json(model: str, system: str, user: str, schema: Dict[str, Any],
              validate: Optional[Callable[[Dict[str, Any]], None]] = None,
              max_tokens: int = 4096) -> Dict[str, Any]:
    """Call the model with a forced tool whose input_schema is `schema`; return the validated dict.

    `validate` raises ValueError on a bad payload; we retry once, telling the model what was wrong.
    """
    client = _get_client()
    messages: List[Dict[str, Any]] = [{"role": "user", "content": user}]
    last_err = ""
    for attempt in range(2):
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system + "\n\nAnswer only by calling the `emit` tool exactly once.", messages=messages,
            tools=[{"name": "emit", "description": "Return the structured result.", "input_schema": schema}],
            tool_choice={"type": "auto"},  # forced tool_choice is rejected by claude-sonnet-5-5
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        if block is None:
            last_err = "no tool_use block returned"
            continue
        payload = dict(block.input)
        try:
            if validate:
                validate(payload)
            return payload
        except ValueError as exc:
            last_err = str(exc)
            messages = [{"role": "user", "content": user + "\n\nYour previous answer was invalid: "
                         + last_err + "\nReturn a corrected answer."}]
    raise LLMError("model output failed validation: " + last_err)


# ---------------------------------------------------------------- diff handling

_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def annotate_patch(patch: str) -> Tuple[List[str], Dict[int, str], Dict[int, str]]:
    """Return (display lines, added {new_line: text}, removed {old_line: text}) for a unified diff patch."""
    shown: List[str] = []
    added: Dict[int, str] = {}
    removed: Dict[int, str] = {}
    old_n = new_n = 0
    for raw in (patch or "").splitlines():
        m = _HUNK.match(raw)
        if m:
            old_n, new_n = int(m.group(1)), int(m.group(2))
            shown.append(raw)
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            added[new_n] = raw[1:]
            shown.append("L%d + %s" % (new_n, raw[1:]))
            new_n += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            removed[old_n] = raw[1:]
            shown.append("L%d - %s" % (old_n, raw[1:]))
            old_n += 1
        elif raw.startswith("\\"):
            continue
        else:
            shown.append("L%d   %s" % (new_n, raw[1:] if raw.startswith(" ") else raw))
            old_n += 1
            new_n += 1
    return shown, added, removed


def _norm(s: str) -> str:
    return re.sub(r"[\s,]+", "", s or "").lower()


_SCHEMA = {
    "type": "object",
    "properties": {
        "deltas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity": {"type": "string", "description": "What the fact is about, e.g. 'Mixpanel Free plan'"},
                    "attribute": {"type": "string", "description": "e.g. 'session replays per month'"},
                    "old": {"type": "string", "description": "Old value exactly as written in the removed line, e.g. '10,000' or '10K'"},
                    "new": {"type": "string", "description": "New value as written in the added line"},
                    "unit": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "integer", "description": "The L-number of the added line holding the new value"},
                    "search_terms": {"type": "array", "items": {"type": "string"},
                                     "description": "6-10 short phrases a web page, FAQ, blog post or doc would use to state the OLD value"},
                    "confidence": {"type": "number"},
                },
                "required": ["entity", "attribute", "old", "new", "unit", "file", "line", "search_terms", "confidence"],
            },
        }
    },
    "required": ["deltas"],
}

_SYSTEM = """You extract product-fact changes from a pull request diff for a product marketing team.
A fact delta is a change to a publicly stated product fact: a plan limit, price, quota, retention period, feature availability, supported platform, and so on.
Rules:
- One delta per changed fact. A line holding two facts changed is two deltas.
- Only changes where an old value was replaced by a new value. Brand-new claims with no old value are not deltas.
- Changes that alter no fact (CSS, layout, typos, rewording, comments, copy tweaks that keep every number and claim) produce an empty list. Do not invent facts.
- `old` and `new` must be copied from the diff text, not inferred. Never output a value that is not in the diff.
- search_terms: phrases other pages would use to state the OLD value, mixing number formats ("10,000", "10K", "10k", "10000") with the attribute wording ("session replays", "replays a month", "free replays"). Include the plan or entity in some. Also include number-as-word and paraphrase forms a writer might use instead of the digits ("ten", "a month", "one month", "four weeks", "a thousand") and wordings without the number ("keeps replays for a month"). Each term is short and case-insensitive.
- `line` is the L-number printed next to the added line that contains the new value."""


def _validate(p: Dict[str, Any]) -> None:
    if not isinstance(p.get("deltas"), list):
        raise ValueError("deltas must be a list")
    for d in p["deltas"]:
        for k in ("entity", "attribute", "old", "new", "unit", "file"):
            if not isinstance(d.get(k), str):
                raise ValueError("delta.%s must be a string" % k)
        if not isinstance(d.get("line"), int):
            raise ValueError("delta.line must be an integer")
        if not isinstance(d.get("search_terms"), list) or not all(isinstance(t, str) for t in d["search_terms"]):
            raise ValueError("delta.search_terms must be a list of strings")


def extract_fact_deltas(diff: Dict[str, Any]) -> List[Dict[str, Any]]:
    """PRDiff -> list[FactDelta]. Empty list when the diff changes no product fact."""
    files = diff.get("files") or []
    blocks: List[str] = []
    added_by_file: Dict[str, Dict[int, str]] = {}
    removed_by_file: Dict[str, Dict[int, str]] = {}
    for f in files:
        shown, added, removed = annotate_patch(f.get("patch") or "")
        if not added and not removed:
            continue
        added_by_file[f["path"]] = added
        removed_by_file[f["path"]] = removed
        blocks.append("FILE %s (%s)\n%s" % (f["path"], f.get("status", "modified"), "\n".join(shown)))
    if not blocks:
        return []

    user = "PR title: %s\n\n%s" % (diff.get("title", ""), "\n\n".join(blocks))
    payload = call_json(SONNET, _SYSTEM, user, _SCHEMA, _validate)

    out: List[Dict[str, Any]] = []
    for raw in payload["deltas"]:
        path = raw["file"]
        if path not in added_by_file:
            # model may shorten the path; match by suffix, else fall back to the only changed file
            match = [p for p in added_by_file if p.endswith(path) or path.endswith(p)]
            path = match[0] if match else (list(added_by_file)[0] if len(added_by_file) == 1 else path)
        added = added_by_file.get(path, {})
        removed = removed_by_file.get(path, {})
        old, new = raw["old"].strip(), raw["new"].strip()
        if not old or not new or _norm(old) == _norm(new):
            continue
        # grounding: both values must literally appear in the diff's removed / added lines
        if not any(_norm(old) in _norm(t) for t in removed.values()) or \
           not any(_norm(new) in _norm(t) for t in added.values()):
            log.warning("dropping ungrounded delta %r -> %r (not in diff lines)", old, new)
            continue
        line = raw["line"]
        if line not in added or _norm(new) not in _norm(added[line]):
            hits = [n for n, t in added.items() if _norm(new) in _norm(t)]
            line = hits[0] if hits else (min(added) if added else line)
        terms: List[str] = []
        for t in raw["search_terms"]:
            t = t.strip()
            if t and t.lower() not in [x.lower() for x in terms]:
                terms.append(t)
        if not terms:
            terms = [old]
        conf = raw.get("confidence")
        conf = float(conf) if isinstance(conf, (int, float)) else 0.5
        out.append({
            "id": "d%d" % (len(out) + 1),
            "entity": raw["entity"].strip(),
            "attribute": raw["attribute"].strip(),
            "old": old, "new": new,
            "unit": raw["unit"].strip(),
            "source": {"file": path, "line": int(line)},
            "search_terms": terms,
            "confidence": max(0.0, min(1.0, conf)),
        })
    return out
