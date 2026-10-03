# Profound data notes

Owner: `lead` (Phase 0). Anyone who learns something about the data adds it here.
Last verified: 2026-10-03, via the Profound MCP (OAuth). Copied from the earlier project's notes; the `data` and `lead` sessions update it.

## Account and access
- Org id: `7cc62199-0b82-4dc8-a808-019382200e85` ("Sebastian Yerovi (Hackathon)"), the only org.
- **The Mixpanel category is named "SF Hackathon Participant 3 - SaaS"**, id `9bbb7725-af0b-48e7-b6aa-929af4b5c869`. No category is literally called Mixpanel. Confirmed: the owned brand is Mixpanel, competitors include Amplitude, PostHog, Heap, FullStory, Hotjar, GrowthBook and others.
- Other categories (not ours): CPG `b26ebed4-8195-4938-bd98-277d580c4cc6`, Travel `9ae45623-bb22-460d-b572-c8b911bf8a4c`, and an empty one named "Sebastian Yerovi" `76dfff36-b861-4fde-9c3d-1a8a62cb09cc` (no topics).
- Auth in use: OAuth via MCP (per user, interactive). Unattended GitHub Action: see "Auth for unattended runs" below.
- Knowledge base: `mixpanel-context`, id `64e1e764-453c-4ba1-baf4-8b4134828af4` (created by the user in the app 2026-10-03, empty until `context` uploads). Pass the name or slug to `search_knowledge_base`.
- Data window used: 2026-09-03 to 2026-10-02 (30 days). Data runs to at least 2026-09-29.
- 8 AI engines: ChatGPT, Google Gemini, Meta AI, Grok, Google AI Mode, Perplexity, Google AI Overviews, Microsoft Copilot.

## What returns data
| Report (MCP tool) | Works? | Sample row | Notes |
|---|---|---|---|
| visibility (`get_visibility_report`) | Yes | `{topic: "Session replay, experiments & feature flags", asset: Mixpanel, visibility_score: 0.154, share_of_voice: 0.024, average_position: 4.24}` | Raw decimals. Group by topic or prompt. `limit` max 50. 200 prompts x assets is large: filter by `topic_filter` and `assets`. |
| factcheck claims (`get_factcheck_claims`) | **No data** | none | 0 claims from 2026-01-01 to 2026-10-02. Report returns accuracy 0, accurate 0, inaccurate 0. Tool works, category has no FactCheck data. |
| citations (`get_citations_report`) | Yes | `{rank: 4, domain: "posthog.com", count: 946, citation_share: 0.0264}` | Domain level by default, `group_by: ["page"]` for URLs. Topic filter works. |
| query fanouts | **No read tool** | n/a | No MCP tool returns fanouts for existing prompts. An agent node type `profound_query_fanout_estimator` exists, so fanouts may be reachable by building an agent (see below). |
| prompt answers (`get_prompt_answers`) | Yes | `{prompt_id, model: "Google AI Overviews", response_text, observed_at: 2026-09-29, country: "United States"}` | Full answer text with citation links. Useful for showing what AI says today. |
| content optimization analysis | **Not via a direct tool** | n/a | Agent node type `profound_aeo_content_scorecard` and template `content-aeo-scorecard` (input: long-text content, output: AEO score + breakdown). Needs a published agent run through `run_agent`. Not yet tested. |

## Mixpanel category: visibility by topic (Mixpanel only, 30 days)
| Topic | Visibility | Avg position |
|---|---|---|
| Product analytics platforms | 93.5% | 2.2 |
| Analytics by company stage & team | 87.5% | 2.4 |
| Alternatives, migration & build vs buy | 82.7% | 2.4 |
| Implementation, data & integrations | 81.2% | 2.9 |
| Funnels, retention & behavior analysis | 80.9% | 2.2 |
| AI, metrics strategy & reporting | 61.1% | 2.9 |
| Product management practice | 52.5% | 2.2 |
| **Session replay, experiments & feature flags** | **15.4%** | **4.2** |

Topic ids: Product analytics platforms `fa0c5269-6bbf-4d41-a697-1468f770d6f6`; Analytics by company stage & team `4712c49d-9b4d-4d5b-9c2e-b3ed97e9b62e`; Alternatives, migration & build vs buy `093ad710-72c8-43dd-b662-c84004ca4e48`; Implementation, data & integrations `ce61e38b-feab-4328-8156-c24d8252c70e`; Funnels, retention & behavior analysis `b49a05d4-9b65-43d2-a13e-c232c4638167`; AI, metrics strategy & reporting `47c7f6d5-4f52-4648-bdc4-e549d1eeebf6`; Product management practice `358f2330-266f-48ee-8268-d0bcfc70114f`; Session replay, experiments & feature flags `7dd0103c-be15-4de8-8a2f-139a7684ff68`.

200 prompts total in the category (all statuses). Prompt records: `{id, text, status, tag_ids, topic_id, persona_id, language, analysis_types, platforms[], regions}`.

## Biggest gap: session replay, experiments and feature flags
Mixpanel visibility is 15.4% on this topic versus 80%+ elsewhere. Prompts to mine for pricing and plan content (T2): look for prompts about free tiers, limits and pricing in this topic and in 'Alternatives, migration & build vs buy'. For example 'What are the best free feature flag and experimentation tools for startups?' (`8de94090-2f5b-41eb-b256-b652531ec36b`) has Mixpanel at 3%.

Citations in this topic (all brands): amplitude.com 235, growthbook.io 225, g2.com 220, youtube.com 158, statsig.com 146, posthog.com 135. mixpanel.com is not in the top 8. Use `group_by: ["page"]` to get URLs.

## Auth for unattended runs (T4, open)
- The MCP uses OAuth tied to a user and a localhost callback. Not usable in a GitHub Action.
- `whoami` reports `sdk_auth_ok: true`, so the MCP is backed by the Profound SDK. Whether an API key can be issued on this hackathon org is **unconfirmed**. PLAN.md says keys need Enterprise plan and approval. Ask the Profound engineer, or check Settings > API Keys in the app.
- Decision for this project: `data` caches Profound responses to disk from an interactive session and the Action replays them, labeled as cached with the fetch date.

## Agents
Decision (user, 2026-10-03): do not build or call Profound agents.

## Quirks
- Knowledge base MCP can only add documents. Edits and deletes need the REST API or the Profound app. Duplicate document names are rejected.
- Every report is scoped to one category id.
- MCP tool responses over about 25k tokens spill to a file: filter by topic and asset, and keep `limit` at or below 50.
- Visibility under `scope: all` returns one row per asset per bucket; use `assets` to target brands.
- `citation_sources` in FactCheck needs `limit` of 5 or less.
- Dates are inclusive on both ends for v2 tools.

## T2 results (lead, fetched live via MCP 2026-10-03, window 2026-09-03 to 2026-10-02)
The topic "Session replay, experiments & feature flags" has 25 active prompts. **None is literally about pricing or limits.** Those tracked prompts are "best X tools" and comparison prompts. The agent should map a fact delta (replays/month, feature flags) to the closest prompts, and say that this mapping is by topic and not by price intent.

Closest prompts for PR A (free tier replays and feature flags) and PR C (replay retention), with Mixpanel visibility over 30 days:
| Prompt id | Text | Mixpanel vis. | Avg pos |
|---|---|---|---|
| `8de94090-2f5b-41eb-b256-b652531ec36b` | What are the best free feature flag and experimentation tools for startups? | 3.3% | 2.0 |
| `02c54a4a-fe21-46e0-9669-89ba97ce1313` | What are the best session replay tools? | 0% | n/a |
| `65414e9b-6faa-4ae2-aa18-a91908763b97` | What are the best tools that combine product analytics and session replay? | 43.3% | 4.15 |
| `6416931f-6672-482a-a12a-578a7e86cbe1` | What are the best all-in-one tools for analytics, replay, experiments, and flags? | 53.3% | 3.0 |
| `c3be360c-999b-44b4-999b-cf597eafe1b9` | What are the best feature flag tools? | 0% | n/a |
| `fe875764-1a6b-4b5f-af54-e6e3d3531c89` | What are the best session replay tools for mobile apps? | 4.2% | 3.0 |
| `fa97c00b-b55d-471d-94aa-4631defe1b6a` | Best session replay tools that mask sensitive data for privacy compliance? | 0% | n/a |
| `d2a9a208-1ebb-4131-8b1e-56aa48befffa` | What is session replay and how do product teams use it? | 21% | 3.7 |
| `8012aa9c-e7a6-4e7e-bbfa-d13ea39e9a97` | Feature flags in a dedicated tool vs in my analytics platform? | 50% | 4.8 |
The other 16 prompts in the topic (A/B testing, heatmaps, sample size, etc.) are less related. Full list: `list_prompts` with `topic_ids` filter.

**Cited pages** (`get_citations_report`, `group_by: ["page"]`, `topic_filter`, 1,579 pages in the topic). Citation share is averaged per model, and pages are all third party unless noted:
- Topic-wide top 5: learn.g2.com/best-session-replay-software 2.09% (104 cites); userpilot.com/blog/session-replay-tools/ 2.04% (87); quantummetric.com/blog/best-session-replay-tools-in-2026 1.80% (81); configcat.com/blog/top-launchdarkly-alternatives/ 1.25% (66); cleverx.com/blog/best-heatmap-tools-in-2026/ 1.03% (54).
- For the free-feature-flag prompt (98 pages): growthbook.io/insights/free-feature-flagging-tools 8.7%; configcat.com/blog/top-launchdarkly-alternatives/ 7.9%; launchdarkly.com/blog/best-free-feature-flag-services/ 6.0%; posthog.com/compare/best-open-source-feature-flag-tools 5.7%; abtesting.cc/blog/best-free-feature-flag-tools/ 4.9%; statsig.com/comparison/best-free-feature-flagging-tools 2.7%.
- **No mixpanel.com page is in the top 40 of the topic.** Owned: mixpanel.com has 32 citations in this topic (share 0.64%, domain rank 36), versus 178 in "Implementation, data & integrations".
- `mixpanel.com/pricing/` is cited: 30 citations, share 0.09%, page rank 86 (topic-wide, 30 days). `docs.mixpanel.com/docs/session-replay` and `seline.com/blog/mixpanel-pricing` returned **no rows** (not cited in the window).
- `group_by: ["page"]` cannot be combined with `scope: owned` or `domain_filter`; use `page_filter` with full URLs to look up specific pages.

Implication for the demo: the pages that spread a stale Mixpanel number are mostly competitor and listicle pages, and Mixpanel's own pages are barely cited on this topic. Ranking by citation share will put third-party pages first, which matches the thesis.

## T3 results: page fetch test (lead, 2026-10-03)
Method: plain `curl -sL` with a desktop browser User-Agent, 25 s timeout. All 11 pages returned HTTP 200 with full HTML, so no blocking and no headless browser is needed. Text is extracted by stripping script and style tags and then tags (the Mixpanel pricing page repeats each line twice from Alpine.js attributes, so dedupe).

| Page | HTTP / bytes | Mixpanel mentions | Owner |
|---|---|---|---|
| mixpanel.com/pricing/ | 200 / 2.4 MB | 206 | owned |
| docs.mixpanel.com/docs/session-replay | 200 / 545 KB | 422 | owned |
| seline.com/blog/mixpanel-pricing | 200 / 139 KB | 224 | third party (not in Profound citations) |
| learn.g2.com/best-session-replay-software | 200 / 204 KB | 0 | third party, cited |
| userpilot.com/blog/session-replay-tools/ | 200 / 214 KB | 0 | third party, cited |
| quantummetric.com/blog/best-session-replay-tools-in-2026 | 200 / 425 KB | 0 | third party, cited |
| configcat.com/blog/top-launchdarkly-alternatives/ | 200 / 55 KB | 0 | third party, cited |
| growthbook.io/insights/free-feature-flagging-tools | 200 / 197 KB | 0 | third party, cited |
| launchdarkly.com/blog/best-free-feature-flag-services/ | 200 / 582 KB | 0 | third party, cited |
| posthog.com/compare/best-open-source-feature-flag-tools | 200 / 1.2 MB | 0 | third party, cited |
| statsig.com/comparison/best-session-replay-tools | 200 / 456 KB | 0 | third party, cited |

**Key finding: none of the 8 cited third-party pages mentions Mixpanel in its HTML.** (A JS-rendered mention is unlikely but not ruled out.) These pages are cited for the topic's prompts, but they do not state a Mixpanel number. So for PR A and PR C the real scan will find stale text on Mixpanel's own pages and on pages that discuss Mixpanel (like seline), and mostly "current/no mention" on the cited listicles. Do not promise "stale numbers on cited third-party pages" in the demo. The planted corpus (T9) covers the third-party case, and the real-corpus run has to report what it actually finds.

**Verified real drift (live text, 2026-10-03):**
- Pricing page, Free plan: "10K session replays / month", "Up to 1M events / month", "Up to 1k MEU / month for experiments", "Up to 10 active feature flags".
- Docs: Free "10k free Replays per month"; Growth "20k free Replays per month" (plans purchased or edited after April 2024); Enterprise "20k free Replays per month"; "By default, replays are stored for 30 days after the time of ingestion". The pricing page says Growth is "up to 500K" and the docs say 20k free, which is the included-versus-purchasable ambiguity.
- seline (updated 2026-05-28): Free "Around 10,000 session replays per month", Growth "Up to 20,000+ replays per month".
- The demo facts are consistent with the live page: Free replays 10K and flags 10 are the old values for PR A, and default retention 30 days (docs) is the old value for PR C. `plumbing` can encode these in the mock site. Retention 30 days appears on the docs page, not on the pricing page.

Scratch copies of the fetched HTML are not kept in the repo. `data` should fetch again and cache into `agent/profound/fixtures/` or the corpus cache.
