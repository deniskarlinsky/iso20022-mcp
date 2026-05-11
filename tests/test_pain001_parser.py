"""Tests for pain.001.001.09 parsing.

Heavier than pacs.008 because pain.001 has a deeper structure
(GroupHeader → PaymentInformation[] → Transaction[]) and richer
optional metadata.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from pactus.core.parsers import UnsafeXmlError, parse_pain001


class TestParsePain001HappyPath:
    """Parsing a pain.001 with one PmtInf and one fully-populated transaction."""

    def test_parses_single_pmt_inf_transaction(self, pain001_single_xml: str) -> None:
        from pactus.core.domain.pain001 import ParsedPain001

        result = parse_pain001(pain001_single_xml)
        assert isinstance(result, ParsedPain001)
        assert len(result.payment_informations) == 1
        assert len(result.payment_informations[0].transactions) == 1

    def test_group_header_message_id_and_initiating_party(self, pain001_single_xml: str) -> None:
        result = parse_pain001(pain001_single_xml)
        assert result.group_header.message_id == "PAIN20260510-001"
        assert result.group_header.initiating_party_name == "ACME Corp"

    def test_group_header_creation_datetime_parsed(self, pain001_single_xml: str) -> None:
        result = parse_pain001(pain001_single_xml)
        assert isinstance(result.group_header.creation_datetime, datetime)
        assert result.group_header.number_of_transactions == 1

    def test_group_header_control_sum_preserved_as_string(self, pain001_single_xml: str) -> None:
        result = parse_pain001(pain001_single_xml)
        assert result.group_header.control_sum == "1500.00"
        assert isinstance(result.group_header.control_sum, str)

    def test_payment_information_id_and_method(self, pain001_single_xml: str) -> None:
        pmt = parse_pain001(pain001_single_xml).payment_informations[0]
        assert pmt.payment_information_id == "BATCH-2026-05-10-A"
        assert pmt.payment_method == "TRF"

    def test_requested_execution_date_parsed_as_date(self, pain001_single_xml: str) -> None:
        pmt = parse_pain001(pain001_single_xml).payment_informations[0]
        assert isinstance(pmt.requested_execution_date, date)
        assert pmt.requested_execution_date == date(2026, 5, 12)

    def test_charge_bearer_literal_accepts_slev(self, pain001_single_xml: str) -> None:
        pmt = parse_pain001(pain001_single_xml).payment_informations[0]
        assert pmt.charge_bearer == "SLEV"

    def test_service_level_and_category_purpose_exposed(self, pain001_single_xml: str) -> None:
        pmt = parse_pain001(pain001_single_xml).payment_informations[0]
        assert pmt.service_level_code == "SEPA"
        assert pmt.category_purpose_code == "SUPP"

    def test_transaction_amount_uses_money_decimal(self, pain001_single_xml: str) -> None:
        """Amount.value must be a Decimal preserving the wire precision."""
        tx = parse_pain001(pain001_single_xml).payment_informations[0].transactions[0]
        assert isinstance(tx.amount.value, Decimal)
        assert tx.amount.value == Decimal("1500.00")
        assert tx.amount.currency == "EUR"

    def test_transaction_creditor_iban_extracted(self, pain001_single_xml: str) -> None:
        tx = parse_pain001(pain001_single_xml).payment_informations[0].transactions[0]
        assert tx.creditor_account_iban == "FR1420041010050500013M02606"
        assert tx.creditor.name == "Acme Supplier SARL"

    def test_transaction_remittance_info_parsed(self, pain001_single_xml: str) -> None:
        tx = parse_pain001(pain001_single_xml).payment_informations[0].transactions[0]
        assert tx.remittance_info == ["Invoice 2026-0042"]
        assert tx.instruction_id == "INSTR-001"


class TestParsePain001MultiplePaymentInformation:
    """Parsing a pain.001 with two PmtInf batches at different execution dates."""

    def test_two_pmt_inf_batches_parsed(self, pain001_multi_pmt_inf_xml: str) -> None:
        result = parse_pain001(pain001_multi_pmt_inf_xml)
        assert len(result.payment_informations) == 2

    def test_batches_have_different_execution_dates(self, pain001_multi_pmt_inf_xml: str) -> None:
        pmts = parse_pain001(pain001_multi_pmt_inf_xml).payment_informations
        assert pmts[0].requested_execution_date == date(2026, 5, 11)
        assert pmts[1].requested_execution_date == date(2026, 5, 25)

    def test_batch_with_two_transactions(self, pain001_multi_pmt_inf_xml: str) -> None:
        pmts = parse_pain001(pain001_multi_pmt_inf_xml).payment_informations
        assert len(pmts[0].transactions) == 1
        assert len(pmts[1].transactions) == 2
        assert [tx.end_to_end_id for tx in pmts[1].transactions] == ["E2E-SAL-1", "E2E-SAL-2"]

    def test_service_level_differs_between_batches(self, pain001_multi_pmt_inf_xml: str) -> None:
        """First batch is URGP, second batch is SEPA — confirms per-batch metadata."""
        pmts = parse_pain001(pain001_multi_pmt_inf_xml).payment_informations
        assert pmts[0].service_level_code == "URGP"
        assert pmts[1].service_level_code == "SEPA"
        assert pmts[1].category_purpose_code == "SALA"


class TestParsePain001OptionalFields:
    """Optional-field branches in parse_pain001."""

    def test_minimal_fixture_parses_with_all_optional_fields_none(
        self, pain001_minimal_xml: str
    ) -> None:
        result = parse_pain001(pain001_minimal_xml)
        pmt = result.payment_informations[0]
        assert result.group_header.control_sum is None
        assert pmt.control_sum is None
        assert pmt.batch_booking is None

    def test_minimal_instruction_id_is_none(self, pain001_minimal_xml: str) -> None:
        tx = parse_pain001(pain001_minimal_xml).payment_informations[0].transactions[0]
        assert tx.instruction_id is None
        assert tx.remittance_info == []

    def test_minimal_service_level_and_category_purpose_none(
        self, pain001_minimal_xml: str
    ) -> None:
        pmt = parse_pain001(pain001_minimal_xml).payment_informations[0]
        assert pmt.service_level_code is None
        assert pmt.category_purpose_code is None
        assert pmt.charge_bearer is None


class TestPain001SecurityGuard:
    """The XXE/DOCTYPE guard must apply to pain.001 just as it does to pacs.008."""

    def test_rejects_xxe_payload(self) -> None:
        payload = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09">&xxe;</Document>"""
        with pytest.raises(UnsafeXmlError):
            parse_pain001(payload)
