# Olostep CLI Tests

This directory contains tests for the Olostep CLI, organized into **unit tests** (no API key needed) and **integration tests** (hit the real Olostep API).

## Setup

```bash
cd CLI
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

Set your API key for integration tests:

```bash
export OLOSTEP_API_KEY="your_api_key_here"
```

Or create a `.env` file in the CLI root:

```
OLOSTEP_API_KEY=your_api_key_here
```

## Running Tests

```bash
# Run all unit tests (no API key needed)
pytest tests/unit/

# Run all integration tests (requires API key, consumes credits)
pytest tests/integration/ -m integration

# Run all tests
pytest

# Run a specific test file
pytest tests/unit/test_scrape_api.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov=config --cov=utils
```

## Test Structure

### Unit Tests (`tests/unit/`)

| File | What it tests |
|---|---|
| `test_config.py` | `.env` loading, `Settings`, `resolve_api_key`, `get_batch_base_url` |
| `test_scrape_api.py` | `parse_scrape_formats`, `build_scrape_payload`, `load_payload_object` |
| `test_crawl_api.py` | `parse_crawl_retrieve_formats`, `build_crawl_payload` |
| `test_batch_api.py` | `parse_retrieve_formats`, `read_csv_items`, `normalize_batch_metadata`, `parse_metadata_object` |
| `test_utils.py` | `write_json`, `poll` (with async) |
| `test_cli.py` | CLI argument parsing and validation via Typer `CliRunner` (mocked API) |

### Integration Tests (`tests/integration/`)

| File | What it tests |
|---|---|
| `test_scrape.py` | Scrape creation (markdown, multi-format, country), scrape-get by ID |
| `test_map.py` | Map creation (basic, search query, include/exclude URL filters) |
| `test_answer.py` | Answer creation (basic, with `json_format` schema) |
| `test_crawl.py` | Crawl creation (basic, depth limit, URL filters, multi-format retrieve) |

## Notes

- **Unit tests** never hit the network — they test pure functions and use mocks for CLI commands.
- **Integration tests** make real API calls and **will consume credits**.
- Integration tests are marked with `@pytest.mark.integration` so you can skip them with `-m "not integration"`.
- Crawl and answer tests use longer timeouts since they involve polling.
