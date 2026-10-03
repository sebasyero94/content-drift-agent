"""Render the Report as a PR comment and post it."""
from __future__ import annotations

import base64
import gzip
import json
import re
import subprocess
import tempfile

from agent.github.diff import parse_pr_url, _gh_api

MARKER = "<!-- content-drift-agent -->"
_DATA_RE = re.compile(r"<!-- report-data:([A-Za-z0-9+/=]+) -->")
APPROVE_LABEL = "content-approved"


def _pct(x) -> str:
    try:
        return "%.2f%%" % (float(x) * 100)
    except (TypeError, ValueError):
        return "n/a"


def _quote(text: str) -> str:
    return "\n".join("> " + line for line in (text or "").strip().splitlines() or [""])


def _finding_block(f: dict, owner_label: str, n: int) -> str:
    lines = [
        "**%d. %s** (%s, %s)" % (n, f["page_url"], f["verdict"], owner_label),
        "",
        "- Priority %.4f · citation share %s · delta `%s`" % (f.get("priority", 0), _pct(f.get("citation_share")), f.get("delta_id", "")),
        "- Why: %s" % f.get("reason", ""),
        "",
        "Passage:",
        _quote(f.get("passage", "")),
    ]
    edit = f.get("proposed_edit")
    if edit:
        lines += ["", "Proposed edit:", "```diff", "- " + edit["before"].replace("\n", "\n- "), "+ " + edit["after"].replace("\n", "\n+ "), "```"]
    else:
        lines += ["", "No edit proposed. A human needs to decide which value is correct."]
    return "\n".join(lines)


def encode_report(report: dict) -> str:
    """Hidden copy of the report, so the approval workflow can read it back from the comment."""
    slim = dict(report)
    slim["findings"] = [f for f in report.get("findings", []) if f.get("verdict") in ("stale", "ambiguous")]
    raw = gzip.compress(json.dumps(slim, separators=(",", ":")).encode("utf-8"))
    return "<!-- report-data:%s -->" % base64.b64encode(raw).decode("ascii")


def decode_report(comment_body: str) -> dict:
    m = _DATA_RE.search(comment_body or "")
    if not m:
        raise ValueError("comment has no report-data block")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))).decode("utf-8"))


def split_by_owner(findings: list):
    """Return (owned, third_party). Uses finding['owner'] when present, else the page host."""
    if any("owner" in f for f in findings):
        return [f for f in findings if f.get("owner") == "owned"], [f for f in findings if f.get("owner") != "owned"]
    owned = [f for f in findings if "mixpanel.com" in f["page_url"] or f["page_url"].startswith("mock-site/")]
    return owned, [f for f in findings if f not in owned]


def render_report(report: dict) -> str:
    t = report.get("triage", {})
    ev = t.get("evidence", {}) or {}
    stats = report.get("stats", {}) or {}
    out = [MARKER, encode_report(report), "## Content Drift report", ""]

    verdict = t.get("verdict", "?")
    out.append("**Verdict: %s** (tier: %s, confidence %s)" % (verdict.upper(), t.get("tier", "?"), t.get("confidence", "n/a")))
    out += ["", t.get("rationale", ""), ""]

    out.append("### Profound evidence")
    out.append("Topic: %s" % ev.get("topic", "n/a"))
    prompts = ev.get("prompts", [])
    if prompts:
        out += ["", "| Tracked prompt | Mixpanel visibility |", "|---|---|"]
        for p in prompts:
            out.append("| %s | %s |" % (p.get("text", p.get("id", "")), _pct(p.get("mixpanel_visibility"))))
    out += [
        "",
        "> Profound data source: **%s**. Fetched **%s**. This run replays saved Profound responses and did not query Profound live."
        % ("cache" if ev.get("data_source") == "cached" else ev.get("data_source", "unknown"), ev.get("fetched", "unknown")),
        "",
    ]

    deltas = report.get("deltas", [])
    out.append("### Fact deltas")
    if deltas:
        out += ["", "| ID | Entity | Attribute | Old | New | Source |", "|---|---|---|---|---|---|"]
        for d in deltas:
            src = d.get("source", {})
            out.append("| %s | %s | %s | %s | %s | %s:%s |" % (d["id"], d["entity"], d["attribute"], d["old"], d["new"], src.get("file", ""), src.get("line", "")))
    else:
        out.append("No fact deltas found in this diff.")
    out.append("")

    findings = sorted(report.get("findings", []), key=lambda f: -f.get("priority", 0))
    findings = [f for f in findings if f.get("verdict") in ("stale", "ambiguous")]
    owned, third = split_by_owner(findings)

    if verdict == "flag":
        out.append("### Findings, ranked by AI citation share")
        out.append("")
        for title, group, label in (("Owned pages (we can edit these)", owned, "owned"), ("Third-party pages (contact the owner)", third, "third party")):
            out.append("#### %s" % title)
            out.append("")
            if not group:
                out += ["None.", ""]
                continue
            for i, f in enumerate(group, 1):
                out += [_finding_block(f, label, i), ""]

    out += [
        "### Stats",
        "",
        "| Pages scanned | Passages checked | Stale | Ambiguous | Current | Seconds |",
        "|---|---|---|---|---|---|",
        "| %s | %s | %s | %s | %s | %s |" % tuple(stats.get(k, "n/a") for k in ("pages_scanned", "passages_checked", "stale", "ambiguous", "current", "elapsed_seconds")),
        "",
        "---",
    ]
    if verdict == "flag":
        out.append("**Human review.** Nothing has been changed. A PMM adds the label `%s` to approve; a workflow then commits `content-updates/pr-<n>.md` with the checklist." % APPROVE_LABEL)
    else:
        out.append("**No content action needed.** This change does not alter a public product fact.")
    return "\n".join(out) + "\n"


def post_comment(pr_url: str, markdown: str) -> None:
    """Post the comment, or update the earlier one from this agent (found by marker)."""
    owner, repo, number = parse_pr_url(pr_url)
    comments = _gh_api("repos/%s/%s/issues/%d/comments?per_page=100" % (owner, repo, number), paginate=True)
    existing = [c for page in comments for c in page if MARKER in (c.get("body") or "")]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"body": markdown}, fh)
        path = fh.name
    if existing:
        cmd = ["gh", "api", "-X", "PATCH", "repos/%s/%s/issues/comments/%d" % (owner, repo, existing[-1]["id"]), "--input", path]
    else:
        cmd = ["gh", "api", "repos/%s/%s/issues/%d/comments" % (owner, repo, number), "--input", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("posting comment failed: %s" % r.stderr.strip())
