# Pactus

[![CI](https://github.com/deniskarlinsky/iso20022-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/deniskarlinsky/iso20022-mcp/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/pactus-mcp.svg)](https://pypi.org/project/pactus-mcp/)

Pactus is an MCP server for parsing and validating ISO 20022 payment messages directly from chat. It exposes nine tools that let AI assistants inspect or validate `pacs.008`, `pacs.002`, `pain.001`, and `camt.053` messages — the message types at the centre of the CBPR+ migration — without leaving the conversation. It is aimed at developers and bank-integration teams who need to read, debug, or explain ISO 20022 traffic during the transition away from MT messages.

## Status

```bash
pip install pactus-mcp
# or
uv add pactus-mcp
```

## Quick start

```bash
git clone https://github.com/deniskarlinsky/iso20022-mcp
cd iso20022-mcp
uv sync
uv run pytest
```

## Connecting to Claude Desktop

Install via uvx for zero-setup use, or run from a local checkout for development.

Add Pactus to your Claude Desktop config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### From PyPI (recommended)

```json
{
  "mcpServers": {
    "pactus": {
      "command": "uvx",
      "args": ["pactus-mcp"]
    }
  }
}
```

### From a local clone (for development)

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

| Tool | Message type | Purpose |
|---|---|---|
| `ping` | — | Health check; returns service name and version. |
| `parse_pacs008` | `pacs.008.001.08` | Parse a FI-to-FI Customer Credit Transfer. |
| `parse_pacs002` | `pacs.002.001.10` | Parse a FI-to-FI Payment Status Report. |
| `parse_pain001` | `pain.001.001.09` | Parse a Customer Credit Transfer Initiation. |
| `parse_camt053` | `camt.053.001.08` | Parse a Bank-to-Customer Account Statement. |
| `validate_pacs008` | `pacs.008.001.08` | Validate a FI-to-FI Customer Credit Transfer against its XSD. |
| `validate_pacs002` | `pacs.002.001.10` | Validate a FI-to-FI Payment Status Report against its XSD. |
| `validate_pain001` | `pain.001.001.09` | Validate a Customer Credit Transfer Initiation against its XSD. |
| `validate_camt053` | `camt.053.001.08` | Validate a Bank-to-Customer Account Statement against its XSD. |

The four parse tools return a structured Pydantic model on success, or `{"error": "..."}` on failure. The four validate tools return a `ValidationReport` listing every XSD violation with line, column, and path information — even when there are multiple errors. All tools never raise; the agent can explain what went wrong.

## Tool reference

### parse_pacs008

`pacs.008` is the primary interbank credit transfer message and the mandatory format for all CBPR+ cross-border traffic from November 2025. It carries one or more credit transfer instructions between financial institutions, each with settlement amount, charge bearer, debtor, and creditor agents.

<details>
<summary>Example response</summary>

```json
{
  "group_header": {
    "message_id": "MSG20240508001",
    "creation_datetime": "2024-05-08T10:00:00",
    "number_of_transactions": 1,
    "settlement_method": "CLRG"
  },
  "transactions": [
    {
      "end_to_end_id": "E2E20240508001",
      "transaction_id": "TX20240508001",
      "settlement_amount": {"value": "1000.00", "currency": "USD"},
      "charge_bearer": "SHAR",
      "debtor": {"name": "Acme Corporation"},
      "debtor_agent": {"bic": "CHASUS33"},
      "creditor": {"name": "Global Supplies Ltd"},
      "creditor_agent": {"bic": "DEUTDEDB"}
    }
  ]
}
```

</details>

### parse_pacs002

`pacs.002` is the status report sent in response to a `pacs.008`. It reports whether each transaction was accepted, rejected, or is in an intermediate state. Rejections carry one or more structured reason codes (e.g. `AC01` incorrect account, `AG01` transaction forbidden) that explain the outcome.

<details>
<summary>Example response</summary>

```json
{
  "group_header": {
    "message_id": "STS20260510001",
    "creation_datetime": "2026-05-10T14:30:00"
  },
  "original_group_info": {
    "original_message_id": "MSG20240508001",
    "original_message_name_id": "pacs.008.001.08",
    "original_creation_datetime": "2024-05-08T10:00:00",
    "group_status": "ACSC"
  },
  "transaction_statuses": [
    {
      "original_end_to_end_id": "E2E-001",
      "original_transaction_id": "TX-001",
      "status": "ACSC",
      "status_reasons": [],
      "acceptance_datetime": "2026-05-10T14:29:45"
    }
  ]
}
```

</details>

### parse_pain001

`pain.001` is the initiating message in a credit transfer flow, sent by a corporate or customer to their bank. It groups transactions into one or more `PaymentInformation` batches that share a debtor account, execution date, and service level. The LLM sees the full hierarchy: group header → batches → transactions.

<details>
<summary>Example response</summary>

```json
{
  "group_header": {
    "message_id": "PAIN20260510-001",
    "creation_datetime": "2026-05-10T09:00:00",
    "number_of_transactions": 1,
    "control_sum": "1500.00",
    "initiating_party_name": "ACME Corp"
  },
  "payment_informations": [
    {
      "payment_information_id": "BATCH-2026-05-10-A",
      "payment_method": "TRF",
      "requested_execution_date": "2026-05-12",
      "debtor": {"name": "ACME Corp"},
      "debtor_account_iban": "DE89370400440532013000",
      "debtor_agent": {"bic": "DEUTDEFFXXX"},
      "charge_bearer": "SLEV",
      "service_level_code": "SEPA",
      "transactions": [
        {
          "end_to_end_id": "E2E-PAIN-001",
          "amount": {"value": "1500.00", "currency": "EUR"},
          "creditor": {"name": "Acme Supplier SARL"},
          "creditor_account_iban": "FR1420041010050500013M02606",
          "remittance_info": ["Invoice 2026-0042"]
        }
      ]
    }
  ]
}
```

</details>

### parse_camt053

`camt.053` is the structured account statement sent by a bank to its customer. It reports opening and closing balances and individual debit/credit entries for a period, each optionally broken down to individual transaction details. It is the primary source for automated bank reconciliation.

<details>
<summary>Example response</summary>

```json
{
  "group_header": {
    "message_id": "CAMT053-SINGLE-001",
    "creation_datetime": "2026-05-10T08:00:00"
  },
  "statements": [
    {
      "statement_id": "STMT-2026-05-09-001",
      "account_iban": "DE89370400440532013000",
      "account_currency": "EUR",
      "balances": [
        {
          "type_code": "OPBD",
          "amount": {"value": "10000.00", "currency": "EUR"},
          "credit_debit": "CRDT",
          "balance_date": "2026-05-09"
        }
      ],
      "entries": [
        {
          "entry_ref": "NTRY-001",
          "amount": {"value": "1500.00", "currency": "EUR"},
          "credit_debit": "DBIT",
          "status": "BOOK",
          "booking_date": "2026-05-09",
          "bank_tx_domain": "PMNT",
          "bank_tx_family": "ICDT",
          "bank_tx_subfamily": "ESCT"
        }
      ]
    }
  ]
}
```

</details>

### validate_pacs008

Validates a `pacs.008.001.08` message against its XSD and returns every violation in one pass. Use this when you need to know all the errors in a message rather than just the first one the parser encounters.

<details>
<summary>Example response (invalid document)</summary>

```json
{
  "valid": false,
  "schema_id": "pacs.008.001.08",
  "violations": [
    {
      "line": 5,
      "column": 3,
      "path": "/{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}Document/{urn:...}FIToFICstmrCdtTrf",
      "message": "Element '{urn:...}WrongElement': This element is not expected.",
      "domain": "SCHEMASV",
      "type_name": "SCHEMAV_CVC_COMPLEX_TYPE_2_4",
      "level": "ERROR"
    }
  ]
}
```

</details>

### validate_pacs002

Validates a `pacs.002.001.10` message against its XSD and returns every violation in one pass.

### validate_pain001

Validates a `pain.001.001.09` message against its XSD and returns every violation in one pass.

### validate_camt053

Validates a `camt.053.001.08` message against its XSD and returns every violation in one pass.

## Security model

- **XXE and entity-expansion hardening:** All parse and validate tools reject input containing `<!DOCTYPE>` or `<!ENTITY>` declarations before any XML parsing occurs. This blocks XXE file-read, SSRF, and billion-laughs DoS patterns.
- **Build integrity:** Generated xsdata models are SHA-256 verified in CI on every commit (`sha256sum -c GENERATED_HASHES.txt`). Regeneration is reproducible from the vendored XSDs.
- **Supply chain:** GitHub Actions workflows use SHA-pinned action references (commit-hash `@` pins, not mutable tags).
- **Distribution integrity:** PyPI artifacts are published via OIDC Trusted Publishing and signed with Sigstore. SBOMs (CycloneDX and SPDX) are generated and vulnerability-scanned on every CI run; release artifacts include the SBOM.
- **Vulnerability disclosure:** See [SECURITY.md](SECURITY.md).

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
