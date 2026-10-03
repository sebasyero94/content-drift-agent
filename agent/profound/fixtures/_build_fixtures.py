"""Writes the fixture JSON from responses copied out of the Profound MCP (2026-10-03).
Kept so the provenance is visible; the raw numbers below are verbatim MCP output (rounded to 5 dp)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
META = {"data_source": "cached", "fetched": "2026-10-03",
        "window": "2026-09-03..2026-10-02", "via": "Profound MCP (interactive OAuth)",
        "category_id": "9bbb7725-af0b-48e7-b6aa-929af4b5c869",
        "topic": "Session replay, experiments & feature flags"}
T = META["topic"]
# id, text, mixpanel visibility_score, average_position (get_visibility_report group_by prompt, assets=Mixpanel)
P = [
 ("a09d8bc0-461a-42b4-8a30-20ae04baff72","What are the best heatmap tools for web apps?",0.03333,4),
 ("2300ab3a-f5e1-4c11-9df7-6d3b75f8d1c2","What are the best experimentation platforms for a SaaS company?",0.23333,5.5625),
 ("0ccafb05-5092-4b0d-8132-1903f0113210","Are session replay tools legal and privacy compliant?",0,None),
 ("bc01e3e7-65fb-4ac7-b3d9-fb4c01d7d4c0","Standalone A/B testing tool vs experiments built into a product analytics platform: which should a 50-person startup choose?",0.6,3.91),
 ("6416931f-6672-482a-a12a-578a7e86cbe1","What are the best all-in-one tools for analytics, replay, experiments, and flags?",0.53333,3.02222),
 ("02c54a4a-fe21-46e0-9669-89ba97ce1313","What are the best session replay tools?",0,None),
 ("8de94090-2f5b-41eb-b256-b652531ec36b","What are the best free feature flag and experimentation tools for startups?",0.03333,2),
 ("f1795741-d73c-4ec9-9087-9e7a3c1b8b41","How long should an A/B test run?",0,None),
 ("403ff7ce-c7a7-4fb2-bdeb-61a8ad1c0099","How do I run an A/B test on a product feature?",0.3,9.25),
 ("7bef9804-776b-422e-8789-92e2241ab9c5","What are the best tools for analyzing session recordings with AI instead of watching them manually?",0.03333,4),
 ("2973c2ef-9cf7-48c5-b1ae-b2071fb9840c","What are the best tools for debugging UX issues with session replay?",0.03333,1),
 ("65414e9b-6faa-4ae2-aa18-a91908763b97","What are the best tools that combine product analytics and session replay?",0.43333,4.15),
 ("f8a4f63d-e135-4295-8dfa-a5d9fc13bd1f","What is the difference between an A/B test and a feature rollout?",0,None),
 ("fa97c00b-b55d-471d-94aa-4631defe1b6a","What are the best session replay tools that mask sensitive data for privacy compliance?",0,None),
 ("c3be360c-999b-44b4-999b-cf597eafe1b9","What are the best feature flag tools?",0,None),
 ("13369fa0-f22b-48aa-99e1-5a88c3dc5618","What do product teams say are the pros and cons of session replay tools?",0.13333,1.75),
 ("0ab30d82-c6b5-42b1-863e-43dc84b167e5","What are the best A/B testing tools with built-in statistical significance?",0.03333,8),
 ("fe875764-1a6b-4b5f-af54-e6e3d3531c89","What are the best session replay tools for mobile apps?",0.04167,3),
 ("8012aa9c-e7a6-4e7e-bbfa-d13ea39e9a97","Feature flags in a dedicated tool vs in my analytics platform: which is easier for engineers and PMs?",0.5,4.83333),
 ("db3dd27f-0d91-4999-8dc4-e0993ad98f81","What are the best tools for feature rollouts and kill switches?",0,None),
 ("3595f987-30fd-40de-b1d5-5218e422d408","What is a feature flag and why do teams use them?",0,None),
 ("6440d987-8222-420a-9a23-fe77b8ac56ff","How do I calculate sample size for a product experiment?",0,None),
 ("d2a9a208-1ebb-4131-8b1e-56aa48befffa","What is session replay and how do product teams use it?",0.21,3.66667),
 ("f8962c99-5c81-4381-b69f-17776cb5648e","What are the best A/B testing tools for product teams?",0.2,6.33333),
 ("3681e922-b7c3-4f31-a4d9-c1b1b4aeafc8","Session replay vs user interviews: which is better for finding onboarding friction?",0,None),
]
prompts = [{"id":i,"text":t,"topic":T,"mixpanel_visibility":v,"mixpanel_avg_position":p} for i,t,v,p in P]
json.dump({"_meta":META,"prompts":prompts}, open(os.path.join(HERE,"prompts.json"),"w"), indent=1)

# page-level citations per prompt: (page.name as returned, count, citation_share, citation_category)
C = {
"8de94090-2f5b-41eb-b256-b652531ec36b":[
 ("growthbook.io/insights/free-feature-flagging-tools",18,0.08660,"other"),
 ("configcat.com/blog/top-launchdarkly-alternatives/",28,0.07895,"other"),
 ("launchdarkly.com/blog/best-free-feature-flag-services/",20,0.06042,"other"),
 ("posthog.com/compare/best-open-source-feature-flag-tools",19,0.05692,"other"),
 ("abtesting.cc/blog/best-free-feature-flag-tools/",5,0.04902,"earned_media"),
 ("growthbook.io/insights/best-feature-flag-tools-for-developers",11,0.03787,"other"),
 ("flagshark.com/blog/open-source-feature-flag-tools-compared-2026/",3,0.02941,"other"),
 ("growthbook.io/blog/best-open-source-feature-flagging-tools-compared",6,0.02761,"other"),
 ("statsig.com/comparison/best-free-feature-flagging-tools",11,0.02678,"other"),
 ("toolradar.com/best/free/feature-flags",3,0.02174,"social"),
 ("kameleoon.com/blog/top-feature-flag-management-tools",7,0.02102,"other"),
 ("harness.io/blog/feature-flag-tools-compared-10-best-platforms-for-safer-releases",5,0.01857,"other")],
"02c54a4a-fe21-46e0-9669-89ba97ce1313":[
 ("learn.g2.com/best-session-replay-software",33,0.09462,"social"),
 ("quantummetric.com/blog/best-session-replay-tools-in-2026",22,0.08009,"other"),
 ("userpilot.com/blog/session-replay-tools/",16,0.06301,"other"),
 ("zapier.com/blog/best-session-replay-tools/",14,0.04617,"other"),
 ("rollbar.com/blog/session-replay-tools/",12,0.04452,"other"),
 ("koji.so/blog/best-session-replay-tools-2026",7,0.03865,"other"),
 ("artisangrowthstrategies.com/blog/best-session-replay-tools-2026",5,0.03493,"other"),
 ("motadata.com/blog/best-session-replay-software",9,0.03426,"other"),
 ("youtube.com/watch?v=mWo0SUX2yGs",6,0.02706,"social"),
 ("fullstory.com/platform/session-replay/",5,0.02185,"other"),
 ("docs.logrocket.com/docs/session-replay",4,0.01852,"other"),
 ("logrocket.com/products/session-replay",4,0.01852,"other")],
"65414e9b-6faa-4ae2-aa18-a91908763b97":[
 ("quantummetric.com/blog/best-session-replay-tools-in-2026",17,0.08621,"other"),
 ("userpilot.com/blog/session-replay-tools/",5,0.03798,"other"),
 ("artisangrowthstrategies.com/blog/best-session-replay-tools-2026",3,0.03655,"other"),
 ("openreplay.com/",9,0.03551,"other"),
 ("learn.g2.com/best-product-analytics-software",8,0.03273,"social"),
 ("motadata.com/blog/best-session-replay-software",8,0.03252,"other"),
 ("statsig.com/comparison/best-session-replay-tools",5,0.02882,"other"),
 ("newrelic.com/blog/observability/session-replay-tools",7,0.02759,"other"),
 ("youtube.com/watch?v=0PtM76cSX6k&vl=en",7,0.02749,"social"),
 ("amplitude.com/compare/best-fullstory-session-replay-alternatives",3,0.02632,"other"),
 ("amplitude.com/compare/best-product-analytics-tools",3,0.02632,"other"),
 ("pendo.io/pendo-blog/top-10-product-analytics-tools/",6,0.02439,"other")],
"6416931f-6672-482a-a12a-578a7e86cbe1":[
 ("statsig.com/comparison/best-session-replay-tools",21,0.07778,"other"),
 ("dupple.com/learn/best-product-analytics-tools",6,0.04545,"earned_media"),
 ("artisangrowthstrategies.com/blog/best-session-replay-tools-2026",5,0.04167,"other"),
 ("swetrix.com/blog/best-analytics-tools-ab-testing-feature-flags",13,0.04096,"other"),
 ("learn.g2.com/best-session-replay-software",11,0.04091,"social"),
 ("growthbook.io/insights/best-ab-testing-tools-with-feature-flags",9,0.02647,"other"),
 ("flagsmith.com/blog/product-experimentation-tools",8,0.02438,"other"),
 ("quantummetric.com/blog/best-session-replay-tools-in-2026",6,0.02247,"other"),
 ("youtube.com/watch?v=0PtM76cSX6k&vl=en",8,0.02184,"social"),
 ("amplitude.com/compare/best-product-analytics-tools",5,0.02098,"other"),
 ("amplitude.com/compare/best-ecommerce-analytics-tools",7,0.01745,"other"),
 ("pendo.io/pendo-blog/the-top-6-session-replay-tools/",7,0.01745,"other")],
"c3be360c-999b-44b4-999b-cf597eafe1b9":[
 ("configcat.com/blog/top-launchdarkly-alternatives/",33,0.08938,"other"),
 ("harness.io/blog/feature-flag-tools-compared-10-best-platforms-for-safer-releases",38,0.08587,"other"),
 ("dif.sh/blog/best-feature-flag-tools-2026/",9,0.07545,"other"),
 ("octopus.com/devops/feature-flags/feature-flag-tools/",10,0.05001,"other"),
 ("abtesting.cc/blog/best-feature-flag-tools/",4,0.03922,"earned_media"),
 ("ciopages.com/buyer-guides/feature-flag-management",5,0.03623,"other"),
 ("reddit.com/r/devops/comments/t9kdyg/what_feature_toggleflag_service_are_you_using/",6,0.03365,"social"),
 ("launchdarkly.com/blog/best-free-feature-flag-services/",5,0.03045,"other"),
 ("schematichq.com/blog/feature-flag-management-tools",7,0.03003,"other"),
 ("guideflow.com/blog/feature-flag-software",3,0.02941,"other"),
 ("stackfyi.com/guides/feature-flag-tools-launchdarkly-statsig-growthbook-unleash-2026",4,0.02899,"other"),
 ("kameleoon.com/blog/top-feature-flag-management-tools",12,0.02823,"other")],
"fe875764-1a6b-4b5f-af54-e6e3d3531c89":[
 ("userpilot.com/blog/session-replay-tools/",21,0.11340,"other"),
 ("quantummetric.com/blog/best-session-replay-tools-in-2026",14,0.07871,"other"),
 ("learn.g2.com/best-session-replay-software",20,0.07459,"social"),
 ("artisangrowthstrategies.com/blog/best-session-replay-tools-2026",7,0.06795,"other"),
 ("posthog.com/compare/best-mobile-app-session-replay-tools",9,0.04245,"other"),
 ("zapier.com/blog/best-session-replay-tools/",9,0.03709,"other"),
 ("uxcam.com/blog/session-replay-tools-for-mobile-apps/",8,0.03631,"other"),
 ("rollbar.com/blog/session-replay-tools/",7,0.03171,"other"),
 ("motadata.com/blog/best-session-replay-software",6,0.02648,"other"),
 ("posthog.com/compare/best-session-replay-tools",6,0.02638,"other"),
 ("youtube.com/watch?v=acJ5ZUlysQA",5,0.02410,"social"),
 ("fullstory.com/blog/mobile-analytics/",5,0.02381,"other")],
"8012aa9c-e7a6-4e7e-bbfa-d13ea39e9a97":[
 ("amplitude.com/compare/best-feature-flag-tools",14,0.11427,"other"),
 ("amplitude.com/compare/top-feature-flag-solutions-for-product-teams",8,0.07868,"other"),
 ("mixpanel.com/blog/feature-flagging/",6,0.04971,"owned"),
 ("featureflags.io/build-or-buy/",6,0.04971,"other"),
 ("launchdarkly.com/blog/what-are-feature-flags/",5,0.04330,"other"),
 ("ciopages.com/buyer-guides/feature-flag-management",4,0.03897,"other"),
 ("futurepicker.com/en/launchdarkly-vs-posthog-vs-flagsmith-vs-devcycle-feature-flags-2026/",3,0.03846,"earned_media"),
 ("statsig.com/glossary/feature-flagging-tools",3,0.03663,"other"),
 ("posthog.com/blog/best-feature-flag-software-for-developers",5,0.03608,"other"),
 ("developers.dev/tech-talk/the-engineering-decision-build-vs-buy-vs-open-source-for-enterprise-feature-flag-management.html",2,0.02564,"other"),
 ("schematichq.com/blog/feature-flag-management-tools",1,0.02381,"other"),
 ("reddit.com/r/SoftwareEngineering/comments/17o7rsj/to_feature_flag_or_to_not_feature_flag/",1,0.02381,"social")],
}
cites = {pid:[{"page":n,"count":c,"citation_share":s,"citation_category":k} for n,c,s,k in rows] for pid,rows in C.items()}
# topic-wide lookup of owned pages (page_filter): only mixpanel.com/pricing returned a row
owned = [{"page":"mixpanel.com/pricing/","count":30,"citation_share":0.00090,"citation_category":"owned","scope":"topic-wide, not per prompt"}]
no_rows = ["docs.mixpanel.com/docs/session-replay","seline.com/blog/mixpanel-pricing"]
json.dump({"_meta":dict(META,note="Top 12 pages per prompt (limit=12), by citation_share averaged per AI model. total pages per prompt were 67-105."),
           "by_prompt":cites,"owned_page_lookup":owned,"page_lookup_no_rows":no_rows},
          open(os.path.join(HERE,"citations.json"),"w"), indent=1)
print("ok", len(prompts), sum(len(v) for v in cites.values()))
