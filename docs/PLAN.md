# Build Plan: Content Drift Agent

Source of truth for every session. Read order for a new session: `CLAUDE.md` → this file → `docs/handoff.md` → `docs/data-notes.md`.

## Goal
A PR on the mock Mixpanel pricing page triggers an agent that reads the diff, extracts the changed facts, triages whether public content is now wrong, scans owned and AI-cited content for passages stating the old fact, proposes before/after edits, ranks findings by AI citation share, and posts a report on the PR. A PMM approves with a label, which commits a checklist of updates.

Hard deadline: Typeform submission by 6:00 PM, Oct 3, 2026. Round 1 judging 6:00 PM, finals 7:00 PM.

## Sessions and ownership
Each session owns specific paths. Do not edit files you do not own. Put cross-session asks in `docs/handoff.md` under "Requests".

| Session | Owns | Tasks |
|---|---|---|
| `lead` | `CLAUDE.md`, `docs/PLAN.md`, `docs/data-notes.md`, `agent/main.py`, `requirements.txt`, `.env.example`, demo and submission | T1-T5, T10, T25-T27 |
| `plumbing` | `mock-site/`, `agent/github/`, `agent/report.py`, `.github/workflows/`, `content-updates/` | T6, T7, T8, T11, T18, T19, T20 |
| `data` | `agent/profound/` | T12, T13 |
| `engine` | `agent/facts.py`, `agent/triage.py`, `agent/scan.py` | T14-T17 |
| `evals` | `agent/evals/`, `docs/evals.md` | T9, T21-T24 |

Dependencies: `data` and `engine` can start now with fixtures. `engine` T16 needs the corpus shape from `data` T13 (use the fixture until it lands). `evals` T21 needs `scan`; it builds the planted corpus first and runs against whatever `scan` exists. `plumbing` T18 needs `agent/main.py` from `lead` T10; until then it calls a stub. Real Profound data needs `lead` T2 and T3.

## Working agreement
1. Read the four files above before starting. When you finish a task, tick its box here (your own lines only) and append a short entry to `docs/handoff.md`: time, session, what you did, files, interface changes, gotchas, what is next.
2. Anything learned about Profound goes in `docs/data-notes.md` (via the `lead` session, or add a request) and not only in the log.
3. Commit small and often. Stage only your own paths with `git add <paths>`, never `git add -A`. Prefix messages with your session name, for example `engine: add fact delta extractor`.
4. Secrets live in `.env` (gitignored): `ANTHROPIC_API_KEY`. Never commit keys, tokens or OAuth output.
5. No pre-built agents, non-public MCPs or pre-existing systems. Public libraries, MCPs and web pages are fine. Do not build or call Profound agents.
6. Python 3.9 only on this machine. Keep code 3.9-compatible.
7. Verify before reporting done: run it and say what you ran. Report real numbers, including misses. Never cache or present stub output as real.
8. Anything shown as Profound data must say it came from cache and when it was fetched.
9. If blocked, write it under "Blocked" in `docs/handoff.md` and move to the next task.

## Data contracts
Build against fixtures in these shapes until real modules exist. An owner may add keys to their own contracts but must update this section and log it in the same change. Never remove or rename a key without a handoff request.

```python
PRDiff    = {pr: str, title: str, base: str, files: [{path, status, patch}]}

FactDelta = {id: str,                       # "d1", "d2"
             entity: str,                   # "Mixpanel Free plan"
             attribute: str,                # "session replays per month"
             old: str, new: str,            # "10,000", "20,000"
             unit: str,
             source: {file: str, line: int},
             search_terms: [str],           # phrases a page would use to state the old value
             confidence: float}

Triage    = {pr: str,
             verdict: "flag" | "skip",
             tier: "high" | "medium" | "skip",
             rationale: str,                # cites the evidence below
             delta_ids: [str],
             confidence: float,
             evidence: {topic: str,
                        prompts: [{id, text, mixpanel_visibility}],
                        data_source: "cached", fetched: str}}

PageRef   = {url: str, domain: str, owner: "owned" | "third_party",
             citation_share: float, prompt_ids: [str]}

Page      = {url, owner, title, text, passages: [str], fetched_at: str,
             cached: bool, citation_share: float, prompt_ids: [str]}

Finding   = {page_url: str, delta_id: str,
             passage: str,
             verdict: "stale" | "current" | "ambiguous",
             reason: str,
             proposed_edit: {before: str, after: str} | None,   # None unless stale
             citation_share: float,
             priority: float}               # see ranking

Report    = {pr: str, triage: Triage, deltas: [FactDelta], findings: [Finding],
             stats: {pages_scanned, passages_checked, stale, ambiguous, current,
                     elapsed_seconds}}
```

**Ranking.** `priority = citation_share * weight`, weight 1.0 for stale and 0.5 for ambiguous, sorted descending. Current passages are not listed in the PR comment but are counted in stats. Owned pages with no citation data get the minimum citation share seen, not zero.

**Proposed edits.** The `after` text may use only the new value and wording already in the passage. It must not add claims that are not in the diff.

## Interfaces
```python
# agent/github/diff.py            (plumbing)
get_pr_diff(pr_url: str) -> PRDiff

# agent/facts.py                  (engine)
extract_fact_deltas(diff: PRDiff) -> list[FactDelta]

# agent/triage.py                 (engine)
triage(diff: PRDiff, deltas: list[FactDelta]) -> Triage     # calls get_related_prompts

# agent/profound/client.py        (data)
get_related_prompts(deltas: list[FactDelta]) -> list[dict]      # {id, text, topic, mixpanel_visibility}
get_cited_pages(prompt_ids: list[str]) -> list[PageRef]

# agent/profound/corpus.py        (data)
build_corpus(refs: list[PageRef], extra_urls: list[str] = [], local_dir: str = None) -> list[Page]

# agent/scan.py                   (engine)
scan(deltas: list[FactDelta], corpus: list[Page]) -> list[Finding]   # classify, propose edit, priority

# agent/report.py                 (plumbing)
render_report(report: Report) -> str            # markdown for the PR comment
post_comment(pr_url: str, markdown: str) -> None

# agent/main.py                   (lead)
run(pr_url: str, local_corpus: str = None) -> Report
```
`agent/main.py` imports each module by these paths and falls back to stubs when one is missing, listing STUBBED steps in its output. `--live` fails instead of stubbing.

## Tasks
Owner tags are in brackets. Time-boxes assume roughly 4.5 hours total. Adjust if the day is shorter.

### Phase 0: Unblock (30 min)
- [x] **T1** `[lead]` Confirm the Profound MCP is connected in this project (`claude mcp list`, `/mcp`) and sign in if needed (5 min)
  - Done when: a Profound tool call returns data from this project.
- [x] **T2** `[lead]` Find pricing, plan, free-tier and limits prompts in the Mixpanel category, and the pages cited for them (`get_citations_report` with `group_by: ["page"]`) (10 min)
  - Done when: `docs/data-notes.md` lists the prompts (ids, text, Mixpanel visibility) and the top cited URLs with citation share, marked owned or third party.
- [x] **T3** `[lead]` Test fetching about 10 candidate pages (Mixpanel pricing and docs pages, 3 to 4 third-party cited pages) (10 min)
  - Done when: a table in data-notes shows which fetch cleanly and which block, and how each was fetched.
- [ ] **T4** `[lead]` Settle keys: get `ANTHROPIC_API_KEY` into `.env` and as a GitHub secret, and confirm the replay mode for Profound data (5 min)
  - Done when: the Anthropic key works from a script and the replay decision is logged.

### Phase 1: Foundations (45 min)
- [ ] **T5** `[lead]` Confirm the demo facts with the user. Default: Free plan replays 10,000 → 20,000 and active feature flags 10 → 20 (15 min)
  - Done when: facts and the prompts they map to are recorded in `CLAUDE.md` Decisions.
- [ ] **T6** `[plumbing]` Create a GitHub repo for this project and push. Ask the user before creating anything (5 min)
  - Done when: remote exists, repo name recorded, and the user has set the `ANTHROPIC_API_KEY` secret.
- [ ] **T7** `[plumbing]` Build `mock-site/index.html`: static pricing page replica with plan cards, a FAQ and a feature section, labeled as a demo replica. Verify every fact against the live pricing page first (15 min)
  - Done when: the page renders locally and a source note lists where each fact came from.
- [ ] **T8** `[plumbing]` Prepare the three demo PRs as branches with patch files: A pricing, B copy tweak, C retention (10 min)
  - Done when: three branches exist and the diffs are small and clear.
- [ ] **T9** `[evals]` Design the planted corpus: about 10 local HTML pages (FAQ, blog, docs, comparison) with known stale, current and ambiguous passages for PR A and PR C, and a ground-truth JSON (10 min)
  - Done when: `agent/evals/planted/` holds pages and `ground_truth.json`.

### Phase 2: Core (85 min)
- [x] **T10** `[lead]` Scaffold: `requirements.txt`, `.env.example`, `agent/main.py` wired to the interfaces with stubs (10 min)
  - Done when: `python -m agent.main --pr <url>` runs end to end on stubs and lists STUBBED steps.
- [ ] **T11** `[plumbing]` PR diff reader using the GitHub API (`gh` is available) (10 min)
  - Done when: `get_pr_diff` returns a correct `PRDiff` for demo PR A.
- [x] **T12** `[data]` Profound client: `get_related_prompts` and `get_cited_pages`, with real MCP responses cached to `agent/profound/fixtures/` (20 min)
  - Done when: both return real cached data for the facts in PR A, stamped `cached` with a fetch date.
- [x] **T13** `[data]` Corpus builder: fetch, clean and cache pages, split into passages that contain the searchable fact, and load local pages from a directory (20 min)
  - Done when: a corpus builds from real URLs (cached to disk) and from `agent/evals/planted/`.
- [ ] **T14** `[engine]` Fact-delta extractor from a diff, including `search_terms` (15 min)
  - Done when: PR A yields two correct deltas, PR B yields none, PR C yields one.
- [ ] **T15** `[engine]` Triage with Profound evidence, structured and validated (15 min)
  - Done when: PR A is flag/high and cites a specific prompt visibility number, and PR B is skip.
- [ ] **T16** `[engine]` Scan and classify: find passages stating the old fact, mark stale, current or ambiguous with a reason (20 min)
  - Done when: it runs on the planted corpus and on real cached pages, and flags the ambiguity cases instead of picking a side.
- [ ] **T17** `[engine]` Proposed edits and priority ranking per the rules above (15 min)
  - Done when: stale findings carry a before/after, sorted by priority, and edits contain no claims outside the diff.

### Phase 3: Trigger and review (45 min)
- [ ] **T18** `[plumbing]` GitHub Action on PRs touching `mock-site/**`: runs `python -m agent.main --pr <url>` with secrets (20 min)
  - Done when: opening PR A starts the run with no terminal involved.
- [ ] **T19** `[plumbing]` `agent/report.py`: render the report as a PR comment (triage verdict and evidence, deltas, ranked findings with before/after, stats, "from cache, fetched <date>" note) and post it (10 min)
  - Done when: the comment is readable on its own and lists owned pages separately from third-party pages.
- [ ] **T20** `[plumbing]` Approval: the PMM adds the label `content-approved` and a second workflow commits `content-updates/pr-<n>.md` (15 min)
  - Done when: nothing is written before the label, and the file holds a checklist of owned edits and a list of third-party pages to contact.

### Phase 4: Evals (40 min)
- [ ] **T21** `[evals]` Planted-corpus runner: precision and recall of stale detection, and how many ambiguous cases were flagged as ambiguous (15 min)
  - Done when: it prints the numbers and the misses.
- [ ] **T22** `[evals]` Triage set: the three demo PRs plus about 6 synthetic diffs with expected verdicts (10 min)
  - Done when: it prints accuracy and each miss with the rationale.
- [ ] **T23** `[evals]` Edit grounding: every proposed `after` uses only the new value from the diff and adds no new claims (10 min)
  - Done when: it reports grounded versus ungrounded edits.
- [ ] **T24** `[evals]` Real-corpus run: pages scanned, stale and ambiguous found, plus a spot-check sheet of 10 findings for the user to verify (5 min)
  - Done when: the sheet exists and the stats are written to `docs/evals.md`.

### Phase 5: Demo and submission (35 min)
- [ ] **T25** `[lead]` Metrics sheet: manual-process baseline from the user (time to find and fix content for one change), plus our measured numbers (10 min)
  - Done when: three numbers can be said out loud and each has a source.
- [ ] **T26** `[lead]` Run of show, two rehearsals, recorded fallback video (15 min)
  - Done when: a full-run video exists in case live fails.
- [ ] **T27** `[lead]` Submit the Typeform: description, demo link, repo (5 min)
  - Done when: confirmation received before 6:00 PM.

## Demo run of show (5 minutes)
1. Problem, 30 seconds: one fact changes, and the old number lives on dozens of pages nobody tracks. Show the real pricing, docs and third-party discrepancy.
2. Live trigger, 45 seconds: open PR A. The Action starts.
3. Extract and triage, 45 seconds: the fact deltas and a flag verdict citing Profound's visibility numbers. Show PR B being skipped.
4. Scan, 60 seconds: the ranked list of stale passages across owned and AI-cited pages, with before/after edits and the ambiguity flagged.
5. Why this order, 30 seconds: ranking by AI citation share.
6. Human gate, 30 seconds: the PMM adds the label and the checklist lands in the repo.
7. Evals, 45 seconds: precision and recall on the planted corpus, triage accuracy, edit grounding.
8. Close, 15 seconds: next step is a full release feed and re-checking AI answers after the fixes.

## Cut line
Drop in this order. The core slice (extract, triage, scan, report) is not negotiable.
1. Third-party outreach list in the checklist (keep owned edits).
2. Approval-label workflow (keep the PR comment).
3. PR C (retention), keeping A and B.
4. LLM judge in edit grounding (keep the deterministic check).
5. Live page fetching (use cached pages only).

## Risks
- **Anthropic key missing.** Nothing runs end to end without it. Get it first (T4).
- **No unattended Profound access.** Replay cached data, labeled. If asked, say the live link needs an API key.
- **Fetching real pages is brittle.** Cache every page to disk and replay. Some sites block.
- **Mixed or ambiguous numbers on real pages.** Classify as ambiguous with a reason and never pick a side silently.
- **False positives.** The same number in a different context (for example Growth versus Free). Show the passage and a reason, and report precision.
- **The mock looks contrived.** Say it is a stand-in for a full release and show the real-page scan, which is not mocked.
- **Time.** Follow the cut line in order.

## Decisions still open
- Demo facts (T5), default above.
- Whether an unattended Profound API key exists.
- What "Profound-native" means to the judges.
- The manual-process baseline, from the user.
