---
name: extract-schema
description: Scrape a webpage with Olostep and extract specific structured data matching a TypeScript interface, JSON schema, or database model. Use when the user wants to turn a website (like a product list, directory, or article) into clean, structured JSON or seed data.
---

# Olostep Extract Schema

Turn any unstructured webpage into perfectly formatted JSON or TypeScript objects. Scrape the site using Olostep's clean markdown extraction, then parse the data to match the user's exact schema.

## When to use

- User provides a URL and a TypeScript interface and says "Extract all the products on this page to match this interface."
- User wants to populate a database or create seed data from a real website.
- User is building a directory or aggregator and needs to scrape profiles, pricing, or features into a JSON file.
- User wants to convert an unstructured blog post or news article into a structured metadata object.

## Workflow

1. Review the TypeScript interface, JSON schema, or data shape requested by the user.
2. Scrape the target URL using `scrape_website` (always use `output_format: markdown` because it is highly optimized for LLM parsing).
3. If scraping multiple pages (like a list of profiles), use `batch_scrape_urls`.
4. Parse the extracted markdown content and map it strictly to the requested schema.
5. Output the result as a raw JSON code block, or write it directly to a `.json` or `.ts` file in the user's workspace if requested.

## Real developer workflows

**"Generate database seed data"**
> "Scrape this YC startup directory page and generate a JSON array matching my `Startup` Prisma schema: `{ name: string, description: string, batch: string, website: string }`. Write it to `seed.json`."
→ Scrapes the URL. Parses the clean markdown into the exact JSON shape. Creates the file.

**"Extract e-commerce products"**
> "Batch scrape these 5 Amazon product URLs and give me an array of objects with `title`, `price`, `rating`, and `inStock` boolean."
→ Runs a `batch` scrape. Extracts the fields for each product. Returns the structured array.

**"Parse article metadata"**
> "Scrape this news article and extract the `author`, `publishDate`, `mainTopics` (array of strings), and a 2-sentence `summary`."
→ Scrapes the article. Uses LLM reasoning to extract the fields. Returns the JSON.

## Parameters to use

### `scrape_website` or `batch_scrape_urls`
- **url_to_scrape** / **urls_to_scrape**: The target URL(s)
- **output_format**: `markdown` (Markdown is the best format for the LLM to read and extract schemas from)
- **wait_before_scraping**: `3000` (Crucial for e-commerce or directory sites that load data via client-side fetching)

## Tips
- Olostep's markdown format strips out all the HTML noise, making it incredibly easy and cheap for you (the AI) to extract fields accurately.
- If data is missing from the page, use `null` or omit the field as defined by the user's schema—do not hallucinate data.
- If the user wants to extract from many URLs, always route them to use `batch_scrape_urls` for speed.
