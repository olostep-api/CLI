---
name: map
description: Discover and list all URLs on a website using Olostep. Use when the user wants to see what pages exist on a site, find specific sections (docs, blog, API reference), audit a site's structure, or get a URL list to feed into batch or crawl.
---

# Olostep Map

Discover every URL on a website instantly. The essential reconnaissance step before scraping, crawling, or batch processing.

## Why this matters

You can't scrape what you can't find. Map gives you a complete inventory of every page on a site — filtered by keyword, narrowed by URL pattern — so you know exactly what's there before spending crawl or batch credits.

## When to use

- User wants to know what pages exist on a site before committing to a scrape or crawl
- User wants to find specific sections: all blog posts, all API reference pages, all pricing pages
- User wants to understand a site's structure and content organisation
- User needs a URL list to feed into `/batch` or `/crawl`
- User says "find all the pages about X on this site"

## Workflow

1. Use `create_map` with the website URL.
2. Use `search_query` to rank/filter URLs by relevance to a keyword.
3. Use `include_url_patterns` / `exclude_url_patterns` to narrow by path structure.
4. Use `top_n` to limit results if the site is very large.
5. Group URLs by section (e.g. `/docs/`, `/blog/`, `/api/`) when presenting results.
6. **Always suggest a next step**: scrape one URL, batch scrape a subset, or crawl a section.

## Real developer workflows

**"Find the right docs page"**
> "Map https://docs.stripe.com and find all pages about webhooks"
→ `create_map` with `search_query: "webhooks"` → returns webhook-related URLs ranked by relevance → user picks the best one → `/scrape` it.

**"Discover all blog posts"**
> "Map https://vercel.com/blog and list all blog posts"
→ Map with `include_url_patterns: ["/blog/**"]` → returns all blog post URLs → offer to `/batch` scrape for content analysis.

**"Understand a competitor's site"**
> "Map https://competitor.com and tell me what sections they have"
→ Map the site → group URLs by path segment (`/docs/`, `/pricing/`, `/blog/`, `/changelog/`) → summarise content focus areas.

**"Find all API reference pages"**
> "Map https://docs.openai.com and list only the API reference pages, not the guides"
→ `include_url_patterns: ["/api-reference/**"]`, `exclude_url_patterns: ["/guides/**"]` → clean list of reference pages only.

**"Plan before crawling"**
> "I want to scrape the entire Tailwind CSS docs. Map it first so I know what I'm dealing with."
→ Map → see 120 URLs across `/docs/`, `/blog/`, `/showcase/` → user picks just `/docs/` → feed those into `/batch` or `/crawl`.

**"Audit our own site"**
> "Map our marketing site and count how many pages we have per section"
→ Map → group by path → count per section → surface any orphaned or unexpected pages.

## Chain with other skills

- **map → batch**: The most powerful combo. Map a site → filter to the URLs you care about → batch scrape them all. Best for known sites with lots of pages.
- **map → crawl**: Map first to understand structure, then crawl a specific section with `start_url` set to that section's root.
- **map → scrape**: Map to find the exact right page, then scrape just that one.

## Parameters
- **website_url**: URL to map (required)
- **search_query**: Keyword to rank/filter URLs by relevance (optional but very useful)
- **top_n**: Max number of URLs to return (optional — useful for large sites)
- **include_url_patterns**: Glob patterns to include — e.g. `["/blog/**", "/docs/**"]` (optional)
- **exclude_url_patterns**: Glob patterns to exclude — e.g. `["/admin/**", "/internal/**"]` (optional)

## Tips
- **Always suggest a next step**: map alone isn't useful — the value is in what you do with the URLs (scrape, batch, crawl)
- `search_query` is powerful — it ranks all URLs by how relevant they are to your keyword, so the best pages float to the top
- Use `include_url_patterns` / `exclude_url_patterns` to be surgical — e.g. include only `/docs/api/**` and exclude `/docs/legacy/**`
- For very large sites (1000+ pages), use `top_n: 50` to keep results manageable
- This is faster than crawling — it discovers URLs without downloading page content
