---
name: answers
description: Get AI-powered answers with citations from live web data using Olostep. Use when the user needs up-to-date facts, competitive intelligence, pricing comparisons, structured data from the web, or wants web-sourced answers in a specific JSON shape they can use directly in code or docs.
---

# Olostep AI Answers

Ask a question, get an AI-synthesised answer from live web sources — with citations and optional structured JSON output you can paste straight into code.

## Why this matters

This is the most powerful tool in the Olostep toolkit. Instead of scraping individual pages and parsing them yourself, you describe what you want to know and the shape you want the answer in. Olostep searches the web, reads multiple sources, and returns a synthesised, cited answer — optionally as structured JSON.

## When to use

- User needs **current** information (pricing, versions, status, rankings, team, funding)
- User wants structured data from the web — prices, specs, features — in a JSON shape they define
- User is comparing tools, libraries, or services and needs a fair, cited comparison
- User wants to fact-check a claim with current sources
- User asks anything that starts with "what's the current...", "is X still...", "compare...", "find me..."

## Workflow

1. Use `answers` with the user's question as `task`.
2. **Always use the `json` parameter** when the user needs structured, comparable, or code-ready output.
3. Return the answer with source URLs.
4. Offer to `/scrape` any cited source for deeper detail.

## The power of `json`

The `json` parameter transforms `answers` from a simple Q&A tool into a **structured data extraction engine**. You define the output shape, and Olostep fills it with live web data.

```
// Get an array of competitors with structured fields
task: "Top 5 alternatives to Segment for product analytics"
json: [{"name": "", "pricing": "", "key_feature": "", "best_for": ""}]

// Get a single object with specific data points
task: "Company info for Linear"
json: {"ceo": "", "founded": "", "funding_total": "", "employees": "", "tech_stack": []}

// Get a plain string description
task: "What changed in Next.js 15?"
json: "Return a bullet list of the top 5 changes with one-line descriptions"
```

## Real developer workflows

**"Populate a comparison table in my app"**
> "Get the pricing for Vercel, Netlify, and Render — return as JSON I can use in my React component"
→ `answers` with `json: [{"provider": "", "free_tier": "", "pro_price": "", "key_limits": ""}]`
→ Returns a JSON array you can import directly into your code.

**"Is this library still maintained?"**
> "Is Zustand still actively maintained? What's the latest version and when was it released?"
→ `answers` with `json: {"maintained": true, "latest_version": "", "released": "", "weekly_downloads": ""}` → live npm/GitHub data with citations.

**"Get company data for my CRM"**
> "Find the CEO, founding year, employee count, and last funding round for Linear.app"
→ `answers` with structured schema → returns verified data with sources.

**"Compare before choosing a tool"**
> "Compare Prisma, Drizzle, and Kysely for TypeScript ORM — which should I pick for a serverless project?"
→ `answers` with `json: [{"orm": "", "pros": [], "cons": [], "serverless_fit": ""}]` → structured comparison you can reason about.

**"Research for a blog post"**
> "What are the most common mistakes developers make with React Server Components in 2026?"
→ `answers` returns a cited, synthesised answer aggregated from multiple blog posts and discussions.

**"Get live stats for a feature decision"**
> "How many developers use TypeScript vs JavaScript in 2026? What's the adoption rate?"
→ `answers` with `json: {"stat": "", "value": "", "source": "", "year": ""}` → cited data points.

**"Tech stack research"**
> "What tech stack does Figma use? I want to understand how they handle real-time collaboration."
→ `answers` aggregates from engineering blog posts, job postings, and conference talks → detailed technical breakdown.

## Chain with other skills

- **answers → scrape**: Get a quick answer with citations, then `/scrape` a cited source for the full page content.
- **answers → batch**: Research a topic, then `/batch` scrape all cited sources for comprehensive detail.
- **answers → code**: Get structured technical data, then use it to write code (e.g. comparison component, config file, feature matrix).

## Parameters
- **task**: Question or research task (required)
- **json**: Output shape for structured results (optional but highly recommended)
  - **Object**: `{"name": "", "price": "", "features": []}` — returns a filled object
  - **Array**: `[{"name": "", "price": ""}]` — returns a filled array
  - **String**: `"return a bullet list of the top 5 changes"` — returns formatted text

## Tips
- **Always use `json`** when the output needs to be structured, compared, or used in code — it's the killer feature
- Share citation URLs with the user so they can verify and explore further
- For deeper detail on any cited source, offer to `/scrape` it
- This replaces dozens of manual Google searches → use it liberally for any "current state of X" question
- Works great for: pricing, versions, status, team info, tech stacks, market data, tool comparisons
