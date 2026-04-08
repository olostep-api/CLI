---
name: migrate-code
description: Scrape a migration guide, changelog, or breaking changes document using Olostep and automatically update the user's local code. Use when the user is upgrading a framework, moving to a new API version, or says "help me migrate this code based on these docs".
---

# Olostep Migrate Code

Take the pain out of major version upgrades. Scrape the official migration guide, understand the breaking changes, and refactor the user's codebase automatically.

## When to use

- User provides a URL to a migration guide (e.g., React 18 to 19, Pages to App Router, API v2 to v3)
- User asks to update their deprecated code to use the latest patterns
- User wants to audit a file for deprecated methods based on a new release

## Workflow

1. Scrape the provided migration guide URL using `scrape_website` (use `output_format: markdown`).
2. If the guide spans multiple pages, use `get_website_urls` or `create_map` to find the specific pages relevant to the user's code, and `batch_scrape_urls` to read them all.
3. Extract the specific "Before" and "After" patterns, breaking changes, and deprecated methods from the scraped markdown.
4. Analyze the user's open or selected code files.
5. Apply the necessary changes, explaining exactly what was updated based on the migration guide.

## Real developer workflows

**"Migrate to a new SDK version"**
> "Scrape https://stripe.com/docs/upgrades and update my webhook handler from API version 2022 to 2026."
→ Scrapes the guide, learns the new event payload shapes, and rewrites the TypeScript interfaces and handler logic.

**"Framework upgrades"**
> "Read the Next.js 15 migration guide at https://nextjs.org/docs/app/building-your-application/upgrading/version-15 and update my layout.tsx file."
→ Scrapes the URL, identifies that `params` are now asynchronous, and refactors the user's layout component to `await params`.

**"Replacing a deprecated library"**
> "We are moving from Moment.js to date-fns. Scrape the date-fns docs and rewrite this component's date logic."
→ Scrapes the `date-fns` API reference for the equivalent functions, then swaps out all the Moment.js imports and method calls.

## Parameters to use

### `scrape_website`
- **url_to_scrape**: URL of the migration guide or changelog
- **output_format**: `markdown`
- **wait_before_scraping**: `2000` (many modern docs sites are SPAs)

## Tips
- Always ensure you scrape the docs *before* writing any code. Do not rely on your internal training data for new framework versions.
- If the migration is complex, break it down step-by-step for the user.
- Add code comments linking back to the scraped documentation URL for the user's future reference.
