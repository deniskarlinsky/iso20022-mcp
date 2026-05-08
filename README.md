# Pactus

An MCP server for ISO 20022 payment message processing. Pactus exposes tools that let AI assistants like Claude parse and validate ISO 20022 payment messages directly from a chat interface.

## Why

The global financial industry is migrating from legacy SWIFT MT messages to ISO 20022 XML by **November 2027**. During this transition, banks, fintechs, and integration teams need fast ways to inspect, debug, and validate ISO 20022 traffic. Pactus brings that capability into any MCP-compatible client so you can hand a message to an AI assistant and ask questions about it in natural language.

## Features

- **Structured error handling** — tools never raise; failures are returned as `{"error": "..."}` so the assistant can explain them
- **Input validation** — empty or whitespace-only payloads are rejected up front
- **Logging** — every tool call is logged with the tool name and either the message id or a 50-character input preview
- **Type hints** — every tool signature is fully annotated
- **Tested** — 15 pytest tests covering happy paths, missing fields, and malformed XML across all six tools

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/deniskarlinsky/iso20022-mcp iso20022-mcp
cd iso20022-mcp
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify the server loads:

```bash
python -c "from server import mcp; print('OK')"
```

## Running tests

```bash
python3 -m pytest tests/ -v
```

## Connecting to Claude Desktop

Add Pactus to your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pactus": {
      "command": "/absolute/path/to/iso20022-mcp/venv/bin/python",
      "args": ["/absolute/path/to/iso20022-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. The Pactus tools will appear in the tools menu.

## Available tools

All tools take an `xml: str` argument and return a `dict`. **No tool raises** — every failure mode (empty input, malformed XML, missing required field) is reported as a structured response.

| Tool pair | Message type |
|---|---|
| `parse_pacs008` / `validate_pacs008` | `pacs.008.001.08` — FI-to-FI Customer Credit Transfer |
| `parse_pain001` / `validate_pain001` | `pain.001.001.09` — Customer Credit Transfer Initiation |
| `parse_camt053` / `validate_camt053` | `camt.053.001.08` — Bank-to-Customer Statement |

### Response shapes

`parse_*` tools — success returns extracted fields; failure returns `{"error": "..."}`:

```json
{ "error": "empty input" }
{ "error": "XML parse error: not well-formed (invalid token): line 1, column 0" }
{ "error": "missing required field" }
```

`validate_*` tools — success returns `{"valid": true}`; failure returns `{"valid": false, "error": "..."}` (or `{"error": "empty input"}` when the payload is empty):

```json
{ "valid": false, "error": "missing required element: .//iso:Cdtr/iso:Nm" }
{ "valid": false, "error": "XML parse error: not well-formed (invalid token): line 1, column 0" }
```

### Example: `parse_pacs008`

**Input**

```xml
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr><MsgId>MSG-001</MsgId></GrpHdr>
    <CdtTrfTxInf>
      <IntrBkSttlmAmt Ccy="EUR">1250.00</IntrBkSttlmAmt>
      <Dbtr><Nm>Acme GmbH</Nm></Dbtr>
      <DbtrAgt><FinInstnId><BICFI>DEUTDEFF</BICFI></FinInstnId></DbtrAgt>
      <Cdtr><Nm>Globex SA</Nm></Cdtr>
      <CdtrAgt><FinInstnId><BICFI>BNPAFRPP</BICFI></FinInstnId></CdtrAgt>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>
```

**Output**

```json
{
  "message_id": "MSG-001",
  "amount": "1250.00",
  "currency": "EUR",
  "debtor": "Acme GmbH",
  "debtor_bic": "DEUTDEFF",
  "creditor": "Globex SA",
  "creditor_bic": "BNPAFRPP"
}
```

See `test_pacs008.xml`, `test_pain001.xml`, and `test_camt053.xml` for full sample messages of each type.

## License

MIT
