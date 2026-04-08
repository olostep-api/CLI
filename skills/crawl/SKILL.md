---
name: crawl
description: Autonomously crawl an entire website by following links from a starting URL using Olostep. Use when the user wants to ingest an entire docs site, blog, knowledge base, or any multi-page site as context for coding, writing, analysis, or building a knowledge base.
---

# Olostep Crawl

Autonomously discover and scrape an entire website by following links from a start URL. Every page is rendered in a full browser with anti-bot bypass — perfect for ingesting docs, blogs, and knowledge bases.

## Why this matters

Manually collecting pages from a docs site is tedious and incomplete. Crawl does it automatically — it starts at a URL, follows links, renders every page (even JS-heavy ones), and returns clean content from each. You get an entire site's knowledge in one call.

## When to use

- User wants to learn a library by ingesting its complete docs
- User wants all blog posts or articles from a site as context
- User is preparing content for a RAG pipeline or knowledge base
- User wants to audit all pages across a site (content completeness, consistency, SEO)
- User wants a full picture of a competitor's documentation or marketing

## Workflow

1. Use `create_crawl` with the starting URL.
2. Set `max_pages: 10` by default — **always ask the user before going above 20**.
3. Set `follow_links: true` (default) to discover pages automatically.
4. Default to `markdown` — best for AI reasoning.
5. After crawling, **synthesise the collected content** — don't dump it raw.

## Real developer workflows

**"Learn this library from its docs"**
> "Crawl https://tanstack.com/query/latest/docs/overview and give me a cheat sheet of the key hooks, patterns, and gotchas"
→ Crawl 15–20 pages → synthesise into a concise reference with code snippets.

**"Generate working examples from docs"**
> "Crawl the Resend docs and write me 5 practical TypeScript examples: send email, send with template, add attachment, send to list, check delivery status"
→ Crawl → extract each endpoint's signature and parameters → write copy-paste-ready examples.

**"Build a knowledge base for my team"**
> "Crawl our internal docs at https://docs.internal.co and create a structured summary of every service, its owner, and its API endpoints"
→ Crawl 30–50 pages → extract service names, team ownership, endpoint lists → generate a services.json or markdown index.

**"Competitive docs analysis"**
> "Crawl https://docs.competitor.com/api and compare their API capabilities with ours — what do they have that we don't?"
→ Crawl → list all endpoints and features → compare against the user's API → identify gaps.

**"Content audit before a redesign"**
> "Crawl our marketing site and give me every page URL, its title, word count, and whether it has a CTA"
→ Crawl up to 50 pages → extract metadata from each → return as a structured table.

**"Prepare context for a refactor"**
> "Crawl our architecture docs and summarise the auth system before I refactor it"
→ Crawl → filter pages related to auth → extract design decisions, data flow, dependencies.

## Chain with other skills

- **map → crawl**: Use `/map` first to see all URLs, then `/crawl` a specific section. Avoids wasting crawl budget on irrelevant pages.
- **crawl → code**: Crawl the docs, then write complete integration code from the collected knowledge (see `/docs-to-code`).
- **crawl → batch**: If the crawl is too broad, use `/map` + `/batch` for more targeted extraction.

## Parameters
- **start_url**: Starting URL for the crawl (required)
- **max_pages**: Maximum pages to crawl — default 10, increase carefully (optional)
- **follow_links**: Whether to follow links on each page — default `true` (optional)
- **output_format**: `markdown` (default), `html`, `json`, `text`
- **country**: Country code for geo-targeted crawling — e.g. `US`, `GB` (optional)
- **parser**: Specialised parser ID for structured extraction (optional)

## Tips
- **Start small**: 10 pages is usually enough for a focused docs section. Ask before going to 50+.
- Always **synthesise** after crawling — generate a summary, cheat sheet, comparison, or structured data.
- Use `/map` first on large sites to understand the structure, then `/crawl` the relevant section.
- For a **known list** of URLs, `/batch` is better — it's parallel and you control exactly which pages to scrape.
- For a **single page**, just use `/scrape`.
