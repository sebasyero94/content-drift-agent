"""Build content-updates/pr-<n>.md from the agent's PR comment. Run by the approval workflow.

    python -m agent.github.approve <pr_url> [--out-dir content-updates]

Writes nothing unless the PR has a Content Drift comment with a 'flag' verdict.
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys

from agent.github.diff import parse_pr_url, _gh_api
from agent.report import MARKER, decode_report, split_by_owner


def load_report(pr_url: str) -> dict:
    owner, repo, number = parse_pr_url(pr_url)
    pages = _gh_api("repos/%s/%s/issues/%d/comments?per_page=100" % (owner, repo, number), paginate=True)
    mine = [c for page in pages for c in page if MARKER in (c.get("body") or "")]
    if not mine:
        raise SystemExit("No Content Drift comment on %s; nothing written." % pr_url)
    return decode_report(mine[-1]["body"])


def render_checklist(report: dict, approver: str = "unknown") -> str:
    ev = report["triage"].get("evidence", {})
    findings = sorted(report.get("findings", []), key=lambda f: -f.get("priority", 0))
    stale = [f for f in findings if f["verdict"] == "stale"]
    ambiguous = [f for f in findings if f["verdict"] == "ambiguous"]
    owned_stale, third_stale = split_by_owner(stale)
    owned_amb, third_amb = split_by_owner(ambiguous)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    out = [
        "# Content updates for %s" % report["pr"],
        "",
        "Approved by @%s on %s (label `content-approved`)." % (approver, now),
        "Profound data in the source report came from %s, fetched %s." % (ev.get("data_source", "unknown"), ev.get("fetched", "unknown")),
        "",
        "## Fact changes",
    ]
    for d in report.get("deltas", []):
        out.append("- %s, %s: %s -> %s" % (d["entity"], d["attribute"], d["old"], d["new"]))
    out += ["", "## Owned pages to edit", ""]
    if not owned_stale:
        out.append("None.")
    for f in owned_stale:
        e = f["proposed_edit"]
        out += ["- [ ] %s (citation share %.2f%%)" % (f["page_url"], f.get("citation_share", 0) * 100),
                "  - before: %s" % e["before"], "  - after: %s" % e["after"]]
    out += ["", "## Third-party pages to contact", ""]
    if not third_stale:
        out.append("None.")
    for f in third_stale:
        e = f["proposed_edit"]
        out += ["- [ ] %s (citation share %.2f%%)" % (f["page_url"], f.get("citation_share", 0) * 100),
                "  - ask the page owner to change: \"%s\" -> \"%s\"" % (e["before"], e["after"])]
    out += ["", "## Needs a human decision (ambiguous, no edit proposed)", ""]
    if not (owned_amb or third_amb):
        out.append("None.")
    for f in owned_amb + third_amb:
        out += ["- [ ] %s: %s" % (f["page_url"], f.get("reason", ""))]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pr_url")
    ap.add_argument("--out-dir", default="content-updates")
    args = ap.parse_args(argv)
    report = load_report(args.pr_url)
    if report["triage"].get("verdict") != "flag":
        print("Verdict is %s; nothing written." % report["triage"].get("verdict"))
        return 0
    _, _, number = parse_pr_url(args.pr_url)
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, "pr-%d.md" % number)
    with open(path, "w") as fh:
        fh.write(render_checklist(report, os.environ.get("APPROVER", "unknown")))
    print("Wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
