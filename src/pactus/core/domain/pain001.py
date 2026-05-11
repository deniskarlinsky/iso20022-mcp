"""Domain models for pain.001.001.09 — Customer Credit Transfer Initiation.

The initiating message in a credit transfer flow: a customer/corporate
instructs their bank to execute one or more payment batches. Structurally
deeper than pacs.008: GroupHeader → PaymentInformation[] → Transaction[].

These are hand-curated LLM-facing models projected from xsdata-generated
classes in pactus.generated.pain_001_001_09. Generated classes never escape
the parser layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from pactus.core.domain.common import Agent, Amount, Party

PaymentMethod = Literal["TRF", "CHK", "TRA", "DD"]
ChargeBearer = Literal["DEBT", "CRED", "SHAR", "SLEV"]


class GroupHeader(BaseModel):
    """Message-level metadata for the whole pain.001."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(description="MsgId of this initiation.")
    creation_datetime: datetime = Field(description="When this message was generated.")
    number_of_transactions: int = Field(
        description="Total transactions across all PaymentInformation blocks."
    )
    control_sum: str | None = Field(
        default=None,
        description="Sum of all transaction amounts, as a string to preserve "
        "decimal precision. Optional in the schema.",
    )
    initiating_party_name: str | None = Field(
        default=None,
        description="Name of the party initiating the message (typically the "
        "corporate or customer sending to their bank).",
    )


class Transaction(BaseModel):
    """One credit transfer transaction within a PaymentInformation batch."""

    model_config = ConfigDict(extra="forbid")

    end_to_end_id: str = Field(
        description="EndToEndId chosen by the initiating party. Travels "
        "through the entire payment chain unchanged."
    )
    instruction_id: str | None = Field(
        default=None,
        description="InstrId — the initiating party's internal reference.",
    )
    amount: Amount = Field(description="Transfer amount and currency.")
    creditor: Party = Field(description="Beneficiary of the transfer.")
    creditor_account_iban: str | None = Field(
        default=None,
        description="Creditor's IBAN. Either IBAN or Other identifier is "
        "required by the schema; this exposes the common IBAN case.",
    )
    creditor_agent: Agent | None = Field(
        default=None,
        description="Creditor's bank, if specified.",
    )
    remittance_info: list[str] = Field(
        default_factory=list,
        description="Free-form remittance lines for the creditor.",
    )


class PaymentInformation(BaseModel):
    """One payment batch sharing debtor account, execution date, and service level."""

    model_config = ConfigDict(extra="forbid")

    payment_information_id: str = Field(
        description="PmtInfId — the initiating party's batch reference."
    )
    payment_method: PaymentMethod = Field(
        description="How the payment is executed. Closed ISO set."
    )
    batch_booking: bool | None = Field(
        default=None,
        description="If True, the bank should book the batch as one entry "
        "on the debtor's statement; if False, as individual entries.",
    )
    number_of_transactions: int | None = Field(
        default=None,
        description="Transaction count within this batch.",
    )
    control_sum: str | None = Field(
        default=None,
        description="Sum of amounts within this batch, as a string.",
    )
    requested_execution_date: date = Field(
        description="When the initiator wants the batch executed."
    )
    debtor: Party = Field(description="The party whose account is debited.")
    debtor_account_iban: str | None = Field(
        default=None,
        description="Debtor's IBAN.",
    )
    debtor_agent: Agent = Field(description="The debtor's bank — required at the batch level.")
    charge_bearer: ChargeBearer | None = Field(
        default=None,
        description="Who pays the transaction fees. Inherited by all "
        "transactions in the batch unless overridden.",
    )
    service_level_code: str | None = Field(
        default=None,
        description="ISO service level code (e.g. 'SEPA', 'URGP'). Free-form "
        "string because the code set is large and version-dependent.",
    )
    category_purpose_code: str | None = Field(
        default=None,
        description="ISO category purpose code (e.g. 'SALA' salary, 'SUPP' "
        "supplier). Free-form for the same reason.",
    )
    transactions: list[Transaction] = Field(
        description="Credit transfer transactions in this batch.",
    )


class ParsedPain001(BaseModel):
    """A fully-parsed pain.001.001.09 Customer Credit Transfer Initiation."""

    model_config = ConfigDict(extra="forbid")

    group_header: GroupHeader
    payment_informations: list[PaymentInformation]
