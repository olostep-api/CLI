---
name: research
description: Do thorough, cited web research to help the user make a decision. Compare tools, libraries, or services. Evaluate competitors. Research tech stacks, market data, or architecture patterns. Use when the user needs a well-sourced answer before making a technical, product, or business decision.
---

# Olostep Research

Do thorough, multi-source web research and present findings as structured, actionable intelligence. This is the skill for when the user needs to make a decision and wants real data — not opinions from stale training data.

## Why this matters

Developers and product teams make dozens of "which tool should we use?" and "should we build or buy?" decisions. These decisions are expensive to get wrong. This skill uses live web data to give cited, structured, current answers — not guesses from training data that may be 6+ months old.

## When to use

- User is choosing between tools, libraries, frameworks, or services
- User wants to understand competitors' features, pricing, positioning, or tech stack
- User is evaluating build vs buy for a component
- User needs market data, adoption stats, or trend information
- User wants to fact-check a technical claim or marketing statement
- User says "help me decide", "what should I use", "compare X vs Y", "is X worth it"

## Research methodology

1. **Quick answer**: Use `answers` with a `json` schema for structured, cited results.
2. **Deep dive**: Scrape the most relevant sources (`scrape_website`) for full detail.
3. **Multi-site comparison**: Batch scrape competitors' pricing/features/docs pages.
4. **Site-specific research**: Use `get_website_urls` to find relevant pages within a specific site.
5. **Synthesise and recommend**: Present findings as a table, structured JSON, or clear recommendation — **always end with a recommendation**, don't just list facts.

## Real developer workflows

**"Help me pick a tool"**
> "Compare Prisma, Drizzle, and Kysely for a serverless TypeScript API. Which should I use?"
→ `answers` with `json: [{"orm": "", "pros": [], "cons": [], "serverless_fit": "", "bundle_size": "", "learning_curve": ""}]` → structured comparison → clear recommendation based on the user's serverless constraint.

**"Competitive intelligence"**
> "I'm building a Firecrawl alternative. What do Firecrawl, Apify, and Browserbase offer, what do they charge, and where are the gaps?"
→ `answers` for broad overview → `batch_scrape_urls` on each competitor's pricing + features pages → detailed comparison with gap analysis → actionable insights.

**"Build vs buy"**
> "Should I build my own auth system or use Clerk/Auth0/Supabase Auth? What are the trade-offs for a B2B SaaS with SSO?"
→ `answers` with schema covering cost, SSO support, migration difficulty, vendor lock-in → scrape each service's SSO docs for detail → recommendation.

**"Is this production-ready?"**
> "Is Bun production-ready in 2026? I want to replace Node in our API."
→ `answers` aggregates: GitHub activity, open issues, community sentiment, production case studies → returns a structured risk assessment.

**"Tech stack deep dive"**
> "What stack does Figma use for real-time collaboration? I'm building something similar."
→ `answers` → finds relevant engineering blog posts → `scrape_website` on the blog posts → detailed technical breakdown of their architecture.

**"Market sizing"**
> "How many developers use Tailwind CSS? I'm deciding whether to build a Tailwind component library."
→ `answers` with `json: [{"stat": "", "value": "", "source": "", "date": ""}]` → cited data points for npm downloads, GitHub stars, survey results.

**"Vendor evaluation"**
> "We're choosing a vector database. Compare Pinecone, Weaviate, Qdrant, and Milvus for a RAG pipeline with 10M documents."
→ `answers` for capabilities overview → `batch_scrape_urls` on each vendor's pricing page → synthesised comparison with our scale requirements.

**"Architecture research"**
> "How do companies like Vercel and Netlify handle serverless function cold starts? What techniques should I use?"
→ `answers` + scrape relevant engineering blog posts → extract patterns, techniques, benchmarks → summarise with code-applicable recommendations.

## Chain with other skills

- **research → scrape**: Get the quick answer, then scrape cited sources for full detail.
- **research → batch**: Compare multiple competitors by batch scraping their key pages.
- **research → docs-to-code**: Research which library to use, then use `/docs-to-code` to integrate it.
- **research → crawl**: For deep technical research, crawl an entire engineering blog or docs site.

## Parameters

### Core tool: `answers`
- **task**: Research question — be specific and include constraints (required)
- **json**: Output schema — structure the answer so it's directly usable (strongly recommended)

### Supporting tools (for deep dives)
- `scrape_website`: Read a specific source in full
- `batch_scrape_urls`: Compare multiple sites side-by-side (pricing, features, docs)
- `get_website_urls`: Find specific pages within a site (e.g. competitor's pricing page)
- `google_search`: Get raw SERP results when you need to discover sources first

## Tips
- **Always use a `json` schema** — structured output makes comparisons fair and useful
- **Always end with a recommendation** — users want a decision, not just a list of facts
- For competitive research, **scrape actual pricing/features pages** — `answers` gives good overviews but may miss fine print
- Share citation URLs so users can verify and explore deeper
- For "is X ready" questions, look for: GitHub commit activity, open issue count, production usage testimonials, latest release date
- Use `country` on scrape/batch when comparing regional pricing or availability
