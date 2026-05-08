import xml.etree.ElementTree as ET
from fastmcp import FastMCP

mcp = FastMCP("iso20022-mcp")

@mcp.tool()
def hello(name: str) -> str:
  """Say hello to someone."""
  return f"Hello {name} from Pactus MCP server!"

@mcp.tool()
def parse_pacs008(xml: str) -> dict:
  """Parse a pacs.008 ISO 20022 payment message and extract key fields."""
  root = ET.fromstring(xml)
  ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}

  return {
    "message_id": root.find(".//iso:MsgId", ns).text,
    "amount": root.find(".//iso:IntrBkSttlmAmt", ns).text,
    "currency": root.find(".//iso:IntrBkSttlmAmt", ns).attrib["Ccy"],
    "debtor": root.find(".//iso:Dbtr/iso:Nm", ns).text,
    "debtor_bic": root.find(".//iso:DbtrAgt//iso:BICFI", ns).text,
    "creditor": root.find(".//iso:Cdtr/iso:Nm", ns).text,
    "creditor_bic": root.find(".//iso:CdtrAgt//iso:BICFI", ns).text,
  }

@mcp.tool()
def validate_pacs008(xml: str) -> dict:
  """Validate that an XML string parses as a pacs.008 ISO 20022 payment message."""
  try:
    root = ET.fromstring(xml)
    ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}
    required = [".//iso:MsgId", ".//iso:IntrBkSttlmAmt", ".//iso:Dbtr/iso:Nm",
                ".//iso:DbtrAgt//iso:BICFI", ".//iso:Cdtr/iso:Nm", ".//iso:CdtrAgt//iso:BICFI"]
    for path in required:
      el = root.find(path, ns)
      if el is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    if "Ccy" not in root.find(".//iso:IntrBkSttlmAmt", ns).attrib:
      return {"valid": False, "error": "missing Ccy attribute on IntrBkSttlmAmt"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}

@mcp.tool()
def parse_pain001(xml: str) -> dict:
  """Parse a pain.001 ISO 20022 CustomerCreditTransferInitiation message and extract key fields."""
  root = ET.fromstring(xml)
  ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}

  return {
    "message_id": root.find(".//iso:GrpHdr/iso:MsgId", ns).text,
    "number_of_transactions": root.find(".//iso:GrpHdr/iso:NbOfTxs", ns).text,
    "control_sum": root.find(".//iso:GrpHdr/iso:CtrlSum", ns).text,
    "debtor": root.find(".//iso:Dbtr/iso:Nm", ns).text,
    "debtor_iban": root.find(".//iso:DbtrAcct/iso:Id/iso:IBAN", ns).text,
    "creditor": root.find(".//iso:CdtTrfTxInf/iso:Cdtr/iso:Nm", ns).text,
  }

@mcp.tool()
def validate_pain001(xml: str) -> dict:
  """Validate that an XML string parses as a pain.001 ISO 20022 CustomerCreditTransferInitiation message."""
  try:
    root = ET.fromstring(xml)
    ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}
    required = [".//iso:GrpHdr/iso:MsgId", ".//iso:GrpHdr/iso:NbOfTxs", ".//iso:GrpHdr/iso:CtrlSum",
                ".//iso:Dbtr/iso:Nm", ".//iso:DbtrAcct/iso:Id/iso:IBAN", ".//iso:CdtTrfTxInf/iso:Cdtr/iso:Nm"]
    for path in required:
      if root.find(path, ns) is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}

@mcp.tool()
def parse_camt053(xml: str) -> dict:
  """Parse a camt.053 ISO 20022 BankToCustomerStatement message and extract key fields."""
  root = ET.fromstring(xml)
  ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"}

  def balance_for(code: str) -> dict | None:
    for bal in root.findall(".//iso:Stmt/iso:Bal", ns):
      cd = bal.find("./iso:Tp/iso:CdOrPrtry/iso:Cd", ns)
      if cd is not None and cd.text == code:
        amt = bal.find("./iso:Amt", ns)
        return {"amount": amt.text, "currency": amt.attrib["Ccy"]}
    return None

  return {
    "message_id": root.find(".//iso:GrpHdr/iso:MsgId", ns).text,
    "account_iban": root.find(".//iso:Stmt/iso:Acct/iso:Id/iso:IBAN", ns).text,
    "opening_balance": balance_for("OPBD"),
    "closing_balance": balance_for("CLBD"),
    "number_of_entries": root.find(".//iso:Stmt/iso:TxsSummry/iso:TtlNtries/iso:NbOfNtries", ns).text,
  }

@mcp.tool()
def validate_camt053(xml: str) -> dict:
  """Validate that an XML string parses as a camt.053 ISO 20022 BankToCustomerStatement message."""
  try:
    root = ET.fromstring(xml)
    ns = {"iso": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"}
    required = [".//iso:GrpHdr/iso:MsgId", ".//iso:Stmt/iso:Acct/iso:Id/iso:IBAN"]
    for path in required:
      if root.find(path, ns) is None:
        return {"valid": False, "error": f"missing required element: {path}"}
    if not root.findall(".//iso:Stmt/iso:Bal", ns):
      return {"valid": False, "error": "missing required element: at least one Stmt/Bal"}
    return {"valid": True}
  except ET.ParseError as e:
    return {"valid": False, "error": f"XML parse error: {e}"}

if __name__ == "__main__":
  mcp.run()