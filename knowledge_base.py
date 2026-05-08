import chromadb
from chromadb.utils import embedding_functions

CHUNKS: list[dict[str, str]] = [
  {
    "id": "pacs008-purpose",
    "topic": "pacs.008",
    "text": (
      "pacs.008 (FIToFICustomerCreditTransfer) is the ISO 20022 message used between "
      "financial institutions to settle customer-initiated credit transfers. The debtor "
      "agent sends it to the creditor agent (directly or via clearing), carrying the "
      "interbank settlement amount and the underlying customer details."
    ),
  },
  {
    "id": "pain001-purpose",
    "topic": "pain.001",
    "text": (
      "pain.001 (CustomerCreditTransferInitiation) is the ISO 20022 message a corporate "
      "or retail customer sends to its bank to initiate one or more credit transfers. "
      "It is a request for payment instruction, not a settlement message — the bank "
      "translates it into pacs.008 for interbank settlement."
    ),
  },
  {
    "id": "camt053-purpose",
    "topic": "camt.053",
    "text": (
      "camt.053 (BankToCustomerStatement) is the ISO 20022 end-of-day statement a bank "
      "sends to its customer. It reports opening and closing balances and lists every "
      "booked entry on the account for a given period. It is the ISO 20022 successor to "
      "the legacy SWIFT MT940 statement."
    ),
  },
  {
    "id": "swift-migration-deadline",
    "topic": "migration",
    "text": (
      "The SWIFT cross-border payments network is migrating from legacy MT messages to "
      "ISO 20022. The coexistence period for MT and MX (ISO 20022) ends in November 2027, "
      "after which CBPR+ flows must use ISO 20022 exclusively. Banks, fintechs, and "
      "corporates are running migration programs to meet this deadline."
    ),
  },
  {
    "id": "bic-codes",
    "topic": "identifiers",
    "text": (
      "A BIC (Business Identifier Code, formerly SWIFT code) uniquely identifies a "
      "financial institution. It is 8 or 11 characters: 4-letter bank code, 2-letter "
      "ISO country code, 2-character location code, and an optional 3-character branch "
      "code. In ISO 20022 it appears as <BICFI> inside <FinInstnId>."
    ),
  },
  {
    "id": "iban-format",
    "topic": "identifiers",
    "text": (
      "An IBAN (International Bank Account Number) identifies a specific bank account "
      "internationally. It begins with a 2-letter ISO country code, followed by 2 check "
      "digits, then a country-specific BBAN of up to 30 alphanumeric characters. In "
      "ISO 20022 messages it appears as <IBAN> inside <Acct>/<Id>."
    ),
  },
  {
    "id": "settlement-methods",
    "topic": "settlement",
    "text": (
      "ISO 20022 settlement methods (<SttlmMtd>) include CLRG (settled through a "
      "clearing system), INDA (settled on the books of the instructed agent), INGA "
      "(settled on the books of the instructing agent), and COVE (cover method using a "
      "separate payment between correspondents). The choice affects routing and liquidity."
    ),
  },
  {
    "id": "group-header-fields",
    "topic": "structure",
    "text": (
      "Every ISO 20022 payment message starts with a GroupHeader (<GrpHdr>) containing "
      "MsgId (the unique message identifier assigned by the sender), CreDtTm (creation "
      "date/time in ISO 8601), NbOfTxs (number of transactions in the message), and "
      "often CtrlSum (the sum of all transaction amounts as a control total)."
    ),
  },
  {
    "id": "agent-roles",
    "topic": "parties",
    "text": (
      "In a credit transfer the DebtorAgent (<DbtrAgt>) is the bank servicing the "
      "debtor (the payer), and the CreditorAgent (<CdtrAgt>) is the bank servicing the "
      "creditor (the payee). Funds flow from the debtor's account at the debtor agent "
      "to the creditor's account at the creditor agent, possibly via intermediaries."
    ),
  },
  {
    "id": "end-to-end-id",
    "topic": "identifiers",
    "text": (
      "EndToEndId (<EndToEndId>) is a reference assigned by the originating party that "
      "is preserved unchanged through the entire payment chain. It lets the debtor and "
      "creditor reconcile a payment across systems even if intermediaries assign their "
      "own identifiers. It is mandatory in pain.001 and pacs.008."
    ),
  },
  {
    "id": "transaction-id",
    "topic": "identifiers",
    "text": (
      "TxId (<TxId>) is the unique transaction identifier assigned by the first "
      "instructing party in the interbank space (typically the debtor agent). Unlike "
      "EndToEndId, it lives in the FI-to-FI domain and is used by clearing/settlement "
      "systems to track an individual payment leg."
    ),
  },
  {
    "id": "control-sum",
    "topic": "structure",
    "text": (
      "CtrlSum (<CtrlSum>) is the arithmetic sum of all individual transaction amounts "
      "within a message or payment information block. Receivers compare it against the "
      "totals they compute from the line items as a basic integrity check; a mismatch "
      "indicates a corrupted or incomplete file."
    ),
  },
  {
    "id": "balance-codes",
    "topic": "camt.053",
    "text": (
      "Balance type codes in camt.053 <Bal>/<Tp>/<CdOrPrtry>/<Cd> include OPBD (Opening "
      "Booked balance at the start of the period), CLBD (Closing Booked balance at the "
      "end), OPAV / CLAV (opening and closing available balances), and ITBD (interim "
      "booked, used for intra-day statements like camt.052)."
    ),
  },
  {
    "id": "fi-to-fi-flow",
    "topic": "flow",
    "text": (
      "A typical FI-to-FI customer credit transfer flow: the customer sends pain.001 to "
      "its bank; the debtor agent issues pacs.008 to the creditor agent (directly or "
      "through a clearing system); the creditor agent credits the beneficiary and may "
      "send pacs.002 status back; both customers receive camt.053 statements at end of day."
    ),
  },
  {
    "id": "credit-transfer-vs-statement",
    "topic": "concepts",
    "text": (
      "Customer credit transfer messages (pain.001, pacs.008) are payment instructions — "
      "they request that money be moved. Bank statement messages (camt.053, camt.052) "
      "are reporting — they describe what already happened on an account. Validating an "
      "instruction is about required routing data; reading a statement is about "
      "reconciling balances and entries."
    ),
  },
]


_client = chromadb.PersistentClient(path="./chroma_db")
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
  model_name="all-MiniLM-L6-v2"
)


def _collection():
  return _client.get_or_create_collection(name="iso20022", embedding_function=_embed_fn)


def build() -> None:
  """(Re)populate the iso20022 collection with the chunks defined above."""
  col = _collection()
  col.upsert(
    ids=[c["id"] for c in CHUNKS],
    documents=[c["text"] for c in CHUNKS],
    metadatas=[{"topic": c["topic"]} for c in CHUNKS],
  )


def query(question: str, n_results: int = 3) -> list[dict]:
  """Return the top n_results matching chunks for question."""
  col = _collection()
  res = col.query(query_texts=[question], n_results=n_results)
  return [
    {"id": id_, "topic": meta.get("topic"), "text": doc, "distance": dist}
    for id_, doc, meta, dist in zip(
      res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    )
  ]


if __name__ == "__main__":
  build()
  print(f"Indexed {len(CHUNKS)} chunks in ./chroma_db (collection: iso20022)")
  print()
  print("Test query: 'what is pacs.008'")
  print("-" * 60)
  for i, hit in enumerate(query("what is pacs.008"), 1):
    print(f"{i}. [{hit['topic']}] {hit['id']} (distance={hit['distance']:.4f})")
    print(f"   {hit['text']}")
    print()
