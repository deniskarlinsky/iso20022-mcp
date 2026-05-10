"""Parsers from raw XML to clean domain models.

Each parser is the only place in the codebase where the ugly
xsdata-generated class names appear. Everything downstream sees only
the clean curated models from pactus.core.domain.
"""

from __future__ import annotations

from xsdata_pydantic.bindings import XmlParser

from pactus.core.domain.common import Agent, Amount, Party
from pactus.core.domain.pacs008 import (
    GroupHeader,
    Pacs008Transaction,
    ParsedPacs008,
)
from pactus.generated.pacs_008_001_08 import Document as Pacs008Document

_xml_parser = XmlParser()


def parse_pacs008(xml: str) -> ParsedPacs008:
    """Parse a pacs.008.001.08 XML message into a curated domain model.

    Raises:
        pydantic.ValidationError: If the XML cannot be mapped to a valid
            ParsedPacs008. This includes XSD violations, missing required
            fields, or out-of-range values.
        lxml.etree.XMLSyntaxError: If the XML is not well-formed.
    """
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

    debtor_agent = None
    if tx.dbtr_agt is not None and tx.dbtr_agt.fin_instn_id is not None:
        debtor_agent = Agent(bic=tx.dbtr_agt.fin_instn_id.bicfi)

    creditor_agent = None
    if tx.cdtr_agt is not None and tx.cdtr_agt.fin_instn_id is not None:
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
