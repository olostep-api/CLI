---
name: debug-error
description: Search the web for a specific error message or bug using Olostep. Use when the user pastes an error stack trace, says their code is failing, or asks how to fix a bug that requires looking up recent GitHub issues, StackOverflow threads, or framework documentation.
---

# Olostep Debug Error

Turn obscure error messages into working fixes by searching the live web and scraping the actual solutions from GitHub issues, StackOverflow, or official docs.

## When to use

- User pastes a stack trace or terminal error and asks "how do I fix this?"
- User is facing a bug with a specific library version that the AI wasn't trained on
- User asks if there is an open GitHub issue for a bug they found
- User is stuck and standard debugging hasn't worked

## Workflow

1. Extract the core error message, framework, and version (if applicable) from the user's context.
2. Use `answers` with the query to search the live web for the error.
   *Example: "How to fix [exact error message] in [Framework name] v[Version]?"*
3. If the answer cites a specific GitHub issue or StackOverflow thread that looks promising, use `scrape_website` on that exact URL to read the full discussion and find the accepted solution or workaround.
4. Explain the root cause of the error based on the scraped context.
5. Provide the exact code fix or terminal commands the user needs to run to resolve the issue.

## Real developer workflows

**"Fix a weird build error"**
> "I'm getting 'Next.js 14 Error: x is not defined' when running npm run build. Help me fix it."
→ `answers` searches for the error. Finds a GitHub issue. → `scrape_website` reads the issue to find the maintainer's workaround. → Applies fix to user's code.

**"Find out if a bug is a known issue"**
> "My Supabase auth listener is firing twice on login. Is this a known bug?"
→ `answers` searches the Supabase repo for the bug. Returns the status of the issue and any community workarounds.

**"Resolve peer dependency conflicts"**
> "npm ERR! ERESOLVE unable to resolve dependency tree for React 19 and Framer Motion"
→ Searches for the specific compatibility issue. Scrapes the relevant PR or discussion. Advises on the correct version bump or `--legacy-peer-deps` flag.

## Parameters to use

### `answers`
- **task**: The exact error message and framework context.

### `scrape_website`
- **url_to_scrape**: The URL of the GitHub issue, forum thread, or docs page found via `answers`.
- **output_format**: `markdown`

## Tips
- Always prioritize scraping GitHub issues or official framework forums when debugging.
- Don't just paste the scraped text; translate the solution directly into a fix for the user's specific codebase.
- If an issue is marked as "open" with no fix, tell the user and suggest the most upvoted workaround.
