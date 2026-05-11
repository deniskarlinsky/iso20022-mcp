"""Domain models for pacs.002.001.10 — FI-to-FI Payment Status Report.

Status reports are responses to pacs.008 credit transfer messages,
indicating per-transaction acceptance, rejection, or intermediate state.

These are hand-curated LLM-facing models projected from the xsdata-generated
classes in pactus.generated.pacs_002_001_10. Generated classes never escape
the parser layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Closed ISO 20022 status code set — same for GrpSts and TxSts at this message level.
StatusCode = Literal[
    "ACSC",
    "ACSP",
    "ACCP",
    "ACCC",
    "ACWC",
    "ACWP",
    "BLCK",
    "CANC",
    "PDNG",
    "RJCT",
]


class StatusReason(BaseModel):
    """One reason explaining a transaction's status.

    Multiple reasons may apply to a single status (e.g. RJCT with both
    AC01 'IncorrectAccountNumber' and AG01 'TransactionForbidden').
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        description="ISO 20022 reason code (e.g. 'AC01', 'AG01'). Free-form "
        "string because the reason-code set is large and version-dependent."
    )
    proprietary: str | None = Field(
        default=None,
        description="Bank-proprietary reason code when no ISO code applies.",
    )
    originator_name: str | None = Field(
        default=None,
        description="Name of the party that originated this status reason "
        "(typically the rejecting institution).",
    )
    additional_information: list[str] = Field(
        default_factory=list,
        description="Free-form explanatory text. Multiple lines possible.",
    )


class OriginalGroupInfo(BaseModel):
    """Reference to the original pacs.008 message this report responds to."""

    model_config = ConfigDict(extra="forbid")

    original_message_id: str = Field(
        description="MsgId of the original pacs.008 being reported on."
    )
    original_message_name_id: str = Field(
        description="Message name identifier of the original (e.g. 'pacs.008.001.08')."
    )
    original_creation_datetime: datetime | None = Field(
        default=None,
        description="CreDtTm of the original message, if known.",
    )
    group_status: StatusCode | None = Field(
        default=None,
        description="Status applying to the entire original group, if reported.",
    )


class TransactionStatus(BaseModel):
    """Status report for a single transaction from the original pacs.008."""

    model_config = ConfigDict(extra="forbid")

    original_end_to_end_id: str | None = Field(
        default=None,
        description="EndToEndId of the original transaction. Optional in the "
        "schema but almost always present in practice.",
    )
    original_transaction_id: str | None = Field(
        default=None,
        description="TxId assigned by the original instructing agent.",
    )
    status: StatusCode = Field(
        description="The current status of this transaction.",
    )
    status_reasons: list[StatusReason] = Field(
        default_factory=list,
        description="Zero or more reasons explaining the status. Always "
        "empty for ACSC/ACSP success cases; typically populated for RJCT.",
    )
    acceptance_datetime: datetime | None = Field(
        default=None,
        description="When the transaction reached its current status.",
    )


class GroupHeader(BaseModel):
    """Group-level metadata for the status report itself."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(description="MsgId of this status report.")
    creation_datetime: datetime = Field(description="When this report was generated.")


class ParsedPacs002(BaseModel):
    """A fully-parsed pacs.002.001.10 FI-to-FI Payment Status Report."""

    model_config = ConfigDict(extra="forbid")

    group_header: GroupHeader
    original_group_info: OriginalGroupInfo
    transaction_statuses: list[TransactionStatus]
