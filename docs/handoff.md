# Handoff log

Shared by every session. Append new entries at the top of "Log". Keep each entry to a few lines. Newest first.

Entry format:
`YYYY-MM-DD HH:MM · session · task ids` then: what was done, files touched, interface changes, gotchas, what is next.

## Requests
Cross-session asks. Say who it is for and what you need.

(none yet)

## Blocked
- (none) The Anthropic key is in `.env` and verified (see the 2026-10-03 lead T4 entry). Still open: the GitHub secret, which `plumbing` T6 needs the user to set once the repo exists.

## Log
2026-10-03 · lead · T4 (partial)
- `ANTHROPIC_API_KEY` is in `.env`. `python -m agent.main --check-key` returned OK for `claude-sonnet-5-5` and `claude-haiku-4-5-20251001`. All sessions can now call the API from scripts (load `.env` via python-dotenv).
- Replay decision stands: Profound data is replayed from cache and labeled. Still no confirmed API key for Profound.
- Open: the GitHub secret `ANTHROPIC_API_KEY` (user sets it after `plumbing` T6 creates the repo).

2026-10-03 · lead · T3
- Fetched 11 pages with plain curl plus a browser User-Agent: all HTTP 200, none blocked. Table in `docs/data-notes.md` ("T3 results").
- Important for `data`, `engine`, `evals`: **the 8 top Profound-cited third-party pages never mention Mixpanel**, so the real scan will mostly return "no mention" for them. Stale and ambiguous findings on real data will come from mixpanel.com/pricing, docs.mixpanel.com session-replay and seline.com/blog/mixpanel-pricing (all three state the replay numbers and already disagree). The planted corpus carries the third-party stale cases. Do not claim otherwise in outputs.
- For `plumbing` T7: verified live on the pricing page, Free plan = 10K session replays/month, 1M events, 1k MEU experiments, 10 active feature flags. The 30-day default retention is in the docs page, not the pricing page.
- The Mixpanel pricing page text is duplicated in the HTML (Alpine attributes): dedupe when extracting passages.

2026-10-03 · lead · T1, T2
- Profound MCP is connected (`whoami` ok, `sdk_auth_ok: true`). `data` can now fetch live and cache to `agent/profound/fixtures/`.
- T2 results are in `docs/data-notes.md` ("T2 results"): the 25 prompts in the weak topic, the closest ones for PR A and PR C with ids and Mixpanel visibility, and page-level citations with shares.
- Gotchas for `data` and `engine`: no tracked prompt is about pricing, so mapping deltas to prompts is by topic, not price intent (say so in triage evidence). `group_by: ["page"]` cannot be combined with `scope: owned` or `domain_filter`; use `page_filter` with full URLs. Citation `page.name` has no scheme (`domain/path`). mixpanel.com/pricing/ has 30 citations (share 0.09%); the Mixpanel docs page and the seline.com article have none in the window, so they would need the "no citation data gets the minimum share" rule from PLAN.
- Next: T3 (test page fetches), then T4 and T5 still need the user.

2026-10-03 · lead · T1 (partial), T10
- Added Profound MCP to this project (`claude mcp add ... profound`); `claude mcp list` says Connected, but its tools are not loaded in the lead session until the user completes OAuth via `/mcp`. T2/T3 wait on that.
- T10 done: `requirements.txt`, `.env.example`, `agent/main.py`, `agent/__init__.py` (empty; other packages work as namespace packages, add your own `__init__.py` if you need one). venv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (Python 3.9.6, anthropic 0.125).
- Run: `.venv/bin/python -m agent.main --pr <url> [--local-corpus DIR] [--post] [--json] [--live]`. Verified: on stubs it runs end to end and lists every STUBBED step; `--live` exits 1 naming the first missing module.
- Interface notes: main calls `get_pr_diff, extract_fact_deltas, triage, get_cited_pages, build_corpus, scan, render_report, post_comment` by the PLAN paths. `triage()` must call `get_related_prompts` itself, and main reads `triage["evidence"]["prompts"][*]["id"]` to fetch cited pages. main only scans when `verdict == "flag"`. Real-module import errors that are not "module missing" (e.g. a missing dependency) are raised, not stubbed. `--post` posts the comment (off by default; plumbing's Action should pass it).
- `python -m agent.main --check-key` calls both models once and never prints the key.
- Next: T2/T3 (need Profound sign-in), T4 (need key), T5 (need user answer).

2026-10-03 · lead · setup: new project created from scratch (Content Drift Agent). Earlier direction (release comms on a PostHog fork, folder `../profound-hackathon`) dropped. Profound facts carried over into `docs/data-notes.md`. Nothing built yet.
