"""Read a pull request's diff through the GitHub API (via the gh CLI)."""
from __future__ import annotations

import json
import re
import subprocess

_PR_URL = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(pr_url: str):
    m = _PR_URL.search(pr_url)
    if not m:
        raise ValueError("Not a GitHub PR URL: %s" % pr_url)
    return m.group(1), m.group(2), int(m.group(3))


def _gh_api(path: str, paginate: bool = False):
    cmd = ["gh", "api", path]
    if paginate:
        cmd += ["--paginate", "--slurp"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("gh api %s failed: %s" % (path, out.stderr.strip()))
    return json.loads(out.stdout)


def get_pr_diff(pr_url: str) -> dict:
    """Return PRDiff: {pr, title, base, files: [{path, status, patch}]}."""
    owner, repo, number = parse_pr_url(pr_url)
    base = "repos/%s/%s/pulls/%d" % (owner, repo, number)
    pr = _gh_api(base)
    pages = _gh_api(base + "/files?per_page=100", paginate=True)
    files = [f for page in pages for f in page]
    return {
        "pr": pr_url,
        "title": pr["title"],
        "base": pr["base"]["ref"],
        "files": [
            {"path": f["filename"], "status": f["status"], "patch": f.get("patch", "")}
            for f in files
        ],
    }


if __name__ == "__main__":
    import sys

    print(json.dumps(get_pr_diff(sys.argv[1]), indent=2))
