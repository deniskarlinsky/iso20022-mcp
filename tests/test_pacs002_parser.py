"""Tests for pacs.002.001.10 parsing.

Mirrors the structure of test_pacs008_parser.py: happy path, multi-tx,
optional-field handling, rejection-reason details, and a security
regression confirming the same hardening applies.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from pactus.core.domain.pacs002 import ParsedPacs002
from pactus.core.parsers import UnsafeXmlError, parse_pacs002


class TestParsePacs002HappyPath:
    """Parsing a pacs.002 with one ACSC transaction."""

    def test_parses_single_acsc_transaction(self, pacs002_single_xml: str) -> None:
        result = parse_pacs002(pacs002_single_xml)
        assert isinstance(result, ParsedPacs002)

    def test_group_header_fields_populated(self, pacs002_single_xml: str) -> None:
        result = parse_pacs002(pacs002_single_xml)
        assert result.group_header.message_id == "STS20260510001"
        assert isinstance(result.group_header.creation_datetime, datetime)

    def test_original_group_info_references_pacs008(self, pacs002_single_xml: str) -> None:
        result = parse_pacs002(pacs002_single_xml)
        assert result.original_group_info.original_message_id == "MSG20240508001"
        assert result.original_group_info.original_message_name_id == "pacs.008.001.08"

    def test_acceptance_datetime_parsed_as_datetime(self, pacs002_single_xml: str) -> None:
        result = parse_pacs002(pacs002_single_xml)
        tx = result.transaction_statuses[0]
        assert isinstance(tx.acceptance_datetime, datetime)

    def test_status_code_literal_accepts_acsc(self, pacs002_single_xml: str) -> None:
        result = parse_pacs002(pacs002_single_xml)
        tx = result.transaction_statuses[0]
        assert tx.status == "ACSC"
        assert result.original_group_info.group_status == "ACSC"


class TestParsePacs002Rejected:
    """Parsing a pacs.002 with one RJCT transaction and two status reasons."""

    def test_rjct_status_carries_two_reasons(self, pacs002_rejected_xml: str) -> None:
        result = parse_pacs002(pacs002_rejected_xml)
        tx = result.transaction_statuses[0]
        assert tx.status == "RJCT"
        assert len(tx.status_reasons) == 2

    def test_first_reason_has_originator_name(self, pacs002_rejected_xml: str) -> None:
        result = parse_pacs002(pacs002_rejected_xml)
        reason = result.transaction_statuses[0].status_reasons[0]
        assert reason.originator_name == "Receiving Bank GmbH"
        assert reason.code == "AC01"

    def test_second_reason_has_no_originator(self, pacs002_rejected_xml: str) -> None:
        result = parse_pacs002(pacs002_rejected_xml)
        reason = result.transaction_statuses[0].status_reasons[1]
        assert reason.originator_name is None
        assert reason.code == "AG01"

    def test_reason_additional_info_preserved(self, pacs002_rejected_xml: str) -> None:
        result = parse_pacs002(pacs002_rejected_xml)
        reasons = result.transaction_statuses[0].status_reasons
        assert reasons[0].additional_information == [
            "Account number format invalid for target jurisdiction"
        ]
        assert reasons[1].additional_information == [
            "Transaction type not supported by creditor agent"
        ]


class TestParsePacs002Multi:
    """Parsing a pacs.002 with three transactions in mixed statuses."""

    def test_parses_three_transactions(self, pacs002_multi_xml: str) -> None:
        result = parse_pacs002(pacs002_multi_xml)
        assert len(result.transaction_statuses) == 3

    def test_status_codes_are_acsc_pdng_rjct(self, pacs002_multi_xml: str) -> None:
        result = parse_pacs002(pacs002_multi_xml)
        statuses = [tx.status for tx in result.transaction_statuses]
        assert statuses == ["ACSC", "PDNG", "RJCT"]

    def test_only_rejected_tx_has_reasons(self, pacs002_multi_xml: str) -> None:
        result = parse_pacs002(pacs002_multi_xml)
        txs = result.transaction_statuses
        assert txs[0].status_reasons == []
        assert txs[1].status_reasons == []
        assert len(txs[2].status_reasons) == 1
        assert txs[2].status_reasons[0].code == "AC04"


class TestParsePacs002OptionalFields:
    """Optional-field branches in parse_pacs002."""

    def test_orgnl_cre_dt_tm_optional(self, pacs002_rejected_xml: str) -> None:
        """OrgnlCreDtTm absent in rejected fixture → original_creation_datetime is None."""
        result = parse_pacs002(pacs002_rejected_xml)
        assert result.original_group_info.original_creation_datetime is None

    def test_acceptance_datetime_optional(self, pacs002_multi_xml: str) -> None:
        """Multi-fixture omits AccptncDtTm → acceptance_datetime is None."""
        result = parse_pacs002(pacs002_multi_xml)
        assert result.transaction_statuses[0].acceptance_datetime is None


class TestPacs002SecurityGuard:
    """The XXE/DOCTYPE guard must apply to pacs.002 just as it does to pacs.008."""

    def test_rejects_xxe_payload(self) -> None:
        payload = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10">&xxe;</Document>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs002(payload)
