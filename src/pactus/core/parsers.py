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
from pactus.core.domain.pain001 import (
    GroupHeader as Pain001GroupHeader,
)
from pactus.core.domain.pain001 import (
    ParsedPain001,
    PaymentInformation,
)
from pactus.core.domain.pain001 import (
    Transaction as Pain001Transaction,
)
from pactus.generated.pacs_002_001_10 import Document as Pacs002Document
from pactus.generated.pacs_008_001_08 import Document as Pacs008Document
from pactus.generated.pain_001_001_09 import Document as Pain001Document


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


# ---------------------------------------------------------------------------
# Shared projection helpers (pain.001 + future slices)
# ---------------------------------------------------------------------------


def _project_party(party) -> Party:  # type: ignore[no-untyped-def]
    """Project a xsdata PartyIdentification into the domain Party."""
    return Party(name=party.nm)


def _project_agent(agt) -> Agent:  # type: ignore[no-untyped-def]
    """Project a xsdata BranchAndFinancialInstitutionIdentification into domain Agent."""
    bic = None
    if agt.fin_instn_id is not None:  # pragma: no branch
        bic = agt.fin_instn_id.bicfi
    return Agent(bic=bic)


# ---------------------------------------------------------------------------
# pain.001.001.09 parser
# ---------------------------------------------------------------------------


def parse_pain001(xml: str) -> ParsedPain001:
    """Parse a pain.001.001.09 Customer Credit Transfer Initiation.

    Raises:
        UnsafeXmlError: if the input contains DOCTYPE or ENTITY declarations.
        ValidationError: if the XML doesn't conform to pain.001.001.09.
    """
    _reject_unsafe_xml(xml)
    generated = _xml_parser.from_string(xml, Pain001Document)
    return _project_pain001(generated)


def _project_pain001(doc: Pain001Document) -> ParsedPain001:
    """Project the xsdata-generated Pain001Document into the domain model."""
    cstmr = doc.cstmr_cdt_trf_initn

    grp_hdr = cstmr.grp_hdr
    initiating_name = grp_hdr.initg_pty.nm if grp_hdr.initg_pty is not None else None

    return ParsedPain001(
        group_header=Pain001GroupHeader(
            message_id=grp_hdr.msg_id,
            creation_datetime=grp_hdr.cre_dt_tm.to_datetime(),
            number_of_transactions=int(grp_hdr.nb_of_txs),
            control_sum=str(grp_hdr.ctrl_sum) if grp_hdr.ctrl_sum is not None else None,
            initiating_party_name=initiating_name,
        ),
        payment_informations=[_project_payment_information(pmt) for pmt in cstmr.pmt_inf],
    )


def _project_payment_information(pmt) -> PaymentInformation:  # type: ignore[no-untyped-def]
    """Project one xsdata PaymentInstruction30 into the domain PaymentInformation."""
    debtor_iban = None
    if pmt.dbtr_acct is not None and pmt.dbtr_acct.id is not None:
        debtor_iban = pmt.dbtr_acct.id.iban

    svc_lvl_code = None
    ctgy_purp_code = None
    if pmt.pmt_tp_inf is not None:
        if pmt.pmt_tp_inf.svc_lvl:
            svc_lvl_code = pmt.pmt_tp_inf.svc_lvl[0].cd
        if pmt.pmt_tp_inf.ctgy_purp is not None:
            ctgy_purp_code = pmt.pmt_tp_inf.ctgy_purp.cd

    return PaymentInformation(
        payment_information_id=pmt.pmt_inf_id,
        payment_method=pmt.pmt_mtd.value,
        batch_booking=pmt.btch_bookg,
        number_of_transactions=int(pmt.nb_of_txs) if pmt.nb_of_txs is not None else None,
        control_sum=str(pmt.ctrl_sum) if pmt.ctrl_sum is not None else None,
        requested_execution_date=pmt.reqd_exctn_dt.dt.to_date(),
        debtor=_project_party(pmt.dbtr),
        debtor_account_iban=debtor_iban,
        debtor_agent=_project_agent(pmt.dbtr_agt),
        charge_bearer=pmt.chrg_br.value if pmt.chrg_br is not None else None,
        service_level_code=svc_lvl_code,
        category_purpose_code=ctgy_purp_code,
        transactions=[_project_pain001_transaction(tx) for tx in pmt.cdt_trf_tx_inf],
    )


def _project_pain001_transaction(tx) -> Pain001Transaction:  # type: ignore[no-untyped-def]
    """Project one xsdata CreditTransferTransaction34 into a domain Transaction."""
    creditor_iban = None
    if tx.cdtr_acct is not None and tx.cdtr_acct.id is not None:
        creditor_iban = tx.cdtr_acct.id.iban

    remittance_lines: list[str] = []
    if tx.rmt_inf is not None and tx.rmt_inf.ustrd:
        remittance_lines = list(tx.rmt_inf.ustrd)

    creditor_agent = _project_agent(tx.cdtr_agt) if tx.cdtr_agt is not None else None

    return Pain001Transaction(
        end_to_end_id=tx.pmt_id.end_to_end_id,
        instruction_id=tx.pmt_id.instr_id,
        amount=Amount(
            value=tx.amt.instd_amt.value,
            currency=tx.amt.instd_amt.ccy,
        ),
        creditor=_project_party(tx.cdtr),
        creditor_account_iban=creditor_iban,
        creditor_agent=creditor_agent,
        remittance_info=remittance_lines,
    )
