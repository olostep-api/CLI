---
name: search
description: Search the web using Olostep for live, up-to-date information. Three tools available — answers (AI-synthesised answers with citations), google_search (structured Google results), and get_website_urls (find pages within a specific site). Use when the user needs current data, comparisons, or facts the AI's training data may not have.
---

# Olostep Search

Search the live web and get answers, structured results, or find specific pages within a site. Three search tools for different needs.

## Why this matters

AI training data goes stale. When a user asks "which library is best" or "what does X cost" — they need **today's answer**, not last year's. Olostep searches the live web, synthesises answers with source citations, and can return structured JSON you can use directly in code.

## When to use

- User asks "what is the best X for Y" — needs live rankings, not stale training data
- User wants to compare tools, libraries, or services with current pricing
- User needs a fact that may have changed since the AI's cutoff (versions, status, pricing, team)
- User wants to find specific pages within a documentation site or company site
- User asks a question that starts with "is X still...", "what's the latest...", "has Y changed..."

## Which tool to use

| Need | Tool | Why |
|------|------|-----|
| Broad research question, comparison, fact-check | `answers` | AI-synthesised answer from multiple sources, with citations |
| Raw Google results (organic, PAA, knowledge graph) | `google_search` | Structured SERP data when you need the actual search results |
| Find pages within a specific site | `get_website_urls` | Ranked URLs from one domain, sorted by relevance to your query |

## Workflow

**For open research / comparisons / fact-checking:**
1. Use `answers` with the user's question as `task`.
2. If the result needs to be used in code, a table, or a comparison, pass a `json` schema.
3. Present the answer with source URLs — offer to `/scrape` any source for deeper detail.

**For raw Google search results:**
1. Use `google_search` with the query.
2. Returns structured organic results, knowledge graph, People Also Ask, related searches.
3. Use this when you need the actual URLs and snippets, not a synthesised answer.

**For finding pages within a specific site:**
1. Use `get_website_urls` with the site URL and search query.
2. Returns up to 100 URLs ranked by relevance.
3. Offer to `/scrape` the most relevant result for full content.

## Real developer workflows

**"Find the best library for this"**
> "What's the best React drag-and-drop library in 2026?"
→ `answers` with schema `[{"library": "", "stars": "", "bundle_size": "", "last_release": "", "verdict": ""}]` → structured comparison with live data.

**"What's the current price?"**
> "What do Vercel, Netlify, and Render charge for a Pro plan?"
→ `answers` with schema `[{"provider": "", "pro_price": "", "included": ""}]` → live pricing you can paste into a doc or comparison page.

**"Is this still maintained?"**
> "Is moment.js still maintained? What should I use instead?"
→ `answers` returns current status + recommended alternatives with sources.

**"Find the right docs page"**
> "Search the Supabase docs for row-level security examples"
→ `get_website_urls` on `https://supabase.com/docs` with query `"row level security"` → ranked URLs → scrape the top one.

**"Get raw search results for a competitive analysis"**
> "Google 'best headless CMS 2026' and give me the top 10 organic results"
→ `google_search` → structured list of titles, URLs, snippets, and any knowledge graph data.

**"Check current version / status"**
> "What's the latest version of Next.js and when was it released?"
→ `answers` → returns current version, release date, key changes, with source link.

## Chain with other skills

- **search → scrape**: Use `answers` or `google_search` to find URLs, then `/scrape` the best ones for full content.
- **search → docs-to-code**: Search for the docs URL, then use `/docs-to-code` workflow to write the integration.
- **search → batch**: Get a list of URLs from search results, then `/batch` scrape all of them.

## Parameters

### `answers` — AI-synthesised answers with citations
- **task**: Question or research task (required)
- **json**: Output schema for structured results (optional but powerful)
  - String: `"return an array with name, price, and pros for each option"`
  - Object: `{"name": "", "price": "", "pros": [], "cons": []}`

### `google_search` — Structured Google SERP results
- **query**: Search query (required)
- **country**: Country code for localised results, e.g. `US`, `GB` (default: `US`)

### `get_website_urls` — Find pages within a specific site
- **url**: Site to search within (required)
- **search_query**: What to find (required)

## Tips
- `answers` is the most powerful — it searches the web, reads sources, and returns a synthesised answer with citations
- The `json` param on `answers` lets you get data in a shape you can paste straight into code or a markdown table
- Use `google_search` when you need the raw SERP (organic results, PAA, knowledge graph) rather than a synthesised answer
- Use `get_website_urls` when the user already knows which site to search — it's faster and more precise than broad web search
- Always offer to `/scrape` cited URLs if the user wants deeper detail on any result
