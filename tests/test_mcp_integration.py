"""MCP-layer integration tests using FastMCP in-memory Client.

Each test exercises the MCP tool boundary (mcp_server.py) rather than the
parser layer directly, covering the dispatch logic, error wrapping, and the
ping metadata endpoint.
"""

from __future__ import annotations

import importlib.metadata

import pytest
from fastmcp import Client

from pactus.mcp_server import mcp

# ---------------------------------------------------------------------------
# Constants shared across parametrized tests
# ---------------------------------------------------------------------------

_ALL_PARSE_TOOLS = ["parse_pacs008", "parse_pacs002", "parse_pain001", "parse_camt053"]

_DOCTYPE_XML = '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY x "y">]><root/>'

# Wrong-namespace XMLs that parse as valid XML but fail domain validation.
# pacs008 uses pain.001 namespace; the others use pacs.008 namespace.
_MALFORMED_XML: dict[str, str] = {
    "parse_pacs008": (
        '<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"/>'
    ),
    "parse_pacs002": (
        '<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"/>'
    ),
    "parse_pain001": (
        '<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"/>'
    ),
    "parse_camt053": (
        '<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"/>'
    ),
}


# ---------------------------------------------------------------------------
# Tools list
# ---------------------------------------------------------------------------


class TestToolsList:
    async def test_exposes_all_five_tools(self) -> None:
        async with Client(mcp) as c:
            tools = await c.list_tools()
            names = {t.name for t in tools}
        assert names == {"ping", "parse_pacs008", "parse_pacs002", "parse_pain001", "parse_camt053"}


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------


class TestPing:
    async def test_returns_ok_metadata(self) -> None:
        expected_version = importlib.metadata.version("pactus-mcp")
        async with Client(mcp) as c:
            r = await c.call_tool("ping", {})
        assert r.data == {"status": "ok", "service": "pactus-mcp", "version": expected_version}


# ---------------------------------------------------------------------------
# Parametrized error branches (all four parse tools share the same contract)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tool", _ALL_PARSE_TOOLS)
@pytest.mark.parametrize(
    "xml",
    ["", "   \n\t "],
    ids=["empty_string", "whitespace_only"],
)
async def test_parse_empty_input(tool: str, xml: str) -> None:
    async with Client(mcp) as c:
        r = await c.call_tool(tool, {"xml": xml})
    assert r.data == {"error": "empty input"}


@pytest.mark.parametrize("tool", _ALL_PARSE_TOOLS)
async def test_parse_doctype_rejected(tool: str) -> None:
    async with Client(mcp) as c:
        r = await c.call_tool(tool, {"xml": _DOCTYPE_XML})
    assert isinstance(r.data, dict)
    assert r.data["error"].startswith("unsafe input rejected:")


@pytest.mark.parametrize("tool,xml", list(_MALFORMED_XML.items()))
async def test_parse_validation_failed(tool: str, xml: str) -> None:
    async with Client(mcp) as c:
        r = await c.call_tool(tool, {"xml": xml})
    assert isinstance(r.data, dict)
    assert r.data["error"].startswith("validation failed:")


@pytest.mark.parametrize("tool", _ALL_PARSE_TOOLS)
async def test_parse_non_xml_garbage(tool: str) -> None:
    async with Client(mcp) as c:
        r = await c.call_tool(tool, {"xml": "not-xml-at-all"})
    assert isinstance(r.data, dict)
    # Generic handler formats as "ExceptionName: message"
    assert ":" in r.data["error"]


# ---------------------------------------------------------------------------
# Happy-path tests — assert structured model fields, not just non-empty
# ---------------------------------------------------------------------------


class TestParsePacs008HappyPath:
    async def test_group_header_and_transaction(self, pacs008_single_xml: str) -> None:
        async with Client(mcp) as c:
            r = await c.call_tool("parse_pacs008", {"xml": pacs008_single_xml})
        assert r.data.group_header.message_id == "MSG20240508001"
        assert r.data.group_header.number_of_transactions == 1
        assert r.data.group_header.settlement_method == "CLRG"
        tx = r.data.transactions[0]
        assert tx.charge_bearer == "SHAR"
        assert tx.settlement_amount.currency == "USD"
        assert tx.settlement_amount.value == "1000.00"
        assert tx.debtor.name == "Acme Corporation"
        assert tx.creditor.name == "Global Supplies Ltd"


class TestParsePacs002HappyPath:
    async def test_group_header_and_transaction_status(self, pacs002_single_xml: str) -> None:
        async with Client(mcp) as c:
            r = await c.call_tool("parse_pacs002", {"xml": pacs002_single_xml})
        assert r.data.group_header.message_id == "STS20260510001"
        assert r.data.original_group_info.original_message_id == "MSG20240508001"
        assert r.data.original_group_info.group_status == "ACSC"
        assert len(r.data.transaction_statuses) == 1
        assert r.data.transaction_statuses[0].status == "ACSC"


class TestParsePain001HappyPath:
    async def test_group_header_and_payment_information(self, pain001_single_xml: str) -> None:
        async with Client(mcp) as c:
            r = await c.call_tool("parse_pain001", {"xml": pain001_single_xml})
        assert r.data.group_header.message_id == "PAIN20260510-001"
        assert r.data.group_header.number_of_transactions == 1
        assert len(r.data.payment_informations) == 1
        pmt = r.data.payment_informations[0]
        assert pmt.payment_method == "TRF"
        assert len(pmt.transactions) == 1


class TestParseCamt053HappyPath:
    async def test_group_header_and_statement(self, camt053_single_xml: str) -> None:
        async with Client(mcp) as c:
            r = await c.call_tool("parse_camt053", {"xml": camt053_single_xml})
        assert r.data.group_header.message_id == "CAMT053-SINGLE-001"
        assert len(r.data.statements) == 1
        stmt = r.data.statements[0]
        assert stmt.statement_id == "STMT-2026-05-09-001"
        assert len(stmt.balances) >= 1
        assert stmt.balances[0].amount.currency is not None
