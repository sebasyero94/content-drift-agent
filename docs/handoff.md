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
2026-10-03 · data · T12, T13
- Done, run on PR A facts (replays 10,000→20,000, flags 10→20): `get_related_prompts` returned 9 prompts, `get_cited_pages` 62 PageRefs (61 third party + mixpanel.com/pricing/ owned), `build_corpus` 58 pages OK + 6 failed (3 youtube and 2 reddit: no extractable text; kameleoon.com: HTTP 403). Offline replay (`offline=True` / `CORPUS_OFFLINE=1`) rebuilds the same 58 from disk.
- Files: `agent/profound/{client.py,corpus.py,__init__.py}`, `fixtures/{prompts.json,citations.json,_build_fixtures.py}` (real MCP output, fetched 2026-10-03, window 2026-09-03..10-02), `fixtures/corpus_cache/` (3.4 MB, **commit it**: the Action replays it).
- Interfaces (PLAN shapes kept; extra keys only): prompts and PageRefs also carry `data_source:"cached"`, `fetched`; prompts add `match_terms`; Pages add `passage_context` (nearest heading per passage, parallel to `passages`) and `source` (`web` or `local:<file>`). `provenance()` in client.py gives the "from cache, fetched <date>" line for reports.
- **Failures are not in the returned list**: call `agent.profound.corpus.last_failures()` (also `corpus_cache/failures.json`) -> [{url, reason, status, owner, citation_share}]. Report them in output, do not hide.
- Page.cached = True when served from the disk cache. First fetch run is cached=False.
- `engine`/`main`: for the owned docs and seline pass `extra_urls=["https://docs.mixpanel.com/docs/session-replay","https://seline.com/blog/mixpanel-pricing"]` (mixpanel.com/pricing/ is already a ref). Extra URLs get the lowest citation_share seen, per PLAN rule. `main` should call `get_cited_pages` with `[p["id"] for p in triage["evidence"]["prompts"]]`.
- `local_dir` (for `evals`): .html/.htm/.md/.txt. Optional metadata: HTML `<meta name="owner|citation_share|prompt_ids|url" content=..>` or `<link rel=canonical>`; markdown front matter (`url:`, `owner:`, `citation_share:`, `prompt_ids:`). Defaults: owner owned, url `local/<file>`, citation_share = lowest in run.
- Gotchas: (1) mapping delta→prompt is by keyword/topic overlap (none of the 25 prompts is about pricing); say so in triage. (2) Citations cached for 7 prompts only (top 12 pages each); 2 of the 9 related prompts (d2a9a208, 13369fa0) have no cached citations and are skipped, not guessed. (3) citation_share of a PageRef = mean of its per-prompt shares over requested prompts with cached data (0 where not cited). (4) Real pages: mixpanel.com/pricing has "10K session replays / month" and "Up to 10 active feature flags"; docs has 10k, 20k, "stored for 30 days"; seline "Around 10,000". Passages also include site mega-menu noise (~160 passages per mixpanel.com page); the scan should pre-filter by search_terms. (5) Page text is verbatim, whitespace-normalised, so `before` strings match the passage exactly.
- Next: could cache citations for the 2 missing prompts, or add `terms=` prefilter if `engine` wants it. Ask via Requests.

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
