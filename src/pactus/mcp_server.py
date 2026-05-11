"""FastMCP server for Pactus — ISO 20022 payment message processing."""

from __future__ import annotations

import importlib.metadata

from fastmcp import FastMCP
from pydantic import ValidationError

from pactus.core.domain import ParsedPacs008
from pactus.core.domain.camt053 import ParsedCamt053
from pactus.core.domain.pacs002 import ParsedPacs002
from pactus.core.domain.pain001 import ParsedPain001
from pactus.core.parsers import (
    UnsafeXmlError,
)
from pactus.core.parsers import (
    parse_camt053 as _parse_camt053,
)
from pactus.core.parsers import (
    parse_pacs002 as _parse_pacs002,
)
from pactus.core.parsers import (
    parse_pacs008 as _parse_pacs008,
)
from pactus.core.parsers import (
    parse_pain001 as _parse_pain001,
)

mcp = FastMCP("pactus")

_VERSION = importlib.metadata.version("pactus-mcp")


@mcp.tool
def ping() -> dict[str, str]:
    """Health check tool. Returns service metadata."""
    return {"status": "ok", "service": "pactus-mcp", "version": _VERSION}


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


@mcp.tool
def parse_pain001(xml: str) -> ParsedPain001 | dict[str, str]:
    """Parse a pain.001.001.09 Customer Credit Transfer Initiation message.

    pain.001 is the initiating message in a credit transfer flow, sent by a
    corporate or customer to their bank. It carries one or more payment
    batches (PaymentInformation), each grouping transactions that share a
    debtor account, execution date, and service level.

    Returns a structured ParsedPain001 on success, or {"error": "..."} on
    failure.

    Args:
        xml: The pain.001 XML message as a string.

    Returns:
        ParsedPain001 on success, or {"error": "..."} on failure.
    """
    if not xml or not xml.strip():
        return {"error": "empty input"}
    try:
        return _parse_pain001(xml)
    except UnsafeXmlError as e:
        return {"error": f"unsafe input rejected: {e}"}
    except ValidationError as e:
        return {"error": f"validation failed: {e.error_count()} error(s) — {e.errors()[0]['msg']}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool
def parse_camt053(xml: str) -> ParsedCamt053 | dict[str, str]:
    """Parse a camt.053.001.08 Bank-to-Customer Cash Management Statement.

    camt.053 is the structured account statement sent by a bank to its
    customer. It reports balances (opening, closing, interim) and individual
    debit/credit entries for a period, each optionally broken down to
    individual transaction details. It is the primary source for automated
    bank reconciliation.

    Returns a structured ParsedCamt053 on success, or {"error": "..."} on
    failure.

    Args:
        xml: The camt.053 XML message as a string.

    Returns:
        ParsedCamt053 on success, or {"error": "..."} on failure.
    """
    if not xml or not xml.strip():
        return {"error": "empty input"}
    try:
        return _parse_camt053(xml)
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
