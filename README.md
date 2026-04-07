# Olostep CLI

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#installation)
[![npm](https://img.shields.io/badge/npm-olostep--cli-CB3837.svg)](https://www.npmjs.com/package/olostep-cli)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

Command-line interface for the [Olostep API](https://www.olostep.com/) — search, map, answer, scrape, crawl, and batch workflows from your terminal. Outputs are **structured JSON** (pretty-printed) so you can pipe them into `jq`, agents, and CI without writing a custom client first.

The same CLI is available as a **standalone binary** (no Python required) via [npm](https://www.npmjs.com/package/olostep-cli), or from source with Python.

---

## Table of contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Quick start](#quick-start)
- [Output, stdout, and agents](#output-stdout-and-agents)
- [Commands](#commands)
  - [`login`](#login--browser-auth)
  - [`map`](#map--discover-urls)
  - [`answer`](#answer--researched-answers)
  - [`scrape`](#scrape--single-url)
  - [`scrape-get`](#scrape-get--fetch-by-id)
  - [`crawl`](#crawl--multi-page)
  - [`batch-scrape`](#batch-scrape--csv)
  - [`batch-update`](#batch-update--metadata)
- [Default output paths](#default-output-paths)
- [Global options](#global-options)
- [Project structure](#project-structure)
- [Development](#development)
- [Security](#security)
- [References](#olostep-references)
- [License](#license)

---

## Installation

### npm (recommended — standalone binary)

Installs a platform-specific binary on `postinstall` (macOS arm64/x64, Linux x64, Windows x64). **Node.js 16+** is required only for install; the `olostep` command does not use Python.

```bash
npm install -g olostep-cli
```

Run without a global install:

```bash
npx -y olostep-cli@latest --help
```

If the binary failed to download, reinstall or check that a [GitHub release](https://github.com/olostep-api/CLI/releases) exists for your package version and platform.

### Python (from this repository)

For development or when you want to run the Typer app directly:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

The console script is `olostep`. You can also run `python main.py ...`.

Package metadata: see [`pyproject.toml`](pyproject.toml) (`olostep-api-cli`).

---

## Authentication

The CLI resolves your API key in this order:

1. Explicit `OLOSTEP_API_KEY` or `OLOSTEP_API_TOKEN` in the process environment  
2. A project **`.env`** next to the package (loaded with `setdefault`, so existing env wins)  
3. **`credentials.json`** in the per-user config directory (written by **`olostep login`** by default)

Config directory layout (override entirely with **`OLOSTEP_CLI_CONFIG_DIR`**):

| OS | Default directory |
| -- | ----------------- |
| macOS | `~/Library/Application Support/olostep-cli` |
| Windows | `%USERPROFILE%\AppData\Roaming\olostep-cli` |
| Linux / others | `~/.config/olostep-cli` |

The credentials file is `credentials.json` with `{"api_key": "..."}`.

| Variable | Description |
| -------- | ----------- |
| `OLOSTEP_API_KEY` | API key (preferred) |
| `OLOSTEP_API_TOKEN` | Alternative token name |
| `OLOSTEP_CLI_CONFIG_DIR` | Override the config directory (parent of `credentials.json`) |
| `OLOSTEP_API_BASE_URL` | API root for `login` and API calls (default: `https://api.olostep.com/v1`) |
| `OLOSTEP_CLI_AUTH_PAGE_URL` | Authorize page base for `olostep login` (overrides env-based default below) |
| `OLOSTEP_ENV` or `ENV` | Set to `development`, `dev`, or `local` to default the authorize link to `http://localhost:1660/cli-auth` (Next.js dev port). Otherwise the default is `https://www.olostep.com/cli-auth`. |

Create keys in the [Olostep API Keys dashboard](https://www.olostep.com/dashboard/api-keys), or run **`olostep login`** to sign in in the browser and store the key in **`credentials.json`**.

Batch commands resolve the token via `resolve_api_key()`; map/answer/scrape/crawl use the same credentials through [`config/config.py`](config/config.py). Defaults include `API_BASE_URL` (`https://api.olostep.com/v1`) and batch base URL — change there if you need another environment.

---

## Quick start

```bash
export OLOSTEP_API_KEY=your_key_here

olostep --help
olostep map "https://example.com" --top-n 20
olostep scrape "https://example.com" --formats markdown,html
```

---

## Output, stdout, and agents

- **`--out <path>`** — Write JSON results to a file. Parent directories are created automatically.
- **`--out -`** — Write **only** the JSON result to **stdout** (UTF-8, indented). Use this for pipelines, subprocess capture in agents, and tools that expect machine-readable output on stdout.
- **Logs** (e.g. `logger.info`, progress) go to **stderr**, so you can redirect or ignore them while keeping clean JSON on stdout.

Examples:

```bash
olostep map "https://example.com" --top-n 50 --out - | jq '.urls[:10]'
olostep answer "What is Olostep?" --out - | jq .result
olostep scrape "https://example.com" --out - | jq .result.markdown_content
```

CI-style usage:

```bash
export OLOSTEP_API_KEY="${{ secrets.OLOSTEP_API_KEY }}"
olostep scrape "https://docs.example.com" --out result.json
```

---

## Commands

Run `olostep <command> --help` for full option text. HTTP timeout for most API-backed commands: `--timeout` (seconds).

### `login` — browser auth

Opens the Olostep CLI authorize page (or prints the URL with `--no-browser`). After you sign in and click **Authorize**, the CLI polls `POST /status` and saves the key to **`credentials.json`** under the OS-specific config directory (see [Authentication](#authentication)). Use **`--env-file`** to write a project `.env` instead.

| Option | Description |
| ------ | ----------- |
| `--poll-seconds` | Interval between status polls (default: `3`) |
| `--timeout` | Max seconds to wait for authorization (default: `600`) |
| `--no-browser` | Print the authorize URL instead of opening a browser |
| `--env-file` | Write `OLOSTEP_API_KEY=` to this `.env` file instead of `credentials.json` |

Set `NO_BROWSER=1` in the environment for the same effect as `--no-browser` (useful over SSH).

```bash
olostep login
olostep login --no-browser   # copy the printed URL into a local browser
olostep login --env-file ./.env
```

---

### `map` — discover URLs

Map a site to discover URLs (Olostep Maps).

| Option | Description |
| ------ | ----------- |
| `--out` | Output path or `-` for stdout |
| `--top-n` | Max URLs to return |
| `--search-query` | Optional query to guide discovery |
| `--include-subdomain` / `--no-include-subdomain` | Include subdomains |
| `--include-url` | Repeatable URL patterns to include |
| `--exclude-url` | Repeatable URL patterns to exclude |
| `--cursor` | Pagination cursor |
| `--timeout` | HTTP timeout (s) |

```bash
olostep map "https://example.com" --top-n 100 --search-query "blog"
olostep map "https://example.com" --include-subdomain --out - | jq '.urls[:5]'
```

**Compatibility:** `--limit` was removed — use `--top-n`.

---

### `answer` — researched answers

Ask a question; the CLI polls until the answer job completes.

| Option | Description |
| ------ | ----------- |
| `--out` | Output path or `-` |
| `--json-format` | Optional JSON shape / schema hint (string or JSON object string) |
| `--poll-interval` | Polling interval (seconds) |
| `--poll-timeout` | Max time to wait (seconds) |
| `--timeout` | HTTP timeout (s) |

```bash
olostep answer "Summarize this company's product" --out output/answer.json
olostep answer "Extract company facts" --json-format '{"company":"","country":""}' --out -
```

**Compatibility:** `--model` was removed — use `--json-format`.

---

### `scrape` — single URL

Scrape one URL in one or more formats.

**Formats** (comma-separated): `html`, `markdown`, `text`, `json`, `raw_pdf`, `screenshot`.

| Option | Description |
| ------ | ----------- |
| `--out` | Output path or `-` |
| `--formats` | Comma-separated formats (default: `markdown`) |
| `--country` | Optional country code |
| `--wait-before-scraping` | Wait before scrape (milliseconds) |
| `--payload-json` | Advanced scrape options as a JSON **object** string |
| `--payload-file` | Same as above, from a JSON file (mutually exclusive with `--payload-json`) |
| `--timeout` | HTTP timeout (s) |

```bash
olostep scrape "https://example.com/article" --formats markdown,text
olostep scrape "https://example.com" --country US --wait-before-scraping 2000
olostep scrape "https://example.com" --payload-file advanced.json --out - | jq .
```

---

### `scrape-get` — fetch by ID

Retrieve a previous scrape by ID.

```bash
olostep scrape-get "scrape_abc123" --out output/scrape_get.json
olostep scrape-get "scrape_abc123" --out - | jq .result.markdown_content
```

---

### `crawl` — multi-page

Start a crawl, poll until finished, then retrieve page contents.

**Retrieve formats** (comma-separated): `markdown`, `html`, `json`.

| Option | Description |
| ------ | ----------- |
| `--out` | Output path or `-` |
| `--max-pages` | Maximum pages to crawl |
| `--max-depth` | Optional max depth |
| `--include-subdomain` / `--no-include-subdomain` | Subdomains |
| `--include-external` / `--no-include-external` | External domains |
| `--include-url` / `--exclude-url` | Repeatable path/URL patterns |
| `--search-query` / `--top-n` | Optional discovery filter and cap |
| `--webhook` | Optional webhook URL |
| `--crawl-timeout` | Crawl timeout (seconds) |
| `--follow-robots-txt` / `--ignore-robots-txt` | robots.txt |
| `--formats` | Retrieve formats |
| `--pages-limit` | Page size for crawl pages API |
| `--pages-search-query` | Filter when listing pages |
| `--poll-seconds` / `--poll-timeout` | Polling |
| `--timeout` | HTTP timeout (s) |
| `--dry-run` | Print API payload JSON and exit (no request) |

```bash
olostep crawl "https://docs.example.com" --max-pages 50 --formats markdown,html
olostep crawl "https://example.com" --max-pages 10 --dry-run
```

---

### `batch-scrape` — CSV

Submit many URLs from a CSV with columns **`custom_id`/`id`** and **`url`**. Polls until completion.

| Option | Description |
| ------ | ----------- |
| `--out` | Output path or `-` |
| `--formats` | `markdown`, `html`, `json` (comma-separated) |
| `--country` | Optional country code |
| `--parser-id` | Optional parser for structured extraction |
| `--poll-seconds` | Poll interval |
| `--log-every` | Log every N polls |
| `--items-limit` | Batch items page size (API often suggests 10–50) |
| `--dry-run` | Print payload JSON and exit |

```bash
olostep batch-scrape urls.csv --formats markdown,html --country US
olostep batch-scrape urls.csv --parser-id "<PARSER_ID>" --out results.json
```

---

### `batch-update` — metadata

Update metadata on an existing batch. **One of** `--metadata-json` or `--metadata-file` is required (JSON object).

```bash
olostep batch-update "batch_abc123" --metadata-json '{"team":"growth"}'
olostep batch-update "batch_abc123" --metadata-file meta.json --out -
```

---

## Default output paths

If you omit `--out`, JSON is written under `output/`:

| Command | Default file |
| ------- | ------------ |
| `map` | `output/map.json` |
| `answer` | `output/answer.json` |
| `scrape` | `output/scrape.json` |
| `scrape-get` | `output/scrape_get.json` |
| `crawl` | `output/crawl_results.json` |
| `batch-scrape` | `output/batch_results.json` |
| `batch-update` | `output/batch_update.json` |

---

## Global options

| Option | Description |
| ------ | ----------- |
| `-V`, `--version` | Print CLI version and exit |
| `-h`, `--help` | Help (Typer / Rich) |

---

## Project structure

```text
.
├── main.py                 # Typer CLI entrypoint
├── pyproject.toml          # Python package + `olostep` script
├── olostep.spec            # PyInstaller spec for release binaries
├── npm/
│   ├── package.json        # olostep-cli on npm
│   ├── bin/olostep.js      # Node shim → native binary
│   └── scripts/postinstall.js
├── config/
│   └── config.py           # Env, defaults, base URLs
├── src/
│   ├── api_client.py
│   ├── map_api.py
│   ├── answer_api.py
│   ├── scrape_api.py
│   ├── crawl_api.py
│   ├── batch_api.py
│   └── batch_scraper.py
└── utils/
    └── utils.py            # JSON output, stdout `-`, polling helpers
```

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[test]"
pytest
olostep --help
```

Release binaries are built with PyInstaller (`pip install -e ".[build]"`); see [`.github/workflows/release.yml`](.github/workflows/release.yml).

---

## Security

- Do not commit `.env` or API keys.
- Rotate keys if they are exposed.

---

## Olostep references

- [Olostep](https://www.olostep.com/)
- [Documentation](https://docs.olostep.com/)
- [Authentication](https://docs.olostep.com/get-started/authentication)
- [Maps](https://docs.olostep.com/features/maps/maps)
- [Batches](https://docs.olostep.com/features/batches/batches)
- [Parsers](https://docs.olostep.com/features/structured-content/parsers)

## License

MIT — see [`LICENSE`](LICENSE).
