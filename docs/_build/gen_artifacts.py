import re, html, os
HERE=os.path.dirname(os.path.abspath(__file__)); DOCS=os.path.dirname(HERE)
PLAN=open(os.path.join(DOCS,'PLAN.md')).read()
OLD_PLAN_TPL=os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/profound-hackathon/docs/_build/plan_tpl.html')
css=re.search(r'<style>(.*?)</style>',open(OLD_PLAN_TPL).read(),re.S).group(1)
FONT='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">'
EXTRA="""
.dg{display:block;min-width:820px;width:100%;height:auto;color:var(--fg)}
.lane{fill:var(--surface)}.lane.alt{fill:var(--lane)}.lane.prof{fill:var(--accent-soft);opacity:.55}
.ln{font:500 12px var(--mono);fill:var(--muted)}
.bx{fill:var(--surface);stroke:var(--line);stroke-width:1.2}.bx.p{stroke:var(--accent);stroke-width:1.6}.bx.h{fill:var(--human-soft);stroke:var(--human);stroke-width:1.6}
.bt{font:400 11px var(--font);fill:var(--fg)}
.ar{stroke:var(--fg);stroke-width:1.3}.al{font:400 10.5px var(--mono);fill:var(--muted)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
figcaption,.cap{color:var(--muted);font-size:14px;max-width:80ch}
.key{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.key span{display:inline-flex;align-items:center;gap:6px}.sw{width:12px;height:12px;border-radius:2px;border:1.6px solid var(--line);display:inline-block}
.sw.p{border-color:var(--accent)}.sw.h{border-color:var(--human);background:var(--human-soft)}
.badge{font-family:var(--mono);font-size:11px;padding:1px 7px;border-radius:3px;border:1px solid var(--line);white-space:nowrap}
.badge.stale{border-color:var(--human);background:var(--human-soft);color:var(--human)}
.badge.amb{border-color:var(--muted);color:var(--muted)}
.badge.ok{border-color:var(--accent);background:var(--accent-soft);color:var(--accent)}
.own{font-family:var(--mono);font-size:11px;color:var(--accent);margin-right:6px}
.own.l{color:var(--muted)}
.ba{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){.ba{grid-template-columns:1fr}}
.ba div{border:1px solid var(--line);border-radius:6px;padding:10px 12px;background:var(--surface);font-size:14px}
.ba b{display:block;font-family:var(--mono);font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.ba .new{border-color:var(--accent);background:var(--accent-soft)}
"""
# ---------- diagram ----------
LH=84; TOP=24; BW=116; BH=52; STEP=132; X0=110; NL=5
W=X0+6*STEP+BW+70; H=TOP+NL*LH+12
cx=lambda i:X0+(i-1)*STEP
cy=lambda l:TOP+l*LH+LH//2
def svg(lanes,boxes,arrows,label):
    o=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{label}" class="dg"><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1 L9 5 L0 9 z" fill="currentColor"/></marker></defs>']
    for l,name in enumerate(lanes):
        cls='lane prof' if l==2 else ('lane alt' if l%2 else 'lane')
        o.append(f'<rect class="{cls}" x="0" y="{TOP+l*LH}" width="{W}" height="{LH}"/>')
        parts=name.split('|')
        for k,t in enumerate(parts):
            y=cy(l)+4-(len(parts)-1)*7+k*14
            o.append(f'<text class="ln" x="12" y="{y}">{t}</text>')
    for (i,l,txt,kind) in boxes:
        x=cx(i); y=cy(l)-BH//2
        o.append(f'<rect class="bx {kind}" x="{x}" y="{y}" width="{BW}" height="{BH}" rx="4"/>')
        ls=txt.split('|'); y0=cy(l)-(len(ls)-1)*7+4
        for k,t in enumerate(ls): o.append(f'<text class="bt" x="{x+BW//2}" y="{y0+k*14}" text-anchor="middle">{t}</text>')
    for pts,lab,both in arrows:
        d='M'+' L'.join(f'{a} {b}' for a,b in pts)
        ms=' marker-start="url(#ah)"' if both else ''
        o.append(f'<path class="ar" d="{d}" fill="none"{ms} marker-end="url(#ah)"/>')
        if lab:
            lx,ly,anc,t=lab; o.append(f'<text class="al" x="{lx}" y="{ly}" text-anchor="{anc}">{t}</text>')
    o.append('</svg>'); return '\n'.join(o)
lanes=['GitHub','Our agent','Profound|(cached MCP)','Web pages','PMM']
boxes=[(1,0,'PR changes the|mock pricing|page','n'),(7,0,'PR comment:|ranked report','n'),
 (2,1,'Extract fact|deltas: entity,|old to new','n'),(3,1,'Triage: flag|or skip, with|evidence','n'),
 (6,1,'Classify: stale,|current, ambiguous;|propose edits','n'),(7,1,'Rank by AI|citation share','n'),
 (3,2,'Related prompts|and Mixpanel|visibility','p'),(4,2,'Pages cited for|those prompts|(citation share)','p'),
 (5,3,'Fetch and cache,|split into|passages','n'),
 (7,4,'PMM reviews;|label approves,|checklist committed','h')]
arrows=[
 ([(cx(1)+58,cy(0)+26),(cx(1)+58,cy(1)),(cx(2),cy(1))],(cx(1)+64,(cy(0)+26+cy(1))//2+4,'start','Action fires'),False),
 ([(cx(2)+116,cy(1)),(cx(3),cy(1))],None,False),
 ([(cx(3)+58,cy(1)+26),(cx(3)+58,cy(2)-26)],(cx(3)+64,(cy(1)+cy(2))//2+4,'start','related prompts'),True),
 ([(cx(3)+116,cy(1)),(cx(4)+58,cy(1)),(cx(4)+58,cy(2)-26)],(cx(4)+64,(cy(1)+cy(2))//2+4,'start','if flagged'),False),
 ([(cx(4)+116,cy(2)),(cx(5)+58,cy(2)),(cx(5)+58,cy(3)-26)],(cx(5)+64,(cy(2)+cy(3))//2+4-8,'start','URLs'),False),
 ([(cx(5)+116,cy(3)),(cx(6)+58,cy(3)),(cx(6)+58,cy(1)+26)],(cx(6)+64,(cy(2)+cy(3))//2+4,'start','page text'),False),
 ([(cx(6)+116,cy(1)),(cx(7),cy(1))],None,False),
 ([(cx(7)+58,cy(1)-26),(cx(7)+58,cy(0)+26)],(cx(7)+64,(cy(0)+cy(1))//2+4,'start','post'),False),
 ([(cx(7)+116,cy(0)),(cx(7)+116+16,cy(0)),(cx(7)+116+16,cy(4)),(cx(7)+116,cy(4))],None,False)]
fig=svg(lanes,boxes,arrows,'Pipeline: a PR changing the mock pricing page fires a GitHub Action. The agent extracts fact deltas, triages with Profound prompt and visibility data, fetches pages Profound reports as cited, classifies passages as stale, current or ambiguous with proposed edits, ranks by citation share, and posts a report that a PMM approves with a label.')
diagram=f"""<title>Content Drift Agent</title>
{FONT}
<style>{css}{EXTRA}</style>
<main>
<header class="top">
<div class="tag">Marketing Engineering Hackathon · Architecture</div>
<h1>Content Drift Agent</h1>
<p class="lead">When a product fact changes, the agent finds every page that still states the old one, proposes the edit, and ranks the pages by how much AI engines cite them. A PMM reviews and approves.</p>
</header>

<section class="fig">
<div class="scroll">{fig}</div>
<figcaption>A PR to a mock Mixpanel pricing page stands in for a full release. Profound supplies the prompts, visibility and cited pages. Everything else runs in our own agent.</figcaption>
<div class="key"><span><i class="sw"></i>Our code, GitHub or the web</span><span><i class="sw p"></i>Profound data (replayed from cache)</span><span><i class="sw h"></i>Human review</span></div>
</section>

<section class="fig">
<h2>What the PMM sees</h2>
<p class="cap">Format of one finding in the PR comment. The page and quote are from Mixpanel's public docs. The edit is illustrative.</p>
<div class="tw"><table>
<thead><tr><th>Rank</th><th>Page</th><th>Verdict</th><th>Why it ranks here</th></tr></thead>
<tbody>
<tr><td>1</td><td><span class="own">owned</span>docs.mixpanel.com/docs/session-replay</td><td><span class="badge stale">stale</span></td><td>States the old Free plan quota as current. AI citation share from Profound.</td></tr>
<tr><td>2</td><td><span class="own l">third party</span>pricing roundup article</td><td><span class="badge stale">stale</span></td><td>Cited by AI engines for plan-limit prompts. Not ours to edit, so it goes on the outreach list.</td></tr>
<tr><td>3</td><td><span class="own">owned</span>pricing FAQ</td><td><span class="badge amb">ambiguous</span></td><td>Page quotes two different numbers for the same plan. The agent flags it and does not pick one.</td></tr>
</tbody></table></div>
<div class="ba"><div><b>Before</b>Free: 10k free Replays per month</div><div class="new"><b>After (proposed)</b>Free: 20k free Replays per month</div></div>
</section>

<section class="fig">
<h2>Why this is a real problem</h2>
<p>Mixpanel's own pages already disagree about session replay limits. The pricing page says Growth gets up to 500K replays a month, the docs say 20k free, and Enterprise retention is 7-365 days on one page and 7 to 360 days on another. They may describe different things, such as included versus purchasable. That ambiguity is what the agent should flag. At 40+ product teams per handful of PMMs, nobody can check this by hand after every change.</p>
</section>

<section class="fig">
<h2>How it differs from a release-notes tool</h2>
<div class="tw"><table>
<thead><tr><th>&nbsp;</th><th>Release notes generator</th><th>Content Drift Agent</th></tr></thead>
<tbody>
<tr><td>Question</td><td>What should we say about this change?</td><td>What have we already said that is now wrong?</td></tr>
<tr><td>Output</td><td>New assets</td><td>Ranked list of stale content with edits</td></tr>
<tr><td>Where Profound data matters</td><td>Optional context</td><td>Core: it says which pages AI engines cite, so it orders the work</td></tr>
<tr><td>Quality check</td><td>Reads well</td><td>Precision and recall on a planted corpus, plus edits that add no new claims</td></tr>
</tbody></table></div>
</section>

<section class="fig">
<h2>Questions for the Profound team</h2>
<ol class="q">
<li><p>Can page-level citations for a prompt be pulled programmatically, and how often are they refreshed?</p></li>
<li><p>Does Profound keep the text of the pages it sees cited? If it does, we could scan that copy instead of fetching pages ourselves.</p></li>
<li><p>Is an API key available so the agent can reach Profound without an interactive sign-in? Today we replay cached data in automation.</p></li>
<li><p>FactCheck claims return no data for this category. If they were enabled, a stale page could be tied to an inaccurate AI answer.</p></li>
<li><p>Did the PMM mean only a brand's own content, or also third-party pages that AI engines cite about it?</p></li>
<li><p>What does "Profound-native" mean for judging?</p></li>
</ol>
<p class="note">Based on Profound's public docs and the hackathon account as of today. The diagram shows the plan and has not been tested end to end.</p>
</section>
</main>"""
open(os.path.join(DOCS,'architecture-diagram.html'),'w').write(diagram)

# ---------- plan ----------
def sect(title):
    m=re.search(r'^## '+re.escape(title)+r'.*?\n(.*?)(?=^## |\Z)',PLAN,re.S|re.M); return m.group(1).strip()
def inline(s):
    s=html.escape(s); return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
phases=[]
for m in re.finditer(r'^### (Phase \d+): (.*?) \((\d+) min\)\n(.*?)(?=^### |^## |\Z)',PLAN,re.S|re.M):
    tasks=[]
    for t in re.finditer(r'- \[[ x]\] \*\*T(\d+)\*\* `\[(\w+)\]` (.*?) \((\d+) min\)\n  - Done when: (.*?)(?=\n- \[|\n\n|\Z)',m.group(4),re.S):
        tasks.append(t.groups())
    phases.append((m.group(1),m.group(2),m.group(3),tasks))
total=sum(len(p[3]) for p in phases)
ph_html=[]
for ph,name,mins,tasks in phases:
    rows=''.join(f'<li class="task"><label><input type="checkbox" id="t{n}" data-k="t{n}"><span class="tt"><b class="tn">T{n}</b> <span class="own">{o}</span>{inline(t)}</span></label><div class="meta"><span class="min">{mm} min</span><span class="done"><b>Done when</b> {inline(d.strip())}</span></div></li>' for n,o,t,mm,d in tasks)
    ph_html.append(f'<section class="phase" id="{ph.lower().replace(" ","")}"><div class="ph"><h2>{ph}: {name}</h2><span class="tb">{mins} min</span></div><ul class="tasks">{rows}</ul></section>')
NUM=re.compile(r'^\d+\. ')
def olist(title):
    out=[]
    for l in sect(title).split('\n'):
        if NUM.match(l): out.append('<li>'+inline(NUM.sub('',l))+'</li>')
    return ''.join(out)
def ulist(title): return ''.join(f'<li>{inline(l[2:])}</li>' for l in sect(title).split('\n') if l.startswith('- '))
demo=olist('Demo run of show (5 minutes)'); cut=olist('Cut line'); risks=ulist('Risks'); dec=ulist('Decisions still open')
nav=''.join(f'<a href="#{p[0].lower().replace(" ","")}">{p[0]}</a>' for p in phases)
tpl_extra=".tn{font-family:var(--mono);font-size:12px;color:var(--muted);margin-right:4px}.own{font-family:var(--mono);font-size:11px;color:var(--accent);border:1px solid var(--accent);border-radius:3px;padding:0 5px;margin-right:6px}.tt .own{white-space:nowrap}"
plan=f"""<title>Content Drift Build Plan</title>
{FONT}
<style>{css}{EXTRA}{tpl_extra}</style>
<main>
<header class="top">
<div class="tag">Marketing Engineering Hackathon · Build plan</div>
<h1>Content Drift Build Plan</h1>
<p class="lead">A PR changes a product fact. The agent finds every page that still states the old one, proposes the edit, and ranks the pages by AI citation share for a PMM to approve. This is the working checklist. The source of truth for sessions is docs/PLAN.md in the repo.</p>
<div class="prog"><div class="bar"><i id="barfill"></i></div><span id="progtext">0 of {total} tasks done</span></div>
<nav class="nav" aria-label="Sections"><a href="#sessions">Sessions</a>{nav}<a href="#demo">Demo</a><a href="#cut">Cut line</a><a href="#risks">Risks</a><a href="#decisions">Decisions</a></nav>
</header>

<section id="sessions">
<h2>Who builds what</h2>
<div class="tw"><table>
<thead><tr><th>Session</th><th>Owns</th><th>Tasks</th></tr></thead>
<tbody>
<tr><td>lead</td><td>Plan, data notes, entry point, demo and submission</td><td>T1-T5, T10, T25-T27</td></tr>
<tr><td>plumbing</td><td>Mock pricing page, GitHub Action, PR comment, approval</td><td>T6, T7, T8, T11, T18-T20</td></tr>
<tr><td>data</td><td>Profound client, page corpus</td><td>T12, T13</td></tr>
<tr><td>engine</td><td>Fact extraction, triage, scan and edits</td><td>T14-T17</td></tr>
<tr><td>evals</td><td>Planted corpus, precision and recall, triage set, edit grounding</td><td>T9, T21-T24</td></tr>
</tbody></table></div>
<p class="note">Sessions share context through CLAUDE.md, docs/PLAN.md, docs/handoff.md and docs/data-notes.md. Ticks on this page save in your browser only, so progress for the team lives in PLAN.md.</p>
</section>

{''.join(ph_html)}

<section id="demo"><h2>Demo run of show (5 minutes)</h2><ol class="plain">{demo}</ol></section>
<section id="cut"><h2>Cut line</h2><p class="small">Drop in this order. The core slice (extract, triage, scan, report) is not negotiable.</p><ol class="plain">{cut}</ol></section>
<section id="risks"><h2>Risks</h2><ul class="plain">{risks}</ul></section>
<section id="decisions"><h2>Decisions still open</h2><ul class="plain">{dec}</ul></section>
</main>
<script>
(function(){{
  var boxes=[].slice.call(document.querySelectorAll('input[type=checkbox][data-k]'));
  var KEY='content-drift-plan-v1', saved={{}};
  try{{saved=JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch(e){{}}
  boxes.forEach(function(b){{ if(saved[b.dataset.k]) b.checked=true; }});
  function update(){{
    var n=boxes.filter(function(b){{return b.checked}}).length;
    document.getElementById('barfill').style.width=(100*n/boxes.length)+'%';
    document.getElementById('progtext').textContent=n+' of '+boxes.length+' tasks done';
  }}
  boxes.forEach(function(b){{ b.addEventListener('change',function(){{
    saved[b.dataset.k]=b.checked;
    try{{localStorage.setItem(KEY,JSON.stringify(saved))}}catch(e){{}}
    update();
  }}); }});
  update();
}})();
</script>"""
open(os.path.join(DOCS,'build-plan.html'),'w').write(plan)
print(total,[len(p[3]) for p in phases])
