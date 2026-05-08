# Pactus

An MCP server for ISO 20022 payment message processing. Pactus exposes tools that let AI assistants like Claude parse and validate `pacs.008` payment messages directly from a chat interface.

## Why

The global financial industry is migrating from legacy SWIFT MT messages to ISO 20022 XML by **November 2027**. During this transition, banks, fintechs, and integration teams need fast ways to inspect, debug, and validate ISO 20022 traffic. Pactus brings that capability into any MCP-compatible client so you can hand a message to an AI assistant and ask questions about it in natural language.

## Installation

Requires Python 3.10+.

```bash
git clone <repo-url> iso20022-mcp
cd iso20022-mcp
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install fastmcp
```

Verify the server loads:

```bash
python -c "from server import mcp; print('OK')"
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

### `parse_pacs008`

Extracts key fields from a `pacs.008.001.08` XML message.

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

### `validate_pacs008`

Checks whether an XML string parses as a `pacs.008.001.08` message and contains the required fields.

**Output (valid)**

```json
{ "valid": true }
```

**Output (invalid)**

```json
{ "valid": false, "error": "missing required element: .//iso:Cdtr/iso:Nm" }
```

```json
{ "valid": false, "error": "XML parse error: not well-formed (invalid token): line 1, column 0" }
```

## License

MIT
