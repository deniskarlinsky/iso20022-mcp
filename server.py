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

if __name__ == "__main__":
  mcp.run()