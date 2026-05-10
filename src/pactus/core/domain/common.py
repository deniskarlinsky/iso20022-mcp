"""Shared domain models used across multiple ISO 20022 message types.

ISO 20022's whole design philosophy is a unified data dictionary —
a Party, Agent, or Amount means the same thing in pacs.008 as in
pain.001 or camt.053. These models mirror that.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, WithJsonSchema


def _coerce_to_decimal(value: object) -> Decimal:
    """Accept Decimal, str, int, or float; reject everything else.

    Going through str(value) when the input is float avoids binary
    floating-point artifacts (Decimal(0.1) vs Decimal("0.1")).
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (str, int, float)):
        return Decimal(str(value))
    raise TypeError(f"cannot coerce {type(value).__name__} to Decimal")


def _serialize_decimal(value: Decimal) -> str:
    """Serialize a Decimal as a fixed-point string.

    Using format spec ``f`` ensures no scientific notation and preserves
    trailing zeros from the original Decimal context.
    """
    return f"{value:f}"


MoneyDecimal = Annotated[
    Decimal,
    BeforeValidator(_coerce_to_decimal),
    PlainSerializer(_serialize_decimal, return_type=str),
    WithJsonSchema({"type": "string", "description": "Decimal value serialized as a string."}),
]
"""A Decimal type that serializes as a string in JSON.

Use this for any monetary value across the project. The JSON Schema
representation becomes a plain ``{"type": "string"}`` (no regex pattern),
which avoids the ECMA-262 look-around issue in Pydantic's default
Decimal schema and lets strict MCP clients consume the schema.

Internally still a ``Decimal``, so arithmetic and precision work normally.
"""


class Party(BaseModel):
    """A party to a payment — debtor, creditor, intermediary, etc.

    Currently captures only the name. Address, identification, and
    contact details will be added when use cases require them.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ..., min_length=1, max_length=140, description="Party name as it appears in the message."
    )


class Agent(BaseModel):
    """A financial institution acting on behalf of a party.

    Currently captures only the BIC. Clearing system membership,
    name, and address are scaffolded for future expansion.
    """

    model_config = ConfigDict(extra="forbid")

    bic: str | None = Field(
        None,
        min_length=8,
        max_length=11,
        pattern=r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",
        description="Business Identifier Code (BIC/SWIFT). 8 or 11 characters.",
    )


class Amount(BaseModel):
    """A monetary amount with currency.

    The value is a Decimal to avoid float arithmetic errors. Currency
    is the ISO 4217 three-letter code.
    """

    model_config = ConfigDict(extra="forbid")

    value: MoneyDecimal = Field(..., description="Monetary value. Always positive.")
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="ISO 4217 currency code.",
    )
