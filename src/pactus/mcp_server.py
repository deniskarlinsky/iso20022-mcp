"""FastMCP server for Pactus — ISO 20022 payment message processing."""

from __future__ import annotations

from fastmcp import FastMCP
from pydantic import ValidationError

from pactus.core.domain import ParsedPacs008
from pactus.core.domain.pacs002 import ParsedPacs002
from pactus.core.parsers import (
    UnsafeXmlError,
)
from pactus.core.parsers import (
    parse_pacs002 as _parse_pacs002,
)
from pactus.core.parsers import (
    parse_pacs008 as _parse_pacs008,
)

mcp = FastMCP("pactus")


@mcp.tool
def ping() -> dict[str, str]:
    """Health check tool. Returns service metadata."""
    return {"status": "ok", "service": "pactus-mcp", "version": "0.2.0"}


@mcp.tool
def parse_pacs008(xml: str) -> ParsedPacs008 | dict[str, str]:
    """Parse a pacs.008.001.08 (FI-to-FI Customer Credit Transfer) message.

    pacs.008 is the most common ISO 20022 message in cross-border payments
    and is required for all SWIFT cross-border traffic from November 2025.
    Each message carries one or more credit transfer instructions between
    financial institutions.

    Returns a structured ParsedPacs008 with the group header (message-level
    metadata) and a list of transactions (each instruction). On parse or
    validation failure, returns {"error": "..."} so the agent can explain
    rather than crashing.

    Args:
        xml: The pacs.008 XML message as a string.

    Returns:
        ParsedPacs008 on success, or {"error": "..."} on failure.
    """
    if not xml or not xml.strip():
        return {"error": "empty input"}
    try:
        return _parse_pacs008(xml)
    except UnsafeXmlError as e:
        return {"error": f"unsafe input rejected: {e}"}
    except ValidationError as e:
        return {"error": f"validation failed: {e.error_count()} error(s) — {e.errors()[0]['msg']}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool
def parse_pacs002(xml: str) -> ParsedPacs002 | dict[str, str]:
    """Parse a pacs.002.001.10 (FI-to-FI Payment Status Report) message.

    pacs.002 is the response to a pacs.008 credit transfer. It reports
    whether each transaction was accepted, rejected, or is in an
    intermediate state. Each transaction carries a status code and
    optionally one or more structured reason codes explaining the outcome.

    Returns a structured ParsedPacs002 on success, or {"error": "..."} on
    failure.

    Args:
        xml: The pacs.002 XML message as a string.

    Returns:
        ParsedPacs002 on success, or {"error": "..."} on failure.
    """
    if not xml or not xml.strip():
        return {"error": "empty input"}
    try:
        return _parse_pacs002(xml)
    except UnsafeXmlError as e:
        return {"error": f"unsafe input rejected: {e}"}
    except ValidationError as e:
        return {"error": f"validation failed: {e.error_count()} error(s) — {e.errors()[0]['msg']}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main() -> None:
    """Entry point for the pactus-mcp console script."""
    mcp.run()


if __name__ == "__main__":
    main()
