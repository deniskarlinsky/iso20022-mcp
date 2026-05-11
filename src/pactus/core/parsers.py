"""Parsers from raw XML to clean domain models.

Each parser is the only place in the codebase where the ugly
xsdata-generated class names appear. Everything downstream sees only
the clean curated models from pactus.core.domain.
"""

from __future__ import annotations

import lxml.etree as _etree
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata_pydantic.bindings import XmlParser

from pactus.core.domain.common import Agent, Amount, Party
from pactus.core.domain.pacs002 import (
    GroupHeader as Pacs002GroupHeader,
)
from pactus.core.domain.pacs002 import (
    OriginalGroupInfo,
    ParsedPacs002,
    StatusReason,
    TransactionStatus,
)
from pactus.core.domain.pacs008 import (
    GroupHeader,
    Pacs008Transaction,
    ParsedPacs008,
)
from pactus.generated.pacs_002_001_10 import Document as Pacs002Document
from pactus.generated.pacs_008_001_08 import Document as Pacs008Document


class UnsafeXmlError(ValueError):
    """Raised when input XML contains constructs disallowed for safety reasons.

    ISO 20022 messages never legitimately contain DOCTYPE or ENTITY
    declarations. Their presence indicates either malformed input or an
    attempted XXE / entity-expansion attack. Inherits from ValueError so
    existing ``except (ValueError, ValidationError)`` handlers catch it.
    """


_lxml_parser = _etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    huge_tree=False,
    load_dtd=False,
    dtd_validation=False,
)

_xml_parser = XmlParser(
    config=ParserConfig(fail_on_unknown_properties=False, load_dtd=False),
)


def _reject_unsafe_xml(xml: str) -> None:
    """Reject XML that contains DOCTYPE or ENTITY declarations.

    This runs *before* the XML is handed to any parser, so even if the
    underlying parser were misconfigured, malicious DTDs cannot reach
    entity-resolution code paths. Case-insensitive because XML is
    case-sensitive but defensive parsing is not — odd casing in a hostile
    payload is still hostile.
    """
    lowered = xml.lstrip().lower()
    prolog_end = xml.find(">", xml.find("<")) if "<" in xml else -1
    scan_window = lowered[: min(4096, len(lowered) if prolog_end < 0 else prolog_end + 4096)]
    if "<!doctype" in scan_window:
        raise UnsafeXmlError("DOCTYPE declarations are not permitted in ISO 20022 input")
    # Defense-in-depth: a bare <!ENTITY without an enclosing <!DOCTYPE is not
    # well-formed XML, and entities inside a <!DOCTYPE are caught by the
    # branch above. Kept in case the scan window or upstream parser ever
    # changes shape; excluded from coverage because it is unreachable today.
    if "<!entity" in scan_window:
        raise UnsafeXmlError(  # pragma: no cover
            "ENTITY declarations are not permitted in ISO 20022 input"
        )


def parse_pacs008(xml: str) -> ParsedPacs008:
    """Parse a pacs.008.001.08 XML message into a curated domain model.

    Raises:
        UnsafeXmlError: If the input contains DOCTYPE or ENTITY declarations.
        pydantic.ValidationError: If the XML cannot be mapped to a valid
            ParsedPacs008. This includes XSD violations, missing required
            fields, or out-of-range values.
        lxml.etree.XMLSyntaxError: If the XML is not well-formed.
    """
    _reject_unsafe_xml(xml)
    generated = _xml_parser.from_string(xml, Pacs008Document)
    body = generated.fito_ficstmr_cdt_trf
    grp = body.grp_hdr

    group_header = GroupHeader(
        message_id=grp.msg_id,
        creation_datetime=grp.cre_dt_tm.to_datetime(),
        number_of_transactions=int(grp.nb_of_txs),
        settlement_method=grp.sttlm_inf.sttlm_mtd.value,
    )

    transactions = [_project_transaction(tx) for tx in body.cdt_trf_tx_inf]

    return ParsedPacs008(group_header=group_header, transactions=transactions)


def _project_transaction(tx) -> Pacs008Transaction:  # type: ignore[no-untyped-def]
    """Project one xsdata-generated transaction into a clean domain transaction.

    The argument is intentionally untyped — its type is the deeply-nested
    generated class with the ugly snake-cased acronym names, and importing
    it here just for the annotation would leak generated types into our
    annotation surface. Type checking still works at the call site.
    """
    settlement_date = None
    if tx.intr_bk_sttlm_dt is not None:
        settlement_date = tx.intr_bk_sttlm_dt.to_date()

    # The ``is not None`` guards on dbtr_agt/cdtr_agt and their fin_instn_id
    # are defense-in-depth: the generated schema marks both as required, so
    # the False branch is unreachable today. ``# pragma: no branch`` keeps
    # the guards in place (in case the schema or generated code ever changes
    # shape) without forcing a coverage gap on an unreachable path.
    debtor_agent = None
    if tx.dbtr_agt is not None and tx.dbtr_agt.fin_instn_id is not None:  # pragma: no branch
        debtor_agent = Agent(bic=tx.dbtr_agt.fin_instn_id.bicfi)

    creditor_agent = None
    if tx.cdtr_agt is not None and tx.cdtr_agt.fin_instn_id is not None:  # pragma: no branch
        creditor_agent = Agent(bic=tx.cdtr_agt.fin_instn_id.bicfi)

    remittance_info = None
    if tx.rmt_inf is not None and tx.rmt_inf.ustrd:
        remittance_info = (
            tx.rmt_inf.ustrd[0] if isinstance(tx.rmt_inf.ustrd, list) else tx.rmt_inf.ustrd
        )

    return Pacs008Transaction(
        end_to_end_id=tx.pmt_id.end_to_end_id,
        instruction_id=tx.pmt_id.instr_id,
        transaction_id=tx.pmt_id.tx_id,
        settlement_amount=Amount(
            value=tx.intr_bk_sttlm_amt.value,
            currency=tx.intr_bk_sttlm_amt.ccy,
        ),
        settlement_date=settlement_date,
        charge_bearer=tx.chrg_br.value,
        debtor=Party(name=tx.dbtr.nm),
        debtor_agent=debtor_agent,
        creditor=Party(name=tx.cdtr.nm),
        creditor_agent=creditor_agent,
        remittance_info=remittance_info,
    )


def parse_pacs002(xml: str) -> ParsedPacs002:
    """Parse a pacs.002.001.10 FI-to-FI Payment Status Report.

    Raises:
        UnsafeXmlError: if the input contains DOCTYPE or ENTITY declarations.
        ValidationError: if the XML doesn't conform to pacs.002.001.10.
    """
    _reject_unsafe_xml(xml)
    generated = _xml_parser.from_string(xml, Pacs002Document)
    return _project_pacs002(generated)


def _project_pacs002(doc: Pacs002Document) -> ParsedPacs002:
    """Project the xsdata-generated Pacs002Document into the curated domain model."""
    report = doc.fito_fipmt_sts_rpt
    if not report.orgnl_grp_inf_and_sts:
        raise ValueError("pacs.002 document is missing OrgnlGrpInfAndSts")

    grp_hdr = report.grp_hdr
    orig_grp = report.orgnl_grp_inf_and_sts[0]

    return ParsedPacs002(
        group_header=Pacs002GroupHeader(
            message_id=grp_hdr.msg_id,
            creation_datetime=grp_hdr.cre_dt_tm.to_datetime(),
        ),
        original_group_info=OriginalGroupInfo(
            original_message_id=orig_grp.orgnl_msg_id,
            original_message_name_id=orig_grp.orgnl_msg_nm_id,
            original_creation_datetime=(
                orig_grp.orgnl_cre_dt_tm.to_datetime()
                if orig_grp.orgnl_cre_dt_tm is not None
                else None
            ),
            group_status=orig_grp.grp_sts,  # type: ignore[arg-type]
        ),
        transaction_statuses=[_project_transaction_status(tx) for tx in report.tx_inf_and_sts],
    )


def _project_transaction_status(tx) -> TransactionStatus:  # type: ignore[no-untyped-def]
    """Project one xsdata-generated TxInfAndSts into the domain TransactionStatus."""
    if tx.tx_sts is None:
        raise ValueError("pacs.002 transaction status is missing required TxSts")

    return TransactionStatus(
        original_end_to_end_id=tx.orgnl_end_to_end_id,
        original_transaction_id=tx.orgnl_tx_id,
        status=tx.tx_sts,
        status_reasons=[_project_status_reason(rsn) for rsn in tx.sts_rsn_inf],
        acceptance_datetime=(
            tx.accptnc_dt_tm.to_datetime() if tx.accptnc_dt_tm is not None else None
        ),
    )


def _project_status_reason(rsn) -> StatusReason:  # type: ignore[no-untyped-def]
    """Project xsdata StsRsnInf into the domain StatusReason."""
    code = None
    proprietary = None
    if rsn.rsn is not None:
        code = rsn.rsn.cd
        proprietary = rsn.rsn.prtry

    return StatusReason(
        code=code or proprietary or "UNKNOWN",
        proprietary=proprietary if code else None,
        originator_name=rsn.orgtr.nm if rsn.orgtr is not None else None,
        additional_information=list(rsn.addtl_inf),
    )
