"""Profound data layer. Serves cached MCP responses from fixtures/ (never live).

The Profound MCP uses interactive OAuth, so automation replays what the `data`
session fetched. Every result carries data_source="cached" and the fetch date.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List
from urllib.parse import urlparse

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OWNED_DOMAIN = "mixpanel.com"
_STOP = {"the", "a", "an", "of", "per", "month", "plan", "in", "for", "and", "or", "to", "on", "is", "are"}
# words a delta might use -> words prompts use for the same product area
_SYN = {"recordings": "replay", "recording": "replay", "replays": "replay", "flags": "flag",
        "flagging": "flag", "experiments": "experiment", "experimentation": "experiment"}


def _load(name: str) -> dict:
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def _stamp(meta: dict) -> dict:
    return {"data_source": "cached", "fetched": meta["fetched"]}


def _tokens(text: str) -> set:
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        w = _SYN.get(w, w)
        if w not in _STOP and len(w) > 2:
            out.add(w)
    return out


def _delta_text(d: dict) -> str:
    parts = [d.get("entity", ""), d.get("attribute", "")] + list(d.get("search_terms") or [])
    return " ".join(parts)


def get_related_prompts(deltas: List[dict], top_n: int = 9) -> List[dict]:
    """Tracked prompts related to the changed facts, best match first.

    Matching is by topic and keyword overlap, NOT price intent: none of the tracked
    prompts is literally about pricing or limits (docs/data-notes.md, T2).
    Each item: {id, text, topic, mixpanel_visibility, data_source, fetched, match_terms}.
    """
    data = _load("prompts.json")
    cited = set(_load("citations.json")["by_prompt"])
    dtext = " ".join(_delta_text(d) for d in deltas)
    dtok = _tokens(dtext)
    free = "free" in dtext.lower()
    scored = []
    for p in data["prompts"]:
        ptok = _tokens(p["text"])
        hit = (dtok & ptok) - {"free"}
        if not hit:
            continue
        score = len(hit) + (1.0 if free and "free" in ptok else 0.0) + (0.1 if p["id"] in cited else 0.0)
        scored.append((score, p, sorted(hit)))
    scored.sort(key=lambda t: (-t[0], -(t[1]["mixpanel_visibility"] or 0)))
    stamp = _stamp(data["_meta"])
    return [dict(id=p["id"], text=p["text"], topic=p["topic"],
                 mixpanel_visibility=p["mixpanel_visibility"], match_terms=hit, **stamp)
            for _, p, hit in scored[:top_n]]


def _ref(page_name: str, share: float, prompt_ids: List[str], stamp: dict) -> dict:
    url = page_name if page_name.startswith("http") else "https://" + page_name
    domain = urlparse(url).netloc.lower()
    owned = domain == OWNED_DOMAIN or domain.endswith("." + OWNED_DOMAIN)
    return dict(url=url, domain=domain, owner="owned" if owned else "third_party",
                citation_share=round(share, 5), prompt_ids=prompt_ids, **stamp)


def get_cited_pages(prompt_ids: List[str]) -> List[dict]:
    """PageRefs for pages AI engines cite on these prompts, highest citation_share first.

    citation_share = mean of the page's per-prompt share over the requested prompts
    that have cached citation data (0 where the page is not cited on one of them).
    Prompts with no cached citations are skipped, not guessed.
    """
    cites = _load("citations.json")
    stamp = _stamp(cites["_meta"])
    use = [p for p in prompt_ids if p in cites["by_prompt"]]
    if not use:
        return []
    acc: Dict[str, dict] = {}
    for pid in use:
        for row in cites["by_prompt"][pid]:
            e = acc.setdefault(row["page"], {"sum": 0.0, "pids": []})
            e["sum"] += row["citation_share"]
            e["pids"].append(pid)
    refs = [_ref(name, e["sum"] / len(use), e["pids"], stamp) for name, e in acc.items()]
    # topic-wide owned lookup (page_filter); not tied to one prompt, so prompt_ids is empty
    for row in cites["owned_page_lookup"]:
        if row["page"] not in acc:
            refs.append(_ref(row["page"], row["citation_share"], [], stamp))
    refs.sort(key=lambda r: -r["citation_share"])
    return refs


def provenance() -> dict:
    """What a report should print: 'Profound data from cache, fetched <date>'."""
    m = _load("prompts.json")["_meta"]
    return {"data_source": "cached", "fetched": m["fetched"], "window": m["window"], "via": m["via"]}
