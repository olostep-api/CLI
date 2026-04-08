---
name: batch
description: Scrape up to 10,000 URLs in parallel using Olostep. Use when the user has a list of URLs to extract content from at once — product pages, job listings, pricing pages, changelogs, docs, or any set of known pages. Much faster than scraping one-by-one.
---

# Olostep Batch Scrape

Scrape up to 10,000 URLs in parallel. All pages are scraped concurrently with full browser rendering, anti-bot bypass, and residential proxies — no rate limiting, no blocking, no setup.

## Why this matters

Scraping 50 pages sequentially takes minutes and often fails halfway through (rate limits, CAPTCHAs, IP bans). Olostep batch processes them all in parallel through its browser infrastructure — you get every page back, fully rendered, in seconds.

## When to use

- User has 3+ URLs they want content from (don't scrape them one-by-one)
- User has a list from `/map` and wants to pull content from matching pages
- User wants to compare multiple competitor pages, product pages, or pricing pages side-by-side
- User needs to build a dataset from a list of known URLs
- User wants to audit, analyse, or extract patterns across many pages

## Workflow

1. Collect URLs from the user (or from a previous `/map` result).
2. Build the array: `[{"url": "...", "custom_id": "competitor-1"}, ...]`.
3. Call `batch_scrape_urls` with the array.
4. Use `custom_id` on each URL so you can match results back to the source.
5. Default to `markdown`. Use `json` + `parser` for structured product data.
6. After batch completes, **synthesise across all results** — compare, extract patterns, build tables, generate code.

## Real developer workflows

**"Compare competitor pricing pages"**
> "Batch scrape the pricing pages of Vercel, Netlify, Render, Railway, and Fly.io — extract each plan name, price, and key limits"
→ Batch 5 URLs with `custom_id` per competitor → extract pricing into a comparison table.

**"Build a product dataset from Amazon"**
> "Here are 30 Amazon product URLs — scrape them all and extract name, price, rating, and review count"
→ Batch with `parser: "@olostep/amazon-product"` → get clean structured JSON for every product.

**"Audit all docs pages for completeness"**
> "I mapped our docs site and got 45 URLs. Batch scrape all of them and tell me which pages are missing code examples"
→ `/map` first → feed URLs into `batch` → scan each page's content for code blocks → report gaps.

**"Extract every job listing"**
> "Scrape all 20 of these job posting URLs and give me a table of: title, company, salary range, required skills, location"
→ Batch all listings → extract fields from each → return as a markdown table or JSON array.

**"Dependency changelog audit"**
> "Scrape the changelogs for these 12 npm packages and flag any breaking changes in their latest major releases"
→ Batch all changelog URLs → scan for "BREAKING", "removed", "deprecated" → report per package.

**"Conference speaker research"**
> "Batch scrape these 20 speaker profile pages and extract name, company, talk title, and bio"
→ Batch with `custom_id` per speaker → extract structured profiles → generate a speakers.json file.

**"Geo-targeted pricing comparison"**
> "Scrape this SaaS pricing page from US, UK, and Germany to see if prices differ by region"
→ Three batch calls with `country: "US"`, `country: "GB"`, `country: "DE"` → compare results.

## Chain with other skills

- **map → batch**: The most powerful combo. `/map` discovers all URLs on a site, you filter to the ones you need, then `/batch` scrapes them all. Perfect for docs sites, blogs, product catalogs.
- **search → batch**: Use `/search` to find relevant URLs, then `/batch` scrape all results for full content.
- **batch → code**: Batch scrape API docs pages, then generate typed clients or integration code from the combined content.

## Parameters
- **urls_to_scrape**: Array of `{url, custom_id?}` objects, 1–10,000 (required)
- **output_format**: `markdown` (default), `html`, `json`, `text`
- **wait_before_scraping**: ms to wait per URL for JS rendering, 0–10000 (optional)
- **country**: Country code for geo-targeted content — e.g. `US`, `GB`, `DE` (optional)
- **parser**: Specialised parser e.g. `@olostep/amazon-product` (optional)

## Tips
- **Always use `custom_id`** — it makes matching results to sources trivial (e.g. `"custom_id": "vercel-pricing"`)
- For 1–2 URLs, use `/scrape`. For 3+, always use `/batch` — it's parallel and faster
- Combine with `/map` for the most powerful pattern: discover → filter → batch scrape → synthesise
- The `country` param routes through residential proxies in that country — great for comparing regional content
- Always synthesise across results (tables, comparisons, summaries) — don't dump raw content
