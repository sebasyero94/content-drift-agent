# Source note for mock-site/index.html

This page is a demo replica, not Mixpanel's site. No logos or brand assets are copied. Facts were checked on 2026-10-03.

Sources: **P** = https://mixpanel.com/pricing/ (live HTML), **D** = https://docs.mixpanel.com/docs/session-replay (live HTML).

| Fact on the replica | Value | Source |
|---|---|---|
| Free: events / month | Up to 1M | P (plan card and table) |
| Free: session replays / month | 10K | P (card "10K session replays / month", table "10k monthly sessions"); D "10k free Replays per month" |
| Free: experiments | 1k MEU / month | P |
| Free: active feature flags | Up to 10 | P |
| Growth: events | Up to 20M | P |
| Growth: session replays | Up to 500K | P card "Up to 500K session replays / month" (see disagreement below) |
| Growth: experiments | Up to 100k MEU / month | P card |
| Growth: active feature flags | Up to 50 | P |
| Enterprise: events | Up to 1T | P |
| Enterprise: replays, experiments, flags | Custom | P |
| Default replay retention | 30 days | D "By default, replays are stored for 30 days"; P comparison table, Replay retention, "30 days" |
| Enterprise custom retention | custom (no range stated on the replica) | P "Custom data and replay retention policy" |
| Startup discount FAQ | first year free for eligible early-stage companies | P startup section |

## Disagreements on Mixpanel's own pages (not resolved here)
- **Growth replays.** P card says "Up to 500K session replays / month". P comparison table says "20k monthly sessions" for the middle column. D says Growth gets "20k free Replays per month" on plans bought or edited after April 2024. These may describe purchasable versus included volume. The replica uses the card figure (500K).
- **Enterprise retention range.** P table says "7-365 days". D says "between 7 days and 360 days". The replica states no range, to avoid picking a side.
- **Third-party page** (seline.com/blog/mixpanel-pricing, per `docs/data-notes.md`) says Growth "up to 20,000+".
- The same pricing page is internally inconsistent about Growth: card 500K versus table 20k.

Not on the replica because the page and docs do not give a clear single value: Growth retention.
