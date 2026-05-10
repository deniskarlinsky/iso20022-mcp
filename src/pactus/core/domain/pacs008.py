"""Domain models for pacs.008.001.08 — FI to FI Customer Credit Transfer.

This is the most common ISO 20022 message in cross-border payments.
A pacs.008 carries one or more credit transfer instructions from one
financial institution to another.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from pactus.core.domain.common import Agent, Amount, Party

ChargeBearer = Literal["DEBT", "CRED", "SHAR", "SLEV"]
"""How transaction charges are allocated between debtor and creditor.

- DEBT: All charges borne by the debtor.
- CRED: All charges borne by the creditor.
- SHAR: Shared — debtor pays sender's charges, creditor pays receiver's.
- SLEV: Following the rules of a service level (e.g. SEPA).
"""

SettlementMethod = Literal["INDA", "INGA", "COVE", "CLRG"]
"""How settlement between the agents occurs.

- INDA: Settled via instructed agent's account.
- INGA: Settled via instructing agent's account.
- COVE: Settled via a cover payment through correspondents.
- CLRG: Settled through a clearing system (most common for SEPA, FedNow).
"""


class GroupHeader(BaseModel):
    """Group-level metadata that applies to all transactions in the message."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(
        ..., max_length=35, description="Unique identifier for the message, assigned by the sender."
    )
    creation_datetime: datetime = Field(..., description="When the message was created.")
    number_of_transactions: int = Field(
        ..., ge=1, description="How many credit transfer transactions are in this message."
    )
    settlement_method: SettlementMethod = Field(..., description="How the agents settle.")


class Pacs008Transaction(BaseModel):
    """A single credit transfer instruction within a pacs.008 message."""

    model_config = ConfigDict(extra="forbid")

    end_to_end_id: str = Field(
        ...,
        max_length=35,
        description="Identifier assigned by the originator, passed unchanged through the entire chain.",
    )
    instruction_id: str | None = Field(
        None,
        max_length=35,
        description="Identifier for this instruction between two parties (e.g. debtor and debtor's bank).",
    )
    transaction_id: str | None = Field(
        None,
        max_length=35,
        description="Unique transaction identifier assigned by the first instructing agent.",
    )
    settlement_amount: Amount = Field(
        ..., description="The amount to be settled between the agents."
    )
    settlement_date: date | None = Field(None, description="The date the agents settle.")
    charge_bearer: ChargeBearer = Field(..., description="Who pays the transaction charges.")
    debtor: Party = Field(..., description="The party that owes the money.")
    debtor_agent: Agent | None = Field(
        None, description="The financial institution serving the debtor."
    )
    creditor: Party = Field(..., description="The party to whom the money is owed.")
    creditor_agent: Agent | None = Field(
        None, description="The financial institution serving the creditor."
    )
    remittance_info: str | None = Field(
        None,
        max_length=140,
        description="Free-form text accompanying the payment (invoice number, reference, etc.).",
    )


class ParsedPacs008(BaseModel):
    """The result of parsing a pacs.008.001.08 message."""

    model_config = ConfigDict(extra="forbid")

    group_header: GroupHeader = Field(..., description="Message-level metadata.")
    transactions: list[Pacs008Transaction] = Field(
        ..., min_length=1, description="The credit transfer instructions in this message."
    )
