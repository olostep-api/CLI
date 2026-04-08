---
name: scrape
description: Scrape a single webpage and extract its content as clean markdown, HTML, JSON, or text using Olostep. Use when the user shares a URL and wants to read it, extract content from it, understand its structure, use it as context for coding, or turn a page into data. Handles JavaScript-rendered pages, SPAs, and bot-protected sites automatically.
---

# Olostep Scrape

Extract clean, LLM-ready content from any URL - including JavaScript-heavy SPAs, bot-protected sites, and geo-restricted pages. No Puppeteer, no proxy config, no CAPTCHA solving - Olostep handles it all.

## Why this matters

Most scraping fails on modern sites: JavaScript doesn't render, CAPTCHAs block you, content varies by country. Olostep runs a full browser with residential proxies and anti-bot bypass built in. You get the exact content a real user sees, in the format you need.

## When to use

- User pastes a URL and says "read this", "summarise this", "use this as context"
- User wants to pull content from a docs page to write code against that API
- User wants to extract structured data from a product page, job listing, or pricing page
- User needs page content from a JS-heavy SPA (React, Next.js, Vue) that raw HTTP can't reach
- User wants geo-specific content (e.g. UK pricing vs US pricing)

## Workflow

1. Use `scrape_website` with the URL.
2. Default to `output_format: markdown` - cleanest for AI reasoning and code generation.
3. For JS-heavy pages (React, Next.js, Vue, Svelte apps), set `wait_before_scraping: 3000` to let the page fully render.
4. For structured product data, use `output_format: json` with a `parser` (e.g. `@olostep/amazon-product`).
5. For geo-targeted content, set `country` (e.g. `GB` for UK pricing, `DE` for German content).
6. After scraping, **act on the content** - write code from it, extract fields, summarise, compare.

## Real developer workflows

**"Read the docs and write the integration"**
> "Scrape https://docs.stripe.com/api/payment_intents and write me a TypeScript function to create a payment intent"
-> Scrape with `markdown` -> parse the endpoint spec -> write a typed function with error handling.

**"What changed in this release?"**
> "Scrape https://github.com/vercel/next.js/releases and tell me what breaking changes are in the latest version"
-> Scrape the releases page -> extract version notes -> flag breaking changes relevant to the user's stack.

**"Get product data from Amazon"**
> "Scrape this Amazon product page and extract the price, rating, and feature bullets"
-> Use `parser: "@olostep/amazon-product"` with `output_format: json` -> get clean structured data instantly.

**"See what users in the UK see"**
> "Scrape https://example.com/pricing with country GB and tell me the UK pricing"
-> Set `country: "GB"` -> request goes through a UK residential proxy -> get the exact page UK users see.

**"Read a JS-heavy SPA"**
> "Scrape this React dashboard at https://app.example.com/public/stats"
-> Set `wait_before_scraping: 5000` -> Olostep's browser waits for React to hydrate -> returns the fully rendered content.

**"Pull a job listing for my cover letter"**
> "Scrape this job posting and write a cover letter paragraph highlighting the matching skills from my resume"
-> Scrape the listing -> extract requirements and qualifications -> generate tailored content.

## Chain with other skills

- **scrape -> code**: Scrape docs, then write an integration (see `/docs-to-code`).
- **map -> scrape**: Use `/map` to find the right page, then scrape it.
- **search -> scrape**: Use `/search` to find relevant URLs, then scrape the best one for full content.
- **scrape -> batch**: Scrape one page to confirm format, then `/batch` the rest.

## Parameters
- **url_to_scrape**: URL to scrape (required)
- **output_format**: `markdown` (default), `html`, `json`, `text`
- **wait_before_scraping**: ms to wait for JS rendering, 0-10000 (use 3000-5000 for SPAs)
- **country**: Country code for geo-targeted content - e.g. `US`, `GB`, `DE`, `JP`, `BR`
- **parser**: Specialised parser for structured extraction - e.g. `@olostep/amazon-product`

## Tips
- Always **act on** the scraped content - don't just return raw markdown to the user
- For JS-heavy pages, `wait_before_scraping: 3000` is usually enough; use 5000 for very slow SPAs
- The `country` parameter routes through residential proxies - use it for pricing, localised content, or region-locked pages
- If you need 3+ URLs, switch to `/batch` - it's parallel and faster
- If you need an entire site, use `/crawl` instead
