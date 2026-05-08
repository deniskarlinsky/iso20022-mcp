# Architecture

```mermaid
flowchart TD
    A[Claude Desktop] -->|reads| B[claude_desktop_config.json]
    A -->|spawns via stdio| C[server.py]
    C -->|registers tools| D[FastMCP]
    D --> E[parse_pacs008]
    D --> F[validate_pacs008]
    E -->|parses| G[xml.etree.ElementTree]
    F -->|parses| G
    G -->|reads| H[ISO 20022 pacs.008 XML]
```

## Flow

1. **Claude Desktop** loads `claude_desktop_config.json` at startup to discover MCP servers.
2. It spawns `server.py` as a subprocess and communicates over **stdio** (stdin/stdout).
3. `server.py` instantiates **FastMCP**, which registers the `parse_pacs008` and `validate_pacs008` tools.
4. When a tool is invoked, it uses **`xml.etree.ElementTree`** to parse the supplied **pacs.008 ISO 20022 XML** and returns structured JSON to Claude.
