import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

from fastmcp import FastMCP
from knowledge_base import query as kb_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("iso20022-mcp")

mcp = FastMCP("iso20022-mcp")

PACS008_NS = {"iso": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}
PAIN001_NS = {"iso": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}
CAMT053_NS = {"iso": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"}

_MSGID_RE = re.compile(r"<(?:[^:>\s]+:)?MsgId\b[^>]*>([^<]+)</")


def _empty(xml: str) -> bool:
  return not xml or not xml.strip()


def _log_call(tool: str, xml: str) -> None:
  if not xml:
    logger.info("tool=%s input_preview=''", tool)
    return
  m = _MSGID_RE.search(xml)
  if m:
    logger.info("tool=%s message_id=%s", tool, m.group(1).strip())
  else:
    logger.info("tool=%s input_preview=%r", tool, xml[:50])


@mcp.tool()
def parse_pacs008(xml: str) -> dict[str, Any]:
  """Parse a pacs.008 (FIToFICustomerCreditTransfer) ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08.
  Output: dict with keys message_id, amount, currency, debtor, debtor_bic, creditor,
          creditor_bic; or {"error": "..."} on failure.
  """
  _log_call("parse_pacs008", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)
    return {
      "message_id": root.find(".//iso:MsgId", PACS008_NS).text,
      "amount": root.find(".//iso:IntrBkSttlmAmt", PACS008_NS).text,
      "currency": root.find(".//iso:IntrBkSttlmAmt", PACS008_NS).attrib["Ccy"],
      "debtor": root.find(".//iso:Dbtr/iso:Nm", PACS008_NS).text,
      "debtor_bic": root.find(".//iso:DbtrAgt//iso:BICFI", PACS008_NS).text,
      "creditor": root.find(".//iso:Cdtr/iso:Nm", PACS008_NS).text,
      "creditor_bic": root.find(".//iso:CdtrAgt//iso:BICFI", PACS008_NS).text,
    }
  except ET.ParseError as e:
    return {"error": f"XML parse error: {e}"}
  except AttributeError:
    return {"error": "missing required field"}


@mcp.tool()
def validate_pacs008(xml: str) -> dict[str, Any]:
  """Validate a pacs.008 ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08.
  Output: {"valid": True} if required fields are present; otherwise
          {"valid": False, "error": "..."}; or {"error": "..."} for empty input.
  """
  _log_call("validate_pacs008", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)
    required = [".//iso:MsgId", ".//iso:IntrBkSttlmAmt", ".//iso:Dbtr/iso:Nm",
                ".//iso:DbtrAgt//iso:BICFI", ".//iso:Cdtr/iso:Nm", ".//iso:CdtrAgt//iso:BICFI"]
    for path in required:
      if root.find(path, PACS008_NS) is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    if "Ccy" not in root.find(".//iso:IntrBkSttlmAmt", PACS008_NS).attrib:
      return {"valid": False, "error": "missing Ccy attribute on IntrBkSttlmAmt"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}


@mcp.tool()
def parse_pain001(xml: str) -> dict[str, Any]:
  """Parse a pain.001 (CustomerCreditTransferInitiation) ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:pain.001.001.09.
  Output: dict with keys message_id, number_of_transactions, control_sum, debtor,
          debtor_iban, creditor; or {"error": "..."} on failure.
  """
  _log_call("parse_pain001", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)
    return {
      "message_id": root.find(".//iso:GrpHdr/iso:MsgId", PAIN001_NS).text,
      "number_of_transactions": root.find(".//iso:GrpHdr/iso:NbOfTxs", PAIN001_NS).text,
      "control_sum": root.find(".//iso:GrpHdr/iso:CtrlSum", PAIN001_NS).text,
      "debtor": root.find(".//iso:Dbtr/iso:Nm", PAIN001_NS).text,
      "debtor_iban": root.find(".//iso:DbtrAcct/iso:Id/iso:IBAN", PAIN001_NS).text,
      "creditor": root.find(".//iso:CdtTrfTxInf/iso:Cdtr/iso:Nm", PAIN001_NS).text,
    }
  except ET.ParseError as e:
    return {"error": f"XML parse error: {e}"}
  except AttributeError:
    return {"error": "missing required field"}


@mcp.tool()
def validate_pain001(xml: str) -> dict[str, Any]:
  """Validate a pain.001 ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:pain.001.001.09.
  Output: {"valid": True} if required fields are present; otherwise
          {"valid": False, "error": "..."}; or {"error": "..."} for empty input.
  """
  _log_call("validate_pain001", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)
    required = [".//iso:GrpHdr/iso:MsgId", ".//iso:GrpHdr/iso:NbOfTxs", ".//iso:GrpHdr/iso:CtrlSum",
                ".//iso:Dbtr/iso:Nm", ".//iso:DbtrAcct/iso:Id/iso:IBAN", ".//iso:CdtTrfTxInf/iso:Cdtr/iso:Nm"]
    for path in required:
      if root.find(path, PAIN001_NS) is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}


@mcp.tool()
def parse_camt053(xml: str) -> dict[str, Any]:
  """Parse a camt.053 (BankToCustomerStatement) ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:camt.053.001.08.
  Output: dict with keys message_id, account_iban, opening_balance, closing_balance,
          number_of_entries; opening_balance and closing_balance are
          {"amount": str, "currency": str} or None; or {"error": "..."} on failure.
  """
  _log_call("parse_camt053", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)

    def balance_for(code: str) -> dict[str, str] | None:
      for bal in root.findall(".//iso:Stmt/iso:Bal", CAMT053_NS):
        cd = bal.find("./iso:Tp/iso:CdOrPrtry/iso:Cd", CAMT053_NS)
        if cd is not None and cd.text == code:
          amt = bal.find("./iso:Amt", CAMT053_NS)
          return {"amount": amt.text, "currency": amt.attrib["Ccy"]}
      return None

    return {
      "message_id": root.find(".//iso:GrpHdr/iso:MsgId", CAMT053_NS).text,
      "account_iban": root.find(".//iso:Stmt/iso:Acct/iso:Id/iso:IBAN", CAMT053_NS).text,
      "opening_balance": balance_for("OPBD"),
      "closing_balance": balance_for("CLBD"),
      "number_of_entries": root.find(".//iso:Stmt/iso:TxsSummry/iso:TtlNtries/iso:NbOfNtries", CAMT053_NS).text,
    }
  except ET.ParseError as e:
    return {"error": f"XML parse error: {e}"}
  except AttributeError:
    return {"error": "missing required field"}


@mcp.tool()
def validate_camt053(xml: str) -> dict[str, Any]:
  """Validate a camt.053 ISO 20022 message.

  Input: XML string in namespace urn:iso:std:iso:20022:tech:xsd:camt.053.001.08.
  Output: {"valid": True} if required fields and at least one Bal entry are present;
          otherwise {"valid": False, "error": "..."}; or {"error": "..."} for empty input.
  """
  _log_call("validate_camt053", xml)
  if _empty(xml):
    return {"error": "empty input"}
  try:
    root = ET.fromstring(xml)
    required = [".//iso:GrpHdr/iso:MsgId", ".//iso:Stmt/iso:Acct/iso:Id/iso:IBAN"]
    for path in required:
      if root.find(path, CAMT053_NS) is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    if not root.findall(".//iso:Stmt/iso:Bal", CAMT053_NS):
      return {"valid": False, "error": "missing required element: at least one Stmt/Bal"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}


@mcp.tool()
def explain_iso20022(question: str) -> dict[str, Any]:
  """Answer a question about ISO 20022 using the built-in knowledge base.

  Input: a natural-language question about ISO 20022 concepts, message types, or fields.
  Output: {"answer": str, "sources": list[str]} with the top matching knowledge chunks
          and their topic labels; or {"error": "..."} on empty input.
  """
  _log_call("explain_iso20022", question)
  if _empty(question):
    return {"error": "empty input"}
  hits = kb_query(question, n_results=3)
  return {
    "answer": "\n\n".join(h["text"] for h in hits),
    "sources": [h["topic"] for h in hits],
  }


if __name__ == "__main__":
  mcp.run()
