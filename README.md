# Pactus

Pactus is an MCP server that lets AI assistants parse ISO 20022 payment messages directly from chat. It currently supports `pacs.008.001.08` (FI-to-FI Customer Credit Transfer); `pacs.002`, `pain.001`, and `camt.053` are scaffolded for upcoming releases.

## Why this exists

SWIFT's cross-border CBPR+ programme is migrating bank-to-bank traffic from legacy MT messages to ISO 20022 XML, with full cutover by November 2027. Banks, fintechs, and integration teams need fast ways to inspect and debug ISO 20022 traffic during the transition. Pactus brings that capability into any MCP-compatible client.

## Status

Early development. One vertical slice (`pacs.008`) is production-quality; remaining message types are in progress. Not yet on PyPI.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) recommended

## Quick start

```bash
git clone https://github.com/deniskarlinsky/iso20022-mcp
cd iso20022-mcp
uv sync
uv run pytest
```

## Connecting to Claude Desktop

Add Pactus to your Claude Desktop config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pactus": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/iso20022-mcp", "pactus-mcp"]
    }
  }
}
```

Restart Claude Desktop. The Pactus tools will appear in the tools menu.

## Available tools

| Tool | Purpose |
|---|---|
| `ping` | Health check; returns service metadata. |
| `parse_pacs008` | Parse a `pacs.008.001.08` message into a typed `ParsedPacs008` model with group header and transactions. |

`parse_pacs008` returns a structured Pydantic model rather than a hand-rolled dict, so the LLM sees fields with their proper types (e.g. `Decimal` amounts, `datetime` timestamps). On parse or validation failure, the tool returns `{"error": "..."}` instead of raising.

Example of what an LLM sees back from `parse_pacs008`:

```json
{
  "group_header": {
    "message_id": "MSG-001",
    "creation_datetime": "2026-05-09T14:30:00",
    "number_of_transactions": 1,
    "settlement_method": "CLRG"
  },
  "transactions": [
    {
      "end_to_end_id": "E2E-001",
      "settlement_amount": {"value": "1250.00", "currency": "EUR"},
      "charge_bearer": "SHAR",
      "debtor": {"name": "Acme GmbH"},
      "debtor_agent": {"bicfi": "DEUTDEFF"},
      "creditor": {"name": "Globex SA"},
      "creditor_agent": {"bicfi": "BNPAFRPP"}
    }
  ]
}
```

## Architecture

Pactus uses a hexagonal layout: `pactus/core/` is pure business logic with no MCP awareness, `mcp_server.py` is a thin FastMCP wrapper, and the generated xsdata models live in `pactus/generated/` and never escape `parsers.py`. See [architecture.md](architecture.md) for the diagram.

## Development

```bash
uv run ruff check
uv run ruff format
uv run mypy
uv run pytest
```

The project targets `mypy --strict`.

## License

MIT
