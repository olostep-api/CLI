# Olostep API CLI

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#prerequisites)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

Command-line interface for the [Olostep API](https://www.olostep.com/). This package wraps common Olostep workflows like `map`, `answer`, `scrape`, `crawl`, `batch-scrape`, and `batch-update`, then writes the JSON responses to local files for debugging, automation, and downstream processing.

It follows the [Olostep documentation](https://docs.olostep.com/) and exposes a packaged `olostep` command through Typer.

---

## Table of Contents

- [Objective](#objective)
- [Prerequisites](#prerequisites)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Reference](#cli-reference)
- [Output Layout](#output-layout)
- [Project Structure](#project-structure)
- [Development](#development)
- [Security](#security)
- [Olostep References](#olostep-references)
- [License](#license)

---

## Objective

This project helps you:
- Run Olostep API workflows directly from the terminal.
- Save consistent JSON outputs under `output/`.
- Test map, answer, scrape, crawl, and batch flows without writing custom client code first.
- Reuse one CLI for quick experiments, local automation, and API debugging.

## Prerequisites

- Python 3.10+ installed locally.
- An [Olostep](https://www.olostep.com/) account with a valid API key or API token.
- `pip` or another Python package installer.

## Features

- `map`: Discover URLs from a site with [Olostep Maps](https://docs.olostep.com/features/maps/maps).
- `answer`: Create and poll Olostep Answers responses.
- `scrape`: Scrape a single URL in one or more formats.
- `scrape-get`: Fetch a scrape response by scrape ID.
- `crawl`: Crawl a site, poll until completion, list pages, and retrieve content.
- `batch-scrape`: Submit a CSV of URLs to [Olostep Batch](https://docs.olostep.com/features/batches/batches) and retrieve completed items.
- `batch-update`: Update metadata for an existing batch.

---

## Quick Start

Create and activate a virtual environment, then install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Create `.env` in the project root:

```bash
OLOSTEP_API_KEY=your_olostep_api_key_here
```

This repo also accepts `OLOSTEP_API_TOKEN`. You can create an API key from the [Olostep API Keys dashboard](https://www.olostep.com/dashboard/api-keys).

Run the CLI:

```bash
olostep --help
olostep map "https://example.com" --top-n 20 --out output/map.json
```

You can also run the same commands with `python main.py ...`.

---

## Configuration

The CLI loads credentials from `.env` or the process environment:

- `OLOSTEP_API_KEY`
- `OLOSTEP_API_TOKEN`

Runtime defaults live in `config/config.py`, including:

- `API_BASE_URL`
- `BATCH_BASE_URL`
- `DEFAULT_HTTP_TIMEOUT_S`
- `DEFAULT_*_OUT_PATH`
- Default polling intervals and output paths for each command

If you need to target a different environment, update `API_BASE_URL` or `BATCH_BASE_URL` in [config/config.py](/home/mubashir/RB/Olostep/olostep_cli/config/config.py).

---

## Usage

Map a site:

```bash
olostep map "https://example.com" --top-n 20 --out output/map.json
```

Create and poll an answer:

```bash
olostep answer "Summarize this company" --out output/answer.json
```

Create an answer with a JSON output shape:

```bash
olostep answer "Extract company facts" --json-format '{"company":"","country":""}' --out output/answer.json
```

Scrape one URL:

```bash
olostep scrape "https://example.com/article" --formats markdown,text --out output/scrape.json
```

Fetch an existing scrape:

```bash
olostep scrape-get "<SCRAPE_ID>" --out output/scrape_get.json
```

Crawl a site and retrieve page content:

```bash
olostep crawl "https://example.com" --max-pages 20 --formats markdown,html --out output/crawl_results.json
```

Batch scrape from CSV:

```bash
olostep batch-scrape "data.csv" --formats markdown,html --out output/batch_results.json
```

Batch scrape with a parser:

```bash
olostep batch-scrape "data.csv" --parser-id "<PARSER_ID>" --out output/batch_results.json
```

Update batch metadata:

```bash
olostep batch-update "<BATCH_ID>" --metadata-json '{"team":"growth"}' --out output/batch_update.json
```

---

## CLI Reference

Use `--help` on the root command or any subcommand:

```bash
olostep --help
olostep map --help
olostep answer --help
olostep scrape --help
olostep scrape-get --help
olostep crawl --help
olostep batch-scrape --help
olostep batch-update --help
```

Compatibility notes:
- `map --limit` was removed. Use `--top-n`.
- `answer --model` was removed. Use `--json-format`.

---

## Output Layout

Commands write JSON to `output/` by default:

- `output/map.json`
- `output/answer.json`
- `output/scrape.json`
- `output/scrape_get.json`
- `output/crawl_results.json`
- `output/batch_results.json`
- `output/batch_update.json`

---

## Project Structure

```text
.
├── main.py                # Typer CLI entrypoint and command definitions
├── pyproject.toml         # Package metadata and `olostep` console script
├── config/
│   └── config.py          # Environment loading, defaults, and base URLs
├── src/
│   ├── api_client.py      # Shared API client for map, answer, scrape, and crawl
│   ├── map_api.py         # Maps command implementation
│   ├── answer_api.py      # Answers command implementation
│   ├── scrape_api.py      # Scrape and scrape-get implementations
│   ├── crawl_api.py       # Crawl execution and page retrieval
│   ├── batch_api.py       # Batch scrape and batch update workflows
│   └── batch_scraper.py   # Low-level batch client
└── utils/
    └── utils.py           # JSON writing and polling helpers
```

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
olostep --help
```

---

## Security

- Do not commit `.env`.
- Treat API keys as secrets and rotate them if they are exposed.

---

## Olostep References

- [Olostep Website](https://www.olostep.com/)
- [Olostep Documentation](https://docs.olostep.com/)
- [Olostep Authentication Guide](https://docs.olostep.com/get-started/authentication)
- [Olostep Maps Guide](https://docs.olostep.com/features/maps/maps)
- [Olostep Batch Guide](https://docs.olostep.com/features/batches/batches)
- [Olostep Parsers Documentation](https://docs.olostep.com/features/structured-content/parsers)

## License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE).
