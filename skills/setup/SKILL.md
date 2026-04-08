---
name: setup
description: Configure the Olostep API key so the MCP server and all Olostep skills work correctly. Use when the user is setting up Olostep for the first time, has no API key configured, or is getting authentication errors.
---

# Olostep Setup

Get the Olostep MCP server running in Cursor so all Olostep skills work.

## Steps

1. **Get an API key**: If the user doesn't have one, direct them to https://olostep.com/auth — sign up is free and takes 30 seconds. The free tier includes 100 credits/month.

2. **Configure the MCP server**: Add the following to `.cursor/mcp.json` in the project root (or go to Cursor Settings → Features → MCP Servers → Add New):

```json
{
  "mcpServers": {
    "olostep": {
      "command": "npx",
      "args": ["-y", "olostep-mcp"],
      "env": {
        "OLOSTEP_API_KEY": "<their-api-key>"
      }
    }
  }
}
```

3. **Verify it works**: Suggest the user tries a simple test:
   - `/scrape` a URL to confirm scraping works
   - `/search` a question to confirm answers works

## Troubleshooting

- **"401 Unauthorized"**: The API key is missing or invalid. Check it at https://olostep.com/auth.
- **"npx not found"**: Node.js is not installed. Install it from https://nodejs.org.
- **Tools not appearing**: Restart Cursor after adding the MCP config. Check Settings → Features → MCP to confirm the server is listed and running.
- **Stale npx cache**: If tools seem outdated, run `npx clear-npx-cache` in a terminal, then restart Cursor.

## What you get

Once configured, all Olostep skills are available:
- `/scrape` — Extract content from any URL (JS rendering + anti-bot bypass built in)
- `/search` — AI-powered web search with structured JSON output
- `/batch` — Scrape up to 10,000 URLs in parallel
- `/crawl` — Autonomously ingest entire websites
- `/map` — Discover all URLs on a site
- `/answers` — Get cited, structured answers from live web data
- `/docs-to-code` — Turn documentation into working code
- `/research` — Deep web research for technical and product decisions

## Links
- Get your API key: https://olostep.com/auth
- Documentation: https://docs.olostep.com
- MCP server on npm: https://www.npmjs.com/package/olostep-mcp
- GitHub: https://github.com/olostep/olostep-mcp-server
