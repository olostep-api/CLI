# Olostep API CLI

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#requirements)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

CLI for the **Olostep API** covering: **map**, **answer**, **scrape**, **crawl**, **batch scrape**, and **batch update**.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Reference](#cli-reference)
- [Output Layout](#output-layout)
- [Development](#development)
- [Security](#security)
- [License](#license)

---

## Features

- **Map**: discover site URLs via `POST /v1/maps`
- **Answer**: create + poll answers via `POST /v1/answers` and `GET /v1/answers/{id}`
- **Scrape**: scrape a single URL via `POST /v1/scrapes` and fetch via `GET /v1/scrapes/{id}`
- **Crawl**: crawl site pages via `POST /v1/crawls`, poll via `GET /v1/crawls/{id}`, list pages via `GET /v1/crawls/{id}/pages`, then retrieve content via `GET /v1/retrieve`
- **Batch scrape**: create batch via `POST /v1/batches`, poll via `GET /v1/batches/{id}`, list items via `GET /v1/batches/{id}/items`, retrieve via `GET /v1/retrieve`
- **Batch update**: patch batch metadata via `PATCH /v1/batches/{id}`

## Requirements

- Python **3.10+**
- `pip`
- An Olostep API key

---

## Quick Start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### 2) Configure API key

Create `.env`:

```bash
OLOSTEP_API_KEY="YOUR_KEY"
# or
OLOSTEP_API_TOKEN="YOUR_KEY"
```

### 3) Run a command

```bash
python main.py --help
python main.py map "https://example.com" --top-n 20 --out output/map.json
```

---

## Configuration

### Environment variables

This project reads the Olostep API key from `.env`:

- `OLOSTEP_API_KEY` (optional): API key used for authentication
- `OLOSTEP_API_TOKEN` (optional): alternate API key variable name

Exactly one of them must be set.

### Code defaults (URLs and CLI defaults)

Defaults live in `config/config.py`:

- `API_BASE_URL`: Olostep API base (includes `/v1`)
- `BATCH_BASE_URL`: Olostep batch base (no `/v1`)
- `DEFAULT_HTTP_TIMEOUT_S`: HTTP timeout seconds
- `DEFAULT_*_OUT_PATH`: default output paths under `output/`

If you need to target a different environment, edit `API_BASE_URL` / `BATCH_BASE_URL` in `config/config.py`.

---

## Usage

```bash
# Map a site
python main.py map "https://example.com" --out output/map.json

# Create and poll an answer
python main.py answer "Summarize this company" --out output/answer.json

# Scrape a single URL
python main.py scrape "https://example.com/article" --out output/scrape.json

# Fetch a scrape by ID
python main.py scrape-get "<SCRAPE_ID>" --out output/scrape_get.json

# Crawl a site and retrieve content for each page
python main.py crawl "https://example.com" --max-pages 20 --out output/crawl_results.json

# Batch scrape from a CSV (header: custom_id,url OR id,url)
python main.py batch-scrape "data.csv" --formats markdown,html --out output/batch_results.json

# Update batch metadata
python main.py batch-update "<BATCH_ID>" --metadata-json '{"team":"growth"}' --out output/batch_update.json
```

---

## CLI Reference

The CLI is self-documented. Use `--help` for full arguments and defaults:

```bash
python main.py --help
python main.py crawl --help
python main.py map --help
python main.py answer --help
python main.py scrape --help
python main.py scrape-get --help
python main.py batch-scrape --help
python main.py batch-update --help
```

Legacy notes:
- `map --limit` was removed. Use `--top-n`.
- `answer --model` was removed. Use `--json-format`.

---

## Output Layout

Commands write JSON outputs under `output/` by default (see `DEFAULT_*_OUT_PATH` in `config/config.py`).

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -e .
python main.py --help
```

---

## Security

- Do not commit `.env`.
- Treat API keys as secrets (rotate if leaked).

---

## License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE).
