---
name: integrate
description: Automatically integrate the Olostep SDK into the user's codebase. Analyzes the project, detects the language and framework, chooses the right integration pattern, installs the SDK, writes all the code, and verifies it works — with minimal prompting. Use when the user wants to add Olostep web scraping, search, or AI answers to their project.
argument-hint: "API-KEY"
---

# Olostep Self-Integrating Setup

Analyze the user's codebase, detect their stack, and write a complete, working Olostep integration — SDK installation, client setup, tool/route wiring, and verification — with minimal user input.

## When to use

- User says "integrate Olostep", "add Olostep to my project", "set up Olostep SDK", or "I want web scraping in my app"
- User runs `/olostep:integrate` with or without an API key
- User wants to add web search, scraping, crawling, or AI answers to an existing codebase
- User is migrating from another scraping provider (Firecrawl, Apify, Browserbase, ScrapingBee, etc.)

## Instructions

You are an expert Olostep integration engineer. You know every endpoint, every SDK method, every parameter, and every framework pattern. Your job is to get the user from zero to a working integration as fast as possible. Be opinionated — pick the best approach and run with it. Only ask the user a question when there is genuine ambiguity that affects the integration (e.g., two equally valid patterns).

### Phase 1 — Detect the codebase

Analyze the project to understand:

1. **Language**: Check for `package.json` (Node/TypeScript), `pyproject.toml` / `requirements.txt` / `setup.py` (Python), or both.
2. **Framework**: Detect from dependencies:
   - **Node/TS**: Next.js (`next`), Express (`express`), Fastify (`fastify`), Hono (`hono`), NestJS (`@nestjs/core`), Nuxt (`nuxt`), SvelteKit (`@sveltejs/kit`), Remix (`@remix-run/node`), Astro (`astro`)
   - **Python**: FastAPI (`fastapi`), Django (`django`), Flask (`flask`), Starlette (`starlette`), Litestar (`litestar`)
3. **AI/Agent frameworks**: LangChain (`langchain`), LangGraph (`langgraph`), CrewAI (`crewai`), Vercel AI SDK (`ai`), OpenAI SDK (`openai`), Anthropic SDK (`@anthropic-ai/sdk`), Google ADK (`google-adk`), Mastra (`mastra`), Haystack, AutoGen
4. **Existing Olostep usage**: Look for `olostep` in dependencies, `OLOSTEP_API_KEY` in `.env` files, existing imports of `olostep` or `Olostep`
5. **Project structure**: Where are API routes? Where are utilities/lib files? Where is the agent loop? Where are environment variables managed?

### Phase 2 — Choose the integration pattern

Based on detection, pick the best pattern. **Default to the most useful pattern for their stack** — don't ask unless two patterns are equally valid.

#### Decision tree

```
Is this a LangChain project?
  → Install `langchain-olostep`, wire tools into agent
Is this a CrewAI project?
  → Install `crewai-olostep`, add tools to agents
Is this a Mastra project?
  → Install `@olostep/mastra`, add tools to mastra config
Is this an AI agent app (Vercel AI SDK, OpenAI function calling, etc.)?
  → Install native SDK (`olostep`), create tools that wrap Olostep endpoints
Is this a web app with API routes (Next.js, Express, FastAPI, etc.)?
  → Install native SDK, create API route(s) for scraping/search
Is this a data pipeline / script?
  → Install native SDK, write the pipeline script
Is this a CLI or automation tool?
  → Install native SDK, add commands
Else (plain project, unclear):
  → Install native SDK, create a utility module, show usage examples
```

If the user's intent is unclear AND the codebase could go multiple ways, ask ONE question:
> "I see you're using [framework]. How do you want to use Olostep?"
> 1. **As an AI tool** — Give your AI agent the ability to search/scrape the web
> 2. **As API routes** — Expose scraping/search as API endpoints in your app
> 3. **As a data pipeline** — Batch scrape/crawl websites for data ingestion

### Phase 3 — API key setup

1. If the user passed an API key via `$ARGUMENTS`, use it.
2. If `OLOSTEP_API_KEY` already exists in `.env` or environment, use it.
3. Otherwise, ask: "What's your Olostep API key? Get one free at https://olostep.com/auth"

Store the key in the project's `.env` file as `OLOSTEP_API_KEY=<key>`. If there's no `.env`, create one (and add `.env` to `.gitignore` if not already there).

### Phase 4 — Install the SDK

Run the appropriate install command:

**Node.js / TypeScript:**
```bash
npm install olostep
# or for LangChain:
npm install langchain-olostep
# or for Mastra:
npm install @olostep/mastra
```

**Python:**
```bash
pip install olostep
# or for LangChain:
pip install langchain-olostep
# or for CrewAI:
pip install crewai-olostep
```

### Phase 5 — Write the integration code

Write idiomatic, production-ready code for the detected stack. Every integration must include:
- Client initialization with proper API key loading
- Error handling
- TypeScript types (if TS project)
- Comments linking to the relevant docs page

Below are the complete SDK references and framework-specific patterns to use.

---

## Olostep SDK Reference — Node.js / TypeScript

**Package**: `olostep` (npm) — https://docs.olostep.com/sdks/node-js

### Client initialization

```ts
import Olostep from 'olostep';

const client = new Olostep({ apiKey: process.env.OLOSTEP_API_KEY });
```

### Scrapes — extract content from any URL

```ts
import Olostep, { Format } from 'olostep';

// Simple scrape
const scrape = await client.scrapes.create('https://example.com');
console.log(scrape.markdown_content);

// With options
const scrape = await client.scrapes.create({
  url: 'https://example.com',
  formats: [Format.HTML, Format.MARKDOWN, Format.TEXT],
  waitBeforeScraping: 1000,
  removeImages: true,
});
console.log(scrape.html_content);
console.log(scrape.markdown_content);

// Get scrape by ID
const fetched = await client.scrapes.get(scrape.id);
```

**Parameters for `scrapes.create()`:**
- `url` (string, required) — URL to scrape
- `formats` (Format[], optional) — `Format.HTML`, `Format.MARKDOWN`, `Format.TEXT`, `Format.JSON`
- `waitBeforeScraping` (number, optional) — ms to wait for JS rendering (0–10000)
- `removeImages` (boolean, optional) — strip images
- `removeCssSelectors` (string | string[], optional) — CSS selectors to remove
- `country` (string | Country, optional) — geo-target: `'us'`, `'gb'`, `Country.DE`, etc.
- `parser` (object, optional) — `{ id: '@olostep/google-search' }` for structured extraction
- `llmExtract` (object, optional) — `{ schema: {...} }` or `{ prompt: '...' }` for LLM-powered extraction
- `actions` (array, optional) — browser actions: `{ type: 'wait', milliseconds: 2000 }`, `{ type: 'click', selector: '#btn' }`, `{ type: 'scroll', distance: 1000 }`, `{ type: 'fill_input', selector: '#search', value: 'query' }`
- `context` (object, optional) — `{ id: 'ctx_...' }` for custom cookies/auth

**Response fields:** `id`, `html_content`, `markdown_content`, `text_content`, `json_content`, `screenshot_hosted_url`, `html_hosted_url`, `markdown_hosted_url`, `json_hosted_url`, `text_hosted_url`, `links_on_page`, `page_metadata`

### Batches — scrape up to 10k URLs in parallel

```ts
// Simple
const batch = await client.batches.create([
  'https://example.com',
  'https://example.org',
]);

// With custom IDs
const batch = await client.batches.create([
  { url: 'https://example.com', customId: 'site-1' },
  { url: 'https://example.org', customId: 'site-2' },
]);

// Wait for completion
await batch.waitTillDone({ checkEveryNSecs: 5, timeoutSeconds: 120 });

// Get info
const info = await batch.info();

// Stream results
for await (const item of batch.items()) {
  console.log(item.customId, item.url);
}
```

### Crawls — crawl entire websites

```ts
const crawl = await client.crawls.create({
  url: 'https://example.com',
  maxPages: 100,
  maxDepth: 3,
  includeUrls: ['*/blog/*'],
  excludeUrls: ['*/admin/*'],
});

await crawl.waitTillDone({ checkEveryNSecs: 10, timeoutSeconds: 300 });

const info = await crawl.info();

for await (const page of crawl.pages()) {
  console.log(page.url, page.status_code);
}
```

### Maps — discover all URLs on a site

```ts
const map = await client.maps.create({
  url: 'https://example.com',
  topN: 100,
  includeSubdomain: true,
  searchQuery: 'blog posts',
});

for await (const url of map.urls()) {
  console.log(url);
}
```

### Answers — AI-powered web search with structured output

> **Note**: The `answers` namespace is not yet in the Node.js SDK (`0.1.2`). Call the REST API directly:

```ts
// Simple question
const response = await fetch('https://api.olostep.com/v1/answers', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${process.env.OLOSTEP_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ task: 'What is the pricing of Stripe?' }),
});
const answer = await response.json();
console.log(answer.result); // string when no json param

// With JSON schema for structured output
const response2 = await fetch('https://api.olostep.com/v1/answers', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${process.env.OLOSTEP_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    task: 'What is the latest book by J.K. Rowling?',
    json: { book_title: '', author: '', release_date: '' },
  }),
});
const answer2 = await response2.json();
// answer2.result.json_content → '{"book_title":"...","author":"...","release_date":"..."}'
// answer2.result.sources → ['https://...', ...]
```

### Content retrieval

```ts
import { Format } from 'olostep';
const content = await client.retrieve(retrieveId, Format.MARKDOWN);
console.log(content.markdown_content);
```

### Advanced — geographic scraping

```ts
import Olostep, { Country } from 'olostep';
const scrape = await client.scrapes.create({
  url: 'https://example.com',
  country: Country.DE, // or any string like 'jp'
});
```

### Advanced — browser actions

```ts
const scrape = await client.scrapes.create({
  url: 'https://example.com',
  actions: [
    { type: 'wait', milliseconds: 2000 },
    { type: 'click', selector: '#load-more' },
    { type: 'scroll', distance: 1000 },
    { type: 'fill_input', selector: '#search', value: 'query' },
  ],
});
```

### Advanced — LLM extraction

```ts
import Olostep, { Format } from 'olostep';

// With a JSON schema
const scrape = await client.scrapes.create({
  url: 'https://example.com/product',
  formats: [Format.JSON],
  llmExtract: {
    schema: {
      title: { type: 'string' },
      price: { type: 'number' },
      description: { type: 'string' },
    },
  },
});
console.log(scrape.json_content);

// With a natural language prompt
const scrape2 = await client.scrapes.create({
  url: 'https://example.com/events',
  formats: [Format.JSON],
  llmExtract: {
    prompt: 'Extract all event names, dates, and venues from this page',
  },
});
```

### Client configuration

```ts
const client = new Olostep({
  apiKey: process.env.OLOSTEP_API_KEY!,
  timeoutMs: 150000,    // request timeout (default 150s)
  retry: {
    maxRetries: 3,
    initialDelayMs: 1000,
  },
});
```

---

## Olostep SDK Reference — Python

**Package**: `olostep` (PyPI, Python 3.11+) — https://docs.olostep.com/sdks/python

### Sync client

```python
from olostep import Olostep

client = Olostep(api_key="your-api-key")  # or uses OLOSTEP_API_KEY env var
```

### Async client (recommended for production)

```python
from olostep import AsyncOlostep

async with AsyncOlostep(api_key="your-api-key") as client:
    result = await client.scrapes.create(url_to_scrape="https://example.com")
```

### Scrapes

```python
# Simple
result = client.scrapes.create(url_to_scrape="https://example.com")
print(result.html_content)
print(result.markdown_content)

# With options (strings)
result = client.scrapes.create(
    url_to_scrape="https://example.com",
    formats=["html", "markdown"],
    wait_before_scraping=2000,
    country="us",
)

# With typed enums (better IDE support)
from olostep import Format, Country
result = client.scrapes.create(
    url_to_scrape="https://example.com",
    formats=[Format.HTML, Format.MARKDOWN],
    wait_before_scraping=2000,
    country=Country.US,
)
```

### Batches

```python
batch = client.batches.create(
    urls=["https://example.com", "https://example.org"]
)
for item in batch.items():
    content = item.retrieve(["html"])
    print(f"Processed {item.url}: {len(content.html_content)} bytes")
```

### Crawls

```python
crawl = client.crawls.create(
    start_url="https://example.com",
    max_pages=100,
    include_urls=["/blog/**"],
    exclude_urls=["/admin/**"],
    include_external=False,
    include_subdomain=True,
)
for page in crawl.pages():
    content = page.retrieve(["html"])
    print(f"Crawled: {page.url}")
```

### Maps

```python
maps = client.maps.create(url="https://example.com")
for url in maps.urls():
    print(url)
```

### Answers

```python
# Simple question
answer = client.answers.create(task="What is the capital of France?")
print(answer.answer)    # parsed dict: {'result': 'Paris'}
print(answer.sources)   # list of source URLs

# Structured output with JSON format
answer = client.answers.create(
    task="What is the latest book by J.K. Rowling?",
    json_format={"book_title": "", "author": "", "release_date": ""},
)
parsed = answer.answer  # {'book_title': '...', 'author': '...', 'release_date': '...'}
print(answer.sources)   # ['https://...', ...]

# Retrieve a previous answer by ID
previous = client.answers.get(answer_id=answer.id)
```

### Advanced — browser actions

The Python SDK exports typed action classes for better IDE support and validation:

```python
from olostep import WaitAction, ClickAction, FillInputAction, ScrollAction

result = client.scrapes.create(
    url_to_scrape="https://example.com",
    actions=[
        WaitAction(milliseconds=2000),
        ClickAction(selector="#load-more"),
        ScrollAction(direction="down", amount=1000),
        FillInputAction(selector="#search", value="query"),
    ],
)
```

You can also use raw dicts (same as the REST API):
```python
result = client.scrapes.create(
    url_to_scrape="https://example.com",
    actions=[
        {"type": "wait", "milliseconds": 2000},
        {"type": "click", "selector": "#load-more"},
        {"type": "scroll", "direction": "down", "amount": 1000},
        {"type": "fill_input", "selector": "#search", "value": "query"},
    ],
)
```

### Advanced — LLM extraction

The Python SDK exports a typed `LLMExtract` class for schema-based extraction:

```python
from olostep import LLMExtract

# With a JSON schema (typed class)
result = client.scrapes.create(
    url_to_scrape="https://example.com/product",
    formats=["json"],
    llm_extract=LLMExtract(schema={
        "title": {"type": "string"},
        "price": {"type": "number"},
        "description": {"type": "string"},
    }),
)
print(result.json_content)

# With a natural language prompt (raw dict — LLMExtract class only supports schema)
result = client.scrapes.create(
    url_to_scrape="https://example.com/events",
    formats=["json"],
    llm_extract={
        "prompt": "Extract all event names, dates, and venues from this page"
    },
)
```

### Error handling

```python
from olostep import Olostep, Olostep_BaseError

try:
    result = client.scrapes.create(url_to_scrape="https://example.com")
except Olostep_BaseError as e:
    print(f"Olostep error: {type(e).__name__}: {e}")
```

### Retry strategy

```python
from olostep import Olostep, RetryStrategy

client = Olostep(
    api_key="your-api-key",
    retry_strategy=RetryStrategy(max_retries=3, initial_delay=1.0),
)
```

---

## Olostep REST API Reference (for raw HTTP integrations)

**Base URL**: `https://api.olostep.com/v1`
**Auth**: `Authorization: Bearer <API_KEY>`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/scrapes` | Scrape a single URL |
| GET | `/v1/scrapes/:id` | Get scrape result |
| POST | `/v1/batches` | Start a batch (up to 10k URLs) |
| GET | `/v1/batches` | List all batches |
| GET | `/v1/batches/:id` | Get batch status |
| GET | `/v1/batches/:id/items` | Get batch results |
| POST | `/v1/crawls` | Start a crawl |
| GET | `/v1/crawls/:id` | Get crawl status |
| GET | `/v1/crawls/:id/pages` | Get crawled pages |
| POST | `/v1/maps` | Map a website's URLs |
| POST | `/v1/answers` | Get AI-powered answers |
| GET | `/v1/answers/:id` | Get answer result |
| GET | `/v1/retrieve` | Retrieve content by ID |

---

## Pre-built parsers

For structured JSON extraction from popular sites, use the `parser` parameter:

- `@olostep/google-search` — Google SERP results
- `@olostep/amazon-it-product` — Amazon product data
- `@olostep/extract-emails` — Extract email addresses
- `@olostep/extract-calendars` — Extract calendar events
- `@olostep/extract-socials` — Extract social media links

More parsers available via the dashboard: https://www.olostep.com/dashboard/parsers

---

## Framework-specific integration patterns

### Next.js (App Router) + Vercel AI SDK

Create `lib/olostep.ts`:
```ts
import Olostep from 'olostep';

export const olostep = new Olostep({
  apiKey: process.env.OLOSTEP_API_KEY!,
});
```

Create a tool for the AI SDK in the chat route (e.g., `app/api/chat/route.ts`):
```ts
import { olostep } from '@/lib/olostep';
import { tool } from 'ai';
import { z } from 'zod';

export const webSearchTool = tool({
  description: 'Search the web and get AI-powered answers with sources',
  parameters: z.object({
    query: z.string().describe('The search query'),
  }),
  execute: async ({ query }) => {
    // answers is not yet in the Node SDK — call REST API directly
    const res = await fetch('https://api.olostep.com/v1/answers', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.OLOSTEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task: query }),
    });
    return res.json();
  },
});

export const scrapeTool = tool({
  description: 'Scrape a webpage and get its content as markdown',
  parameters: z.object({
    url: z.string().url().describe('The URL to scrape'),
  }),
  execute: async ({ url }) => {
    const result = await olostep.scrapes.create(url);
    return result.markdown_content;
  },
});
```

### Express.js API routes

```ts
import Olostep from 'olostep';
import express from 'express';

const olostep = new Olostep({ apiKey: process.env.OLOSTEP_API_KEY! });
const router = express.Router();

router.post('/scrape', async (req, res) => {
  try {
    const { url, format = 'markdown' } = req.body;
    const result = await olostep.scrapes.create({ url, formats: [format] });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: 'Scrape failed' });
  }
});

router.post('/search', async (req, res) => {
  try {
    const { query, json } = req.body;
    const response = await fetch('https://api.olostep.com/v1/answers', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.OLOSTEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task: query, ...(json && { json }) }),
    });
    const result = await response.json();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: 'Search failed' });
  }
});

export default router;
```

### FastAPI (Python)

```python
from fastapi import FastAPI, HTTPException
from olostep import AsyncOlostep
from contextlib import asynccontextmanager

olostep_client: AsyncOlostep | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global olostep_client
    olostep_client = AsyncOlostep()  # reads OLOSTEP_API_KEY from env
    yield
    if olostep_client:
        await olostep_client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/scrape")
async def scrape(url: str, format: str = "markdown"):
    result = await olostep_client.scrapes.create(
        url_to_scrape=url, formats=[format]
    )
    return {"content": result.markdown_content}

@app.post("/search")
async def search(query: str):
    result = await olostep_client.answers.create(task=query)
    return result
```

### LangChain (Python)

```python
from langchain_olostep import (
    scrape_website,
    answer_question,
    scrape_batch,
    crawl_website,
    map_website,
)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI

tools = [scrape_website, answer_question, scrape_batch, crawl_website, map_website]

llm = ChatOpenAI(model="gpt-4o")
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

### LangChain (TypeScript)

```ts
import { OlostepScrape, OlostepAnswer, OlostepBatch, OlostepCrawl, OlostepMap } from 'langchain-olostep';

const tools = [
  new OlostepScrape(),
  new OlostepAnswer(),
  new OlostepBatch(),
  new OlostepCrawl(),
  new OlostepMap(),
];
```

### CrewAI

```python
from crewai import Agent, Task, Crew
from crewai_olostep import (
    olostep_scrape_tool,
    olostep_answer_tool,
    olostep_batch_tool,
    olostep_crawl_tool,
    olostep_map_tool,
)

researcher = Agent(
    role="Web Researcher",
    goal="Find accurate, current information from the web",
    backstory="Expert researcher with web scraping capabilities.",
    tools=[olostep_scrape_tool, olostep_answer_tool],
    verbose=True,
)

task = Task(
    description="Research the pricing of Stripe vs Square vs PayPal",
    expected_output="Comparison table with pricing tiers",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

### OpenAI function calling (direct)

```ts
import Olostep from 'olostep';
import OpenAI from 'openai';

const olostep = new Olostep({ apiKey: process.env.OLOSTEP_API_KEY! });
const openai = new OpenAI();

const tools: OpenAI.ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'web_search',
      description: 'Search the web and return answers with sources',
      parameters: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
        },
        required: ['query'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'scrape_url',
      description: 'Extract content from a webpage as markdown',
      parameters: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'URL to scrape' },
        },
        required: ['url'],
      },
    },
  },
];

// In your tool handler:
async function handleToolCall(name: string, args: Record<string, string>) {
  if (name === 'web_search') {
    // answers is not yet in the Node SDK — call REST API directly
    const res = await fetch('https://api.olostep.com/v1/answers', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.OLOSTEP_API_KEY!}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task: args.query }),
    });
    return res.json();
  }
  if (name === 'scrape_url') {
    const result = await olostep.scrapes.create(args.url);
    return result.markdown_content;
  }
}
```

### Data pipeline / script (Python)

```python
from olostep import Olostep

client = Olostep()  # reads OLOSTEP_API_KEY from env

# Step 1: Map the site to find URLs
site_map = client.maps.create(url="https://example.com", top_n=500)
urls = [url for url in site_map.urls()]

# Step 2: Batch scrape all URLs
batch = client.batches.create(urls=urls)
for item in batch.items():
    content = item.retrieve(["markdown"])
    print(f"Scraped: {item.url} — {len(content.markdown_content)} chars")

# Step 3: Get AI answers from the data
answer = client.answers.create(
    task="Summarize the key products from this website",
    json={"products": [{"name": "", "description": "", "price": ""}]},
)
print(answer)
```

---

## MCP Server integration

If the user is also using Cursor, set up the MCP server config alongside the SDK integration.

Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "olostep": {
      "command": "npx",
      "args": ["-y", "olostep-mcp"],
      "env": {
        "OLOSTEP_API_KEY": "<API_KEY>"
      }
    }
  }
}
```

MCP tools available: `scrape_website`, `get_webpage_content`, `search_web`, `google_search`, `answers`, `batch_scrape_urls`, `create_crawl`, `create_map`, `get_website_urls`.

---

## Phase 6 — Verify the integration

After writing all code:

1. Run the install command (`npm install` / `pip install`) if not already done.
2. Run a quick test — use the Olostep MCP tools to scrape a simple URL (like `https://example.com`) to verify the API key works.
3. Show the user a summary of what was created:
   - Files created or modified
   - SDK installed
   - Environment variable set
   - What they can do next
4. Suggest next steps:
   - "Try calling the Olostep scrape endpoint to test"
   - "Run your app and test the new API route / tool"
   - "Check out `/scrape`, `/search`, and `/research` for ad-hoc web data"

## Migration from other providers

If the user is migrating from another scraping API:

| From | Migration notes |
|------|----------------|
| **Firecrawl** | `FirecrawlApp.scrape_url()` → `client.scrapes.create()`, `FirecrawlApp.crawl_url()` → `client.crawls.create()`, `FirecrawlApp.map_url()` → `client.maps.create()` |
| **Apify** | Replace Actor runs with Olostep endpoints. `ApifyClient.actor().call()` → `client.scrapes.create()` or `client.batches.create()` |
| **ScrapingBee** | Replace `ScrapingBeeClient.get()` → `client.scrapes.create()` with `waitBeforeScraping` for JS rendering |
| **Browserbase** | Replace session-based scraping → `client.scrapes.create()` with `actions` for interaction |

## Tips
- For JS-heavy sites (SPAs, React apps), always use `waitBeforeScraping: 2000` or higher
- Use `answers` for quick web search — it's 1 call instead of search + scrape + parse
- Use `batches` instead of looping `scrapes` when you have >5 URLs — it's faster and cheaper
- Use `maps` before `crawls` to understand site structure first
- For e-commerce/SERP, use pre-built parsers for clean JSON instead of markdown
- Always handle errors — the SDK throws `Olostep_BaseError` (Python) or rejects the promise (Node)
- Set up retry strategy for production: `RetryStrategy(max_retries=3)` in Python, or wrap in try/catch with backoff in Node

## Links
- Get your API key: https://olostep.com/auth
- Node.js SDK docs: https://docs.olostep.com/sdks/node-js
- Python SDK docs: https://docs.olostep.com/sdks/python
- API Reference: https://docs.olostep.com/api-reference/scrapes/create
- Features overview: https://docs.olostep.com/get-started/welcome
- MCP Server: https://github.com/olostep/olostep-mcp-server
- LangChain integration: https://docs.olostep.com/integrations/langchain
- CrewAI integration: https://docs.olostep.com/integrations/crewai
- Parsers list: https://docs.olostep.com/features/structured-content/parsers
