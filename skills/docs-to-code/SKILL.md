---
name: docs-to-code
description: Scrape API documentation or library docs and use them to write working, up-to-date code. Use when the user wants to integrate a third-party API, learn a new library, generate SDK usage examples, write code based on a docs URL, or update code after a library version change. This is the flagship workflow — never hallucinate API parameters when you can scrape the real docs.
---

# Olostep Docs-to-Code

Turn any documentation URL into working, tested code. Scrape the real docs → understand the API surface → write the integration. Never guess parameters when the actual docs are one scrape away.

## Why this matters

AI models hallucinate API parameters, use deprecated methods, and miss breaking changes from new versions. This skill solves that — it scrapes the **actual, current docs** and writes code based on what's really there. The result is code that works on the first try.

## When to use

- User wants to integrate a third-party API and shares (or mentions) a docs URL
- User says "write me code using [library]" — especially if it's new, niche, or recently updated
- User wants examples for a library that shipped a new major version
- User wants to generate a typed client, SDK wrapper, or helper from an API reference
- User says "read the docs and write the code" or "use the latest docs"
- User wants to migrate code after a breaking change in a dependency

## Workflow

1. **Scrape the docs page**: `scrape_website` with `output_format: markdown`, `wait_before_scraping: 2000`.
2. **If docs span multiple pages**: Use `get_website_urls` or `create_map` to find sub-pages (auth, endpoints, types, errors), then scrape the relevant ones.
3. **For entire doc sites**: Use `create_crawl` with `max_pages: 15` to ingest a full docs section.
4. **Parse the API surface**: Extract endpoints, parameters (required vs optional), auth patterns, request/response shapes, error codes.
5. **Write the code**: Use **exactly** what's in the docs — don't guess, don't hallucinate. Include:
   - Correct imports and auth setup
   - TypeScript types derived from the docs' response shapes
   - Error handling for documented error codes
   - Working, copy-paste-ready examples
6. **Cite the source**: Link to the doc page you scraped so the user can verify.

## Real developer workflows

**"Integrate this API"**
> "Scrape https://docs.resend.com/api-reference/emails/send-email and write a Next.js API route that sends a welcome email"
→ Scrape the endpoint docs → extract auth header, payload shape (`from`, `to`, `subject`, `html`), response → write a typed `POST /api/send-welcome` handler.

**"Generate a typed client"**
> "Scrape the Anthropic messages API docs and write me a fully typed TypeScript client with streaming support and error handling"
→ Scrape API reference → extract endpoints, input/output types, error types → generate a `AnthropicClient` class with methods for each endpoint.

**"Learn a library and write examples"**
> "Crawl https://docs.upstash.com/redis and generate 5 practical examples for a Next.js app: cache a DB query, rate limit an API, session storage, pub/sub, and leaderboard"
→ Crawl 10–15 docs pages → extract commands and patterns → write 5 focused, working examples.

**"Implement a webhook handler"**
> "Scrape the Stripe webhook verification docs and write me a Next.js webhook handler for payment_intent.succeeded"
→ Scrape → extract signature verification logic → implement with `stripe.webhooks.constructEvent()` and proper error handling.

**"Migrate to a new version"**
> "Scrape the v4 migration guide at https://sdk.vercel.ai/docs/migration and update my code from v3"
→ Scrape migration guide → identify breaking changes → apply each change to the user's existing code → explain what changed and why.

**"Generate an OpenAPI-style reference"**
> "Scrape the Hono framework docs and generate a quick reference of all route methods, middleware, and context helpers"
→ Map docs → scrape relevant pages → extract the full API surface → present as a structured reference.

**"Write the auth flow"**
> "Scrape the Clerk docs for Next.js App Router and write the complete auth setup: middleware, sign-in page, protected routes, and user object access"
→ Scrape 3–4 relevant docs pages → write each piece with correct imports and configuration.

## Chain with other skills

- **map → scrape → code**: Map a docs site to find the right pages → scrape the specific reference pages → write code from them.
- **search → scrape → code**: Don't have the docs URL? Use `/search` to find it, then scrape and code.
- **crawl → code**: For full library learning, crawl the entire docs section → synthesise into working examples.

## Tips
- **Always scrape before writing** — never assume your training data has the current API surface
- If a user mentions a library version ("v5", "latest"), the docs have likely changed — scrape them
- For large APIs, use `/map` first to find the exact reference pages, then scrape those specifically
- Prefer specific **reference pages** over overview/guide pages — they have the exact parameters and types
- If auth is unclear from the endpoint docs, scrape the authentication/quickstart page separately
- Always include error handling based on documented error codes
- Link to the scraped doc page so the user can verify the code matches
