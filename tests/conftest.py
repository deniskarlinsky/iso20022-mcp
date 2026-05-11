"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def pacs008_single_xml() -> str:
    """A pacs.008 message with one transaction."""
    return (FIXTURES_DIR / "test_pacs008.xml").read_text(encoding="utf-8")


@pytest.fixture
def pacs008_multi_xml() -> str:
    """A pacs.008 message with three transactions."""
    return (FIXTURES_DIR / "test_pacs008_multi.xml").read_text(encoding="utf-8")


@pytest.fixture
def pacs002_single_xml() -> str:
    """A pacs.002 with one transaction in ACSC final-success status."""
    return (FIXTURES_DIR / "test_pacs002_single.xml").read_text(encoding="utf-8")


@pytest.fixture
def pacs002_rejected_xml() -> str:
    """A pacs.002 with one transaction rejected with multiple status reasons."""
    return (FIXTURES_DIR / "test_pacs002_rejected.xml").read_text(encoding="utf-8")


@pytest.fixture
def pacs002_multi_xml() -> str:
    """A pacs.002 with three transactions in mixed statuses."""
    return (FIXTURES_DIR / "test_pacs002_multi.xml").read_text(encoding="utf-8")
