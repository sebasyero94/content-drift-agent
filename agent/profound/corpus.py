"""Corpus builder: fetch pages, clean to text, split into passages, cache to disk.

Fetched pages are cached as JSON in fixtures/corpus_cache/ so the demo replays offline
(set CORPUS_OFFLINE=1 or offline=True to forbid network). Fetch failures are recorded in
the cache dir (failures.json) and returned by last_failures(); failed pages are NOT in the
returned corpus, and nothing is silently dropped.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "corpus_cache")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MIN_TEXT = 200          # below this a page is "no extractable text" (JS-rendered, video, ...)
MAX_PASSAGE = 350       # longer blocks are split into sentences so a passage states ~one fact
MIN_PASSAGE = 12
_BLOCK = {"p", "div", "section", "article", "main", "aside", "header", "footer", "li", "ul", "ol",
          "dl", "dt", "dd", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "blockquote",
          "figure", "figcaption", "details", "summary", "pre", "form", "h1", "h2", "h3", "h4",
          "h5", "h6", "body", "html", "br", "hr"}
_HEAD = {"h1", "h2", "h3", "h4", "h5", "h6"}
_DROP = ["script", "style", "noscript", "svg", "template", "nav", "iframe", "head"]
_FAILURES: List[dict] = []


def last_failures() -> List[dict]:
    """Failures from the most recent build_corpus call: [{url, reason, status, owner, ...}]."""
    return list(_FAILURES)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _split(block: str) -> List[str]:
    if len(block) <= MAX_PASSAGE:
        return [block]
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", block) if s.strip()]


def _passages(blocks: List[tuple]) -> tuple:
    """blocks: [(heading, text)] -> (passages, contexts), deduped, in page order."""
    seen, out, ctx = set(), [], []
    for heading, text in blocks:
        for p in _split(_norm(text)):
            key = p.lower()
            if len(p) < MIN_PASSAGE or not re.search(r"[A-Za-z]", p) or key in seen:
                continue
            seen.add(key)
            out.append(p)
            ctx.append(heading)
    return out, ctx


def _has_block(el: Tag) -> bool:
    return el.find(list(_BLOCK)) is not None


def _html_blocks(html: str) -> tuple:
    soup = BeautifulSoup(html, "html.parser")
    title = _norm(soup.title.get_text()) if soup.title else ""
    for t in soup(_DROP):
        t.decompose()
    root = soup.body or soup
    blocks: List[tuple] = []
    state = {"heading": ""}

    def flush(buf: List[str]) -> None:
        text = _norm(" ".join(buf))
        if text:
            blocks.append((state["heading"], text))
        buf.clear()

    def walk(el: Tag) -> None:
        buf: List[str] = []
        for ch in el.children:
            if isinstance(ch, NavigableString):
                if type(ch).__name__ in ("Comment", "Doctype", "CData"):
                    continue
                buf.append(str(ch))
            elif isinstance(ch, Tag):
                if ch.name in _HEAD:
                    flush(buf)
                    state["heading"] = _norm(ch.get_text(" "))
                    blocks.append((state["heading"], state["heading"]))
                elif ch.name in _BLOCK and ch.name != "br":
                    flush(buf)
                    walk(ch)
                elif ch.name == "br":
                    flush(buf)
                elif _has_block(ch):
                    flush(buf)
                    walk(ch)
                else:
                    buf.append(ch.get_text(" "))
        flush(buf)

    walk(root)
    return title, blocks


def _md_blocks(md: str) -> tuple:
    title, blocks, heading = "", [], ""
    for para in re.split(r"\n\s*\n", md):
        for line in para.split("\n"):
            m = re.match(r"^(#{1,6})\s+(.*)", line)
            if m:
                heading = _norm(m.group(2))
                title = title or heading
                blocks.append((heading, heading))
        body = [l for l in para.split("\n") if not re.match(r"^#{1,6}\s", l)]
        text = re.sub(r"[*_`>]|^\s*[-+]\s+|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", " ".join(body))
        if _norm(text):
            blocks.append((heading, text))
    return title, blocks


def _owner_of(url: str) -> str:
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    return "owned" if host == "mixpanel.com" or host.endswith(".mixpanel.com") else "third_party"


def _cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest()[:16] + ".json")


def _fetch(url: str, offline: bool, refresh: bool) -> dict:
    """Return a cache record {url,status,title,text,passages,contexts,fetched_at,error,from_cache}."""
    path = _cache_path(url)
    if os.path.exists(path) and not refresh:
        rec = json.load(open(path))
        rec["from_cache"] = True
        return rec
    if offline:
        return {"url": url, "error": "not in cache and offline mode is on", "from_cache": False}
    rec = {"url": url, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"}, timeout=25)
        rec["status"] = r.status_code
        if r.status_code != 200:
            rec["error"] = "HTTP %d" % r.status_code
        else:
            title, blocks = _html_blocks(r.content)
            passages, ctx = _passages(blocks)
            text = "\n".join(passages)
            rec.update(title=title, text=text, passages=passages, contexts=ctx, bytes=len(r.content))
            if len(text) < MIN_TEXT:
                rec["error"] = "no extractable text (%d chars; likely JS-rendered or media page)" % len(text)
    except Exception as e:  # network, TLS, timeout: record, never hide
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:160])
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(rec, open(path, "w"))   # failures are cached too, so replays report them identically
    rec["from_cache"] = False
    return rec


def _local_pages(local_dir: str, default_share: float) -> List[dict]:
    """Local .html/.htm/.md/.txt pages. Optional metadata (all optional):
    html: <meta name="owner|citation_share|prompt_ids|url" content=...> or <link rel=canonical>;
    md: front matter lines `owner:`, `citation_share:`, `prompt_ids:` (comma list), `url:`.
    Defaults: owner owned, url local/<filename>, citation_share = lowest share in the run."""
    pages = []
    for name in sorted(os.listdir(local_dir)):
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".html", ".htm", ".md", ".markdown", ".txt"):
            continue
        path = os.path.join(local_dir, name)
        raw = open(path, encoding="utf-8", errors="replace").read()
        meta: Dict[str, str] = {}
        if ext in (".html", ".htm"):
            soup = BeautifulSoup(raw, "html.parser")
            for m in soup.find_all("meta"):
                if m.get("name") and m.get("content"):
                    meta[m["name"].lower()] = m["content"]
            can = soup.find("link", rel="canonical")
            if can and can.get("href"):
                meta.setdefault("url", can["href"])
            title, blocks = _html_blocks(raw)
        else:
            fm = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
            if fm:
                for line in fm.group(1).split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip().lower()] = v.strip()
                raw = raw[fm.end():]
            title, blocks = _md_blocks(raw)
        passages, ctx = _passages(blocks)
        url = meta.get("url") or "local/" + name
        owner = meta.get("owner") or (_owner_of(url) if meta.get("url") else "owned")
        pids = [p.strip() for p in meta.get("prompt_ids", "").split(",") if p.strip()]
        share = float(meta["citation_share"]) if meta.get("citation_share") else default_share
        pages.append(dict(url=url, owner=owner, title=meta.get("title") or title, text="\n".join(passages),
                          passages=passages, passage_context=ctx,
                          fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(os.path.getmtime(path))),
                          cached=True, citation_share=share, prompt_ids=pids, source="local:" + name))
    return pages


def build_corpus(refs: List[dict], extra_urls: Optional[List[str]] = None, local_dir: Optional[str] = None,
                 offline: Optional[bool] = None, refresh: bool = False, workers: int = 8) -> List[dict]:
    """Page dicts (PLAN contract + passage_context, source) for refs, extra_urls and local_dir.

    extra_urls (e.g. owned docs with no citation data) get the lowest citation_share seen in refs,
    per the PLAN ranking rule. Failed fetches are excluded here and listed by last_failures().
    """
    if offline is None:
        offline = os.environ.get("CORPUS_OFFLINE") == "1"
    _FAILURES.clear()
    refs = list(refs or [])
    shares = [r["citation_share"] for r in refs if r.get("citation_share")]
    min_share = min(shares) if shares else 0.0
    by_url: Dict[str, dict] = {r["url"]: dict(r) for r in refs}
    for u in extra_urls or []:
        by_url.setdefault(u, dict(url=u, owner=_owner_of(u), citation_share=min_share, prompt_ids=[]))
    urls = list(by_url)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        recs = list(ex.map(lambda u: _fetch(u, offline, refresh), urls))
    pages: List[dict] = []
    for u, rec in zip(urls, recs):
        ref = by_url[u]
        if rec.get("error"):
            _FAILURES.append(dict(url=u, reason=rec["error"], status=rec.get("status"),
                                  owner=ref.get("owner"), citation_share=ref.get("citation_share"),
                                  fetched_at=rec.get("fetched_at")))
            continue
        pages.append(dict(url=u, owner=ref.get("owner") or _owner_of(u), title=rec.get("title", ""),
                          text=rec["text"], passages=rec["passages"], passage_context=rec["contexts"],
                          fetched_at=rec["fetched_at"], cached=bool(rec["from_cache"]),
                          citation_share=ref.get("citation_share", min_share),
                          prompt_ids=ref.get("prompt_ids", []), source="web"))
    if local_dir:
        pages.extend(_local_pages(local_dir, min_share))
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(_FAILURES, open(os.path.join(CACHE_DIR, "failures.json"), "w"), indent=1)
    return pages
