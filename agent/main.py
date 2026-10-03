"""Content Drift Agent orchestrator.

    python -m agent.main --pr <url> [--local-corpus DIR] [--live] [--json]

Each step imports its real module by the paths in docs/PLAN.md. A missing module
falls back to a stub that returns fixture data in the PLAN.md contract shapes,
and the step is listed as STUBBED. With --live a missing module is an error.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from typing import Any, Callable, Dict, List, Optional

STUB_FETCHED = "stub (not real data)"

# ---------------------------------------------------------------- stubs
def _stub_get_pr_diff(pr_url: str) -> Dict[str, Any]:
    return {"pr": pr_url, "title": "STUB: raise Free plan limits", "base": "main",
            "files": [{"path": "mock-site/index.html", "status": "modified",
                       "patch": "-10,000 session replays / month\n+20,000 session replays / month"}]}


def _stub_extract_fact_deltas(diff: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{"id": "d1", "entity": "Mixpanel Free plan", "attribute": "session replays per month",
             "old": "10,000", "new": "20,000", "unit": "replays/month",
             "source": {"file": "mock-site/index.html", "line": 0},
             "search_terms": ["10,000 session replays", "10K replays"], "confidence": 0.0}]


def _stub_get_related_prompts(deltas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"id": "stub-prompt-1", "text": "STUB prompt about free session replay limits",
             "topic": "Session replay, experiments & feature flags", "mixpanel_visibility": 0.0}]


def _stub_triage(diff: Dict[str, Any], deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"pr": diff["pr"], "verdict": "flag", "tier": "high", "rationale": "STUB verdict",
            "delta_ids": [d["id"] for d in deltas], "confidence": 0.0,
            "evidence": {"topic": "stub", "prompts": _stub_get_related_prompts(deltas),
                         "data_source": "cached", "fetched": STUB_FETCHED}}


def _stub_get_cited_pages(prompt_ids: List[str]) -> List[Dict[str, Any]]:
    return [{"url": "https://example.com/stub-owned", "domain": "example.com", "owner": "owned",
             "citation_share": 0.02, "prompt_ids": list(prompt_ids)},
            {"url": "https://example.org/stub-third-party", "domain": "example.org",
             "owner": "third_party", "citation_share": 0.01, "prompt_ids": list(prompt_ids)}]


def _stub_build_corpus(refs: List[Dict[str, Any]], extra_urls: Optional[List[str]] = None,
                       local_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    return [{"url": r["url"], "owner": r["owner"], "title": "STUB page",
             "text": "Free plan includes 10,000 session replays a month.",
             "passages": ["Free plan includes 10,000 session replays a month."],
             "fetched_at": STUB_FETCHED, "cached": True,
             "citation_share": r["citation_share"], "prompt_ids": r["prompt_ids"]} for r in refs]


def _stub_scan(deltas: List[Dict[str, Any]], corpus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for page in corpus:
        for p in page["passages"]:
            out.append({"page_url": page["url"], "delta_id": deltas[0]["id"], "passage": p,
                        "verdict": "stale", "reason": "STUB",
                        "proposed_edit": {"before": p, "after": p.replace("10,000", "20,000")},
                        "citation_share": page["citation_share"],
                        "priority": page["citation_share"]})
    return sorted(out, key=lambda f: -f["priority"])


def _stub_render_report(report: Dict[str, Any]) -> str:
    s = report["stats"]
    lines = ["## Content Drift Report (STUB RENDERER)", "",
             "Triage: %s / %s" % (report["triage"]["verdict"], report["triage"]["tier"]),
             "Stats: %s" % json.dumps(s), ""]
    for f in report["findings"]:
        lines.append("- [%s] %s (priority %.3f)" % (f["verdict"], f["page_url"], f["priority"]))
    return "\n".join(lines)


def _stub_post_comment(pr_url: str, markdown: str) -> None:
    print("[stub post_comment] would post %d chars to %s" % (len(markdown), pr_url))


# (step name, module path, function name, stub)
STEPS = {
    "get_pr_diff": ("agent.github.diff", "get_pr_diff", _stub_get_pr_diff),
    "extract_fact_deltas": ("agent.facts", "extract_fact_deltas", _stub_extract_fact_deltas),
    "triage": ("agent.triage", "triage", _stub_triage),
    "get_cited_pages": ("agent.profound.client", "get_cited_pages", _stub_get_cited_pages),
    "build_corpus": ("agent.profound.corpus", "build_corpus", _stub_build_corpus),
    "scan": ("agent.scan", "scan", _stub_scan),
    "render_report": ("agent.report", "render_report", _stub_render_report),
    "post_comment": ("agent.report", "post_comment", _stub_post_comment),
}


class StepLoader:
    def __init__(self, live: bool) -> None:
        self.live = live
        self.stubbed = []  # type: List[str]

    def get(self, step: str) -> Callable[..., Any]:
        mod_path, fn_name, stub = STEPS[step]
        try:
            fn = getattr(importlib.import_module(mod_path), fn_name)
        except (ImportError, AttributeError) as exc:
            # ImportError from inside an existing module (missing dependency) must not hide as a stub.
            if isinstance(exc, ModuleNotFoundError) and exc.name not in _prefixes(mod_path):
                raise
            if self.live:
                raise SystemExit("--live: %s.%s is not available (%s)" % (mod_path, fn_name, exc))
            self.stubbed.append("%s (%s.%s)" % (step, mod_path, fn_name))
            return stub
        return fn


def _prefixes(mod_path: str) -> List[str]:
    parts = mod_path.split(".")
    return [".".join(parts[: i + 1]) for i in range(len(parts))]


def run(pr_url: str, local_corpus: Optional[str] = None, live: bool = False,
        post: bool = False) -> Dict[str, Any]:
    """Run the pipeline. Returns a Report (PLAN.md) plus `stubbed` and `markdown`."""
    t0 = time.time()
    steps = StepLoader(live)

    diff = steps.get("get_pr_diff")(pr_url)
    deltas = steps.get("extract_fact_deltas")(diff)
    tri = steps.get("triage")(diff, deltas)

    findings = []  # type: List[Dict[str, Any]]
    corpus = []  # type: List[Dict[str, Any]]
    if tri["verdict"] == "flag":
        prompt_ids = [p["id"] for p in tri["evidence"]["prompts"]]
        refs = steps.get("get_cited_pages")(prompt_ids)
        corpus = steps.get("build_corpus")(refs, local_dir=local_corpus)
        findings = steps.get("scan")(deltas, corpus)
        findings = sorted(findings, key=lambda f: -f["priority"])

    count = lambda v: sum(1 for f in findings if f["verdict"] == v)  # noqa: E731
    report = {"pr": pr_url, "triage": tri, "deltas": deltas, "findings": findings,
              "stats": {"pages_scanned": len(corpus),
                        "passages_checked": sum(len(p["passages"]) for p in corpus),
                        "stale": count("stale"), "ambiguous": count("ambiguous"),
                        "current": count("current"),
                        "elapsed_seconds": round(time.time() - t0, 2)}}
    markdown = steps.get("render_report")(report)
    if post:
        steps.get("post_comment")(pr_url, markdown)
    report["stubbed"] = steps.stubbed
    report["markdown"] = markdown
    return report


def check_key() -> int:
    """Call both configured models once. Never prints the key."""
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set (checked the environment and .env)")
        return 1
    import anthropic
    client = anthropic.Anthropic()
    for model in ("claude-sonnet-5-5", "claude-haiku-4-5-20251001"):
        try:
            r = client.messages.create(model=model, max_tokens=10,
                                       messages=[{"role": "user", "content": "Say ok"}])
            print("%s: OK (%s)" % (model, r.content[0].text.strip()))
        except Exception as exc:  # report and keep going so both models are checked
            print("%s: FAILED %s: %s" % (model, type(exc).__name__, exc))
            return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m agent.main", description=__doc__.split("\n")[0])
    ap.add_argument("--pr", help="PR URL (required unless --check-key)")
    ap.add_argument("--check-key", action="store_true", help="verify ANTHROPIC_API_KEY works, then exit")
    ap.add_argument("--local-corpus", help="directory of local HTML pages (planted corpus)")
    ap.add_argument("--live", action="store_true", help="fail instead of stubbing a missing step")
    ap.add_argument("--post", action="store_true", help="post the report as a PR comment")
    ap.add_argument("--json", action="store_true", help="print the full Report as JSON")
    args = ap.parse_args(argv)

    try:
        from dotenv import load_dotenv  # optional
        load_dotenv()
    except ImportError:
        pass

    if args.check_key:
        return check_key()
    if not args.pr:
        ap.error("--pr is required")
    report = run(args.pr, args.local_corpus, live=args.live, post=args.post)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report["markdown"])
    print("\n--- run summary ---")
    print("triage: %s/%s | stats: %s" % (report["triage"]["verdict"], report["triage"]["tier"],
                                        json.dumps(report["stats"])))
    if report["stubbed"]:
        print("STUBBED steps (output is NOT real): " + "; ".join(report["stubbed"]))
    else:
        print("STUBBED steps: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
