# Content Drift Agent

Profound Marketing Engineering Hackathon, Oct 3, 2026, San Francisco. Typeform submission deadline **6:00 PM**. Round 1 judging 6:00 PM (parallel rooms), finals 7:00 PM.

## Start here (every session)
Several Claude sessions work on this project in parallel and do not share conversation memory. They share these files instead:
1. This file: brief, rules, rubric, decisions, research findings.
2. `docs/PLAN.md`: tasks (T1 to T27), which session owns what, interfaces and data contracts, working agreement.
3. `docs/handoff.md`: what other sessions have done, requests and blockers. Read it before starting and append to it when you finish a task.
4. `docs/data-notes.md`: what the Profound data actually contains (verified today).

Your session name (`lead`, `plumbing`, `data`, `engine` or `evals`) decides which paths you may edit. If you were not told your session name, ask before changing files.

## The prompt
Find a marketing process that is inhuman in scope or scale, and ship a system or agent that runs it. Judges look for a specific pain point (do not recreate Profound, use its data to be targeted), a clear human-in-the-loop, and a live demo.

## Rules
- Built today. Past builds may be referenced but must be adapted today.
- No pre-built agents, non-public MCPs, or systems built before today. Public MCPs, libraries and public web pages are fine.
- Submission needs a working build or prototype, a short written description, and a demo. No malicious code, respect licenses and IP.
- Demo brand: **Mixpanel**. The Profound dataset holds AEO data about the brand (what AI engines say about it), not Mixpanel product analytics.
- We do not build or call Profound agents (decision 2026-10-03).

## Rubric (1-5 per criterion)
| Criterion | Weight | A 5 means |
|---|---|---|
| Marketing Insight | 30% | Solves a deep pain or gives teams a competitive edge |
| Quantifiable Impact | 25% | KPI ladders to revenue, runs continuously across dimensions a big team could not cover |
| Technical Craft and Quality | 20% | Sophisticated architecture with visible evals or guardrails |
| Working Demo | 15% | Deployable after the demo |
| Scale | 10% | Thousands of dimensions continuously, plug-and-play across orgs |

Prizes: Best overall build ($20k) and Best Profound-native agent ($20k).

## Thesis and pain point
Product teams ship much faster than product marketing can keep up. Feedback from Profound's own product marketing manager: when features change so fast, the hard part is **keeping existing content and assets up to date**. If a feature changed, you must know what changed and then fix every FAQ, blog post, docs page and pricing page that now says the old thing. At 40+ product teams per handful of PMMs, nobody can do that by hand.

## What we are building
**Content Drift Agent.** A PR that changes a product fact triggers an agent that tells the PMM which content is now wrong.
1. **Extract.** Read the PR diff and pull out the *fact deltas*: entity, attribute, old value, new value (for example "Mixpanel Free plan, session replays per month, 10,000 → 20,000").
2. **Triage.** Decide whether the change makes public content wrong (flag) or not (skip, for example a CSS tweak). Use Profound data: which tracked prompts the fact relates to and how visible Mixpanel is on them.
3. **Scan.** Find content that states the old fact: Mixpanel's own pages plus the third-party pages Profound's citations report says AI engines cite for those prompts. Classify each passage as stale, current or ambiguous.
4. **Propose.** Write a before/after edit for each stale passage, grounded only in the diff.
5. **Rank.** Order findings by how much AI engines cite the page, so the PMM fixes the pages that spread the stale number first.
6. **Review.** Post the report on the PR. The PMM approves with a label, which commits a checklist of updates.

**Mock.** The PR target is a small static "Mixpanel pricing page" replica in `mock-site/`. It stands in for a real release. Label it clearly as a demo replica in the page and in the demo. Do not copy logos or brand assets, and do not publish it as if it were Mixpanel's site. At a real company the trigger would be a full release.

**Demo PRs (all on the mock site):**
- PR A, pricing change: Free plan replays 10,000 → 20,000 and active feature flags 10 → 20. Expect: flag, high.
- PR B, copy or style tweak. Expect: skip.
- PR C, feature detail: default replay retention 30 → 60 days. Expect: flag, medium.
Facts for the replica come from the public pricing page. `plumbing` must verify them against the live page before encoding.

## Decisions made
- Our own agent (Claude API, Python) with Profound as the data layer over the MCP. Profound's platform cannot yet take external action calls, and we decided not to use Profound agents.
- **Profound data is replayed from cache in automation.** The MCP uses interactive OAuth, which a GitHub Action cannot use, and no API key is confirmed. The `data` session fetches Profound data interactively through the MCP and caches it to `agent/profound/fixtures/`. Output must say it came from cache and when it was fetched. If an API key appears, switch to live.
- **The mock site lives in this repo** under `mock-site/`. The GitHub Action triggers on PRs that touch `mock-site/**`.
- Python 3.9 only on this machine, so keep all code 3.9-compatible: `from __future__ import annotations`, no `match`, no `X | Y` type syntax at runtime.
- Models: `claude-sonnet-5-5` for fact extraction, triage and edits. `claude-haiku-4-5-20251001` for cheap bulk steps such as filtering passages.
- Demo facts confirmed by user (2026-10-03): PR A Free plan session replays 10,000 → 20,000 and active feature flags 10 → 20; PR C default replay retention 30 → 60 days; PR B copy tweak. Prompt mapping: pending T2 (Profound sign-in needed).
- Human gate: nothing is committed to the repo without the PMM adding the label `content-approved`.

## Research findings to use
**Real example of content drift (verified 2026-10-03, via summarizing fetch tool, re-verify before putting on a slide).** Mixpanel's session replay limits appear in several places and already disagree:
- Pricing page (https://mixpanel.com/pricing/): Free 10K replays a month, Growth "up to 500K", Enterprise retention 7-365 days.
- Docs (https://docs.mixpanel.com/docs/session-replay): Free 10k, Growth "20k free Replays per month" (plans bought or edited after April 2024), Enterprise retention 7 to 360 days, default storage 30 days.
- Third-party article (https://seline.com/blog/mixpanel-pricing, updated 2026-05-28): Free around 10,000, Growth "up to 20,000+".
These may describe different things (included versus purchasable), which is exactly the ambiguity the agent should flag rather than silently resolve.

**Profound platform facts** are in `docs/data-notes.md`. Key points: the Mixpanel category is named "SF Hackathon Participant 3 - SaaS". Visibility, citations and prompt answers return data. FactCheck claims have no data, and there is no query fanout read tool. Mixpanel's weak topic is "Session replay, experiments & feature flags" (15.4% visibility versus 80%+ elsewhere).

## Open questions
- Does the PMM mean only Profound's own content, or customers' content too? We assume the brand's own content plus content AI engines cite about it.
- How do judges define "Profound-native"?
- Is an unattended Profound API key available on this account?
- Anthropic API key: not present in the environment yet. The user claims the $100 credit (link on slide 8) and adds it to `.env`.

## Layout
- `agent/` orchestrator code: `main.py`, `facts.py`, `triage.py`, `scan.py`, `report.py`, and subfolders `github/`, `profound/`, `evals/`
- `mock-site/` the replica pricing page used as the PR target
- `content-updates/` created by the approval workflow
- `docs/` plan, handoff log, data notes, session prompts

## Earlier work
A first project folder, `../profound-hackathon`, built a release-comms agent on a PostHog fork. We dropped that direction. Do not edit it, and do not copy its code. Its `docs/data-notes.md` was the source for ours.

## Working style
Follow the global principles in `~/.claude/CLAUDE.md`: surface assumptions, keep it simple, change only what the task needs, verify before calling anything done. This is a one-day build, so favor a thin end-to-end slice over breadth.
