"""Scan (T16) and edits + ranking (T17): find passages that state the old fact, classify, propose edits.

Pipeline per (page, delta):
  1. deterministic candidate filter (old/new value variants + attribute keywords)
  2. Haiku: drop candidates that are not about this entity/attribute at all (conservative: keep if unsure)
  3. Sonnet: classify stale / current / ambiguous / unrelated with a reason, seeing the page's other relevant passages
  4. Sonnet: minimal before/after edit for stale passages, checked deterministically for grounding
`LAST_STATS` holds counts from the most recent scan() for the report.
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from agent.facts import HAIKU, SONNET, call_json

log = logging.getLogger("agent.scan")

WEIGHTS = {"stale": 1.0, "ambiguous": 0.5, "current": 0.0}
MAX_PASSAGE = 1200
LAST_STATS: Dict[str, Any] = {}

_STOP = {"per", "month", "monthly", "year", "with", "from", "that", "this", "each", "plan", "free", "number", "total"}


# ---------------------------------------------------------------- matching helpers

def _parse_number(value: str) -> Optional[int]:
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?\b", value)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    if m.group(2):
        n *= 1000 if m.group(2).lower() == "k" else 1000000
    return int(n)


def _value_regex(value: str) -> "re.Pattern[str]":
    n = _parse_number(value)
    forms = {re.escape(value.strip())}
    if n is not None:
        forms |= {re.escape("{:,}".format(n)), str(n)}
        if n >= 1000 and n % 1000 == 0:
            forms.add("%dk" % (n // 1000))
        if n >= 1000000 and n % 1000000 == 0:
            forms.add("%dm" % (n // 1000000))
    alt = "|".join(sorted(forms, key=len, reverse=True))
    return re.compile(r"(?<![\d,.])(?:%s)(?![\d,]|\.\d|\w)" % alt, re.I)


def _keywords(delta: Dict[str, Any]) -> List[str]:
    words = re.findall(r"[a-z]{4,}", (delta["attribute"] + " " + delta.get("unit", "")).lower())
    return sorted({w[:5] for w in words if w not in _STOP})


def _has_keyword(text: str, kws: List[str]) -> bool:
    low = text.lower()
    return any(k in low for k in kws)


def _is_candidate(passage: str, delta: Dict[str, Any], old_re, new_re, kws) -> bool:
    low = passage.lower()
    if any(t.lower() in low for t in delta["search_terms"]):
        return True
    for rx, val in ((old_re, delta["old"]), (new_re, delta["new"])):
        if rx.search(passage):
            n = _parse_number(val)
            if n is None or n >= 1000 or _has_keyword(passage, kws):
                return True
    # a different number for the same attribute (e.g. "up to 25 flags"): judged too, so conflicts surface as ambiguous
    return _has_keyword(passage, kws) and bool(re.search(r"\d", passage))


def _clean_passages(page: Dict[str, Any]) -> List[str]:
    """Passages in page order, deduped. Fills page['_ctx'] {passage: heading context} from data's passage_context."""
    seen, out = set(), []
    ctxs = page.get("passage_context") or []
    ctx_map: Dict[str, str] = {}
    for i, p in enumerate(page.get("passages") or []):
        p = re.sub(r"\s+", " ", p or "").strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p[:MAX_PASSAGE])
            if i < len(ctxs) and ctxs[i]:
                ctx_map[p[:MAX_PASSAGE]] = re.sub(r"\s+", " ", str(ctxs[i])).strip()[:200]
    page["_ctx"] = ctx_map
    return out


# ---------------------------------------------------------------- LLM steps

def _filter_relevant(delta: Dict[str, Any], cands: List[str]) -> List[str]:
    """Haiku: keep candidates that talk about the delta's entity+attribute (any value). Keep when unsure."""
    schema = {"type": "object", "properties": {"keep": {"type": "array", "items": {"type": "integer"}}}, "required": ["keep"]}
    system = ("You filter text passages. Given a product fact (entity + attribute), return the indexes of passages that make any "
              "claim about that attribute for that product or plan, whatever the value. Drop a passage only when it is clearly about "
              "something else (e.g. '10 minutes to set up' for a replays-per-month fact). If unsure, keep it.")
    user = "Fact: %s — %s (old value %s, new value %s)\n\nPassages:\n%s" % (
        delta["entity"], delta["attribute"], delta["old"], delta["new"],
        "\n".join("[%d] %s" % (i, c) for i, c in enumerate(cands)))

    def validate(p):
        if not all(isinstance(i, int) and 0 <= i < len(cands) for i in p["keep"]):
            raise ValueError("keep must be valid passage indexes")

    keep = set(call_json(HAIKU, system, user, schema, validate, max_tokens=512)["keep"])
    return [c for i, c in enumerate(cands) if i in keep]


_CLASSIFY_SYSTEM = """You audit web content for staleness after a product fact changed.
The fact changed from OLD to NEW (effective now). For each numbered passage decide:
- stale: the passage states the OLD value as true now, for the same entity/plan/attribute as the fact. Fixing it means changing the number.
- current: it already states the NEW value, OR it states the same number but for a different plan, tier, metric or context than the fact (for example Growth instead of Free, a different feature, a different unit), OR it is dated/historical and says so.
- ambiguous: you cannot tell which fact the passage means, or the page states conflicting values for this attribute elsewhere (see the page's other passages), or it is unclear whether the number is the included amount or a purchasable maximum. A page that states the NEW value in one place and the OLD value in another is half-updated, not ambiguous: the old-value passage is stale and the new-value passage is current. Conflict with a third value that matches neither OLD nor NEW (or with a different date/version of the same plan) is what makes a page ambiguous. Never resolve an ambiguity by guessing: use ambiguous and explain exactly what is unclear.
- unrelated: not about this attribute at all.
The same number in a different context is NOT stale. Judge only from the text shown, including the section heading when given (it can name the plan). If neither the passage nor its section names the plan or context and it cannot be established, use ambiguous. `reason` is one or two sentences, specific, quoting the deciding words. For ambiguous, say why it is ambiguous."""

_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {"index": {"type": "integer"},
                       "verdict": {"type": "string", "enum": ["stale", "current", "ambiguous", "unrelated"]},
                       "reason": {"type": "string"}},
        "required": ["index", "verdict", "reason"]}}},
    "required": ["results"],
}


def _classify(page: Dict[str, Any], delta: Dict[str, Any], cands: List[str], context: List[str]) -> List[Dict[str, Any]]:
    user = "Fact: %s — %s\nOLD: %s %s\nNEW: %s %s\n\nPage: %s (%s, %s)\nTitle: %s\n\nPassages to judge:\n%s" % (
        delta["entity"], delta["attribute"], delta["old"], delta.get("unit", ""), delta["new"], delta.get("unit", ""),
        page["url"], page.get("owner", ""), "cached" if page.get("cached") else "live", page.get("title", ""),
        "\n".join("[%d] %s%s" % (i, c, ("   (section: %s)" % page["_ctx"][c]) if page.get("_ctx", {}).get(c) else "")
                  for i, c in enumerate(cands)))
    if context:
        user += "\n\nOther passages from the same page that touch this attribute (context only, not to be judged):\n" + \
                "\n".join("- " + c[:400] for c in context)

    def validate(p):
        got = {r["index"] for r in p["results"]}
        if got != set(range(len(cands))):
            raise ValueError("need exactly one result for each index 0..%d" % (len(cands) - 1))
        for r in p["results"]:
            if not r["reason"].strip():
                raise ValueError("every result needs a reason")

    return call_json(SONNET, _CLASSIFY_SYSTEM, user, _CLASSIFY_SCHEMA, validate)["results"]


_EDIT_SYSTEM = """You write a minimal correction for one stale passage. A product fact changed from OLD to NEW.
Return `before`: the shortest exact verbatim span of the passage that contains the old value (copy it character for character).
Return `after`: that same span with only the old value replaced by the new value, keeping the passage's own style (if it writes '10K', write '20K').
Hard rules: use only the NEW value and wording already in the passage. Add no claim, number, date or qualifier that is not in the passage or the NEW value. Do not reword anything else."""

_EDIT_SCHEMA = {"type": "object", "properties": {"before": {"type": "string"}, "after": {"type": "string"}},
                "required": ["before", "after"]}

_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?[kKmM]?")


def _nums(s: str) -> set:
    return {m.group(0).lower().replace(",", "") for m in _NUM.finditer(s)}


def _edit_grounded(before: str, after: str, passage: str, delta: Dict[str, Any]) -> Optional[str]:
    """Return None if the edit is acceptable, else the reason it is not."""
    if before not in passage:
        return "before is not a verbatim span of the passage"
    if before == after:
        return "after equals before"
    if not _value_regex(delta["old"]).search(before):
        return "before does not contain the old value"
    if _value_regex(delta["old"]).search(after):
        return "after still contains the old value"
    new_nums = _nums(delta["new"])
    n = _parse_number(delta["new"])
    if n is not None:
        new_nums |= {str(n), "%dk" % (n // 1000) if n % 1000 == 0 else str(n)}
    extra = _nums(after) - _nums(before) - new_nums
    if extra:
        return "after introduces numbers not in the passage or the diff: %s" % sorted(extra)
    return None


def _surface_new(old_surface: str, delta: Dict[str, Any]) -> str:
    """Express the new value in the same style as the old surface form found in the text."""
    n = _parse_number(delta["new"])
    if n is None:
        return delta["new"]
    m = re.fullmatch(r"(\d+)([kK])", old_surface)
    if m and n % 1000 == 0:
        return "%d%s" % (n // 1000, m.group(2))
    if "," in old_surface:
        return "{:,}".format(n)
    return str(n) if re.fullmatch(r"\d+", old_surface) else delta["new"]


def _fallback_edit(passage: str, delta: Dict[str, Any]) -> Optional[Dict[str, str]]:
    m = _value_regex(delta["old"]).search(passage)
    if not m:
        return None
    s, e = max(0, m.start() - 20), min(len(passage), m.end() + 30)
    before = passage[s:e]
    after = before.replace(m.group(0), _surface_new(m.group(0), delta), 1)
    return {"before": before, "after": after}


def _propose_edit(passage: str, delta: Dict[str, Any]) -> Optional[Dict[str, str]]:
    user = "OLD: %s\nNEW: %s\nFact: %s — %s\n\nPassage:\n%s" % (delta["old"], delta["new"], delta["entity"], delta["attribute"], passage)
    problem = "none"
    for _ in range(2):
        try:
            r = call_json(SONNET, _EDIT_SYSTEM, user + ("\n\nPrevious attempt rejected: " + problem if problem != "none" else ""),
                          _EDIT_SCHEMA, max_tokens=1024)
        except Exception as exc:  # noqa: BLE001 - fall back to the deterministic edit
            problem = str(exc)
            continue
        bad = _edit_grounded(r["before"], r["after"], passage, delta)
        if bad is None:
            return {"before": r["before"], "after": r["after"]}
        problem = bad
    log.warning("edit rejected (%s); using deterministic replacement", problem)
    fb = _fallback_edit(passage, delta)
    if fb and _edit_grounded(fb["before"], fb["after"], passage, delta) is None:
        return fb
    return None


# ---------------------------------------------------------------- scan

def _scan_job(page: Dict[str, Any], delta: Dict[str, Any], cands: List[str], context: List[str]) -> Tuple[List[Dict[str, Any]], int]:
    kept = _filter_relevant(delta, cands)
    dropped = len(cands) - len(kept)
    if not kept:
        return [], dropped
    findings = []
    for res in _classify(page, delta, kept, context):
        if res["verdict"] == "unrelated":
            dropped += 1
            continue
        passage = kept[res["index"]]
        edit = _propose_edit(passage, delta) if res["verdict"] == "stale" else None
        reason = res["reason"].strip()
        if res["verdict"] == "stale" and edit is None:
            reason += " (Could not produce a grounded automatic edit; fix by hand.)"
        findings.append({"page_url": page["url"], "delta_id": delta["id"], "passage": passage,
                         "verdict": res["verdict"], "reason": reason, "proposed_edit": edit})
    return findings, dropped


def scan(deltas: List[Dict[str, Any]], corpus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """list[FactDelta], list[Page] -> list[Finding] sorted by priority. Current passages are included (priority 0)."""
    jobs = []
    total_passages = 0
    for page in corpus:
        passages = _clean_passages(page)
        total_passages += len(passages)
        for d in deltas:
            old_re, new_re, kws = _value_regex(d["old"]), _value_regex(d["new"]), _keywords(d)
            cands = [p for p in passages if _is_candidate(p, d, old_re, new_re, kws)]
            if not cands:
                continue
            context = [p for p in passages if p not in cands and _has_keyword(p, kws)][:6]
            jobs.append((page, d, cands, context))

    findings: List[Dict[str, Any]] = []
    filtered_out = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fs, dropped in pool.map(lambda j: _scan_job(*j), jobs):
            findings.extend(fs)
            filtered_out += dropped

    _rank(findings, corpus)
    LAST_STATS.clear()
    LAST_STATS.update({
        "pages_scanned": len(corpus), "passages_checked": total_passages,
        "candidate_passages": sum(len(j[2]) for j in jobs), "filtered_out": filtered_out,
        "stale": sum(f["verdict"] == "stale" for f in findings),
        "ambiguous": sum(f["verdict"] == "ambiguous" for f in findings),
        "current": sum(f["verdict"] == "current" for f in findings),
    })
    return findings


def _rank(findings: List[Dict[str, Any]], corpus: List[Dict[str, Any]]) -> None:
    pages = {p["url"]: p for p in corpus}
    shares = [p.get("citation_share") or 0.0 for p in corpus]
    positive = [s for s in shares if s > 0]
    floor = min(positive) if positive else 0.0
    for f in findings:
        page = pages.get(f["page_url"], {})
        share = page.get("citation_share") or 0.0
        imputed = share <= 0 and page.get("owner") == "owned"
        if imputed:
            share = floor
        f["citation_share"] = share
        f["citation_share_imputed"] = imputed
        f["priority"] = share * WEIGHTS[f["verdict"]]
    order = {"stale": 0, "ambiguous": 1, "current": 2}
    findings.sort(key=lambda f: (-f["priority"], order[f["verdict"]], f["page_url"]))
