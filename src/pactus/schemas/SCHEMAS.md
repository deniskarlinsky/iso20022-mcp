# Vendored ISO 20022 Schemas

These XSD files are the official ISO 20022 message schemas published by
ISO20022.org and republished under MIT license by the phoughton/pyiso20022
project on GitHub. They are vendored here to enable XSD-based validation
and xsdata-driven Pydantic model generation without requiring users of
pactus-mcp to register with iso20022.org.

## Provenance

- **Source repository:** https://github.com/phoughton/pyiso20022
- **Source license:** MIT
- **Pinned commit SHA:** cfb785fcc5174b09adee1419eb83743c85c79398
- **Retrieved on:** 2026-05-09
- **Original publisher:** ISO20022.org (registration authority)
- **Standard governance:** ISO 20022 — Universal financial industry message scheme

## Vendored files

| File | Purpose | Source path | SHA-256 |
|------|---------|-------------|---------|
| pacs.008.001.08.xsd | FI-to-FI Customer Credit Transfer | xsd/payments_clearing_and_settlement/pacs.008/pacs.008.001.08.xsd | cf048155f70cacd03f1f1dfadf66cba8752be93c249c267351782fd6adb023f7 |
| pacs.002.001.10.xsd | FI-to-FI Payment Status Report | xsd/payments_clearing_and_settlement/pacs.002/pacs.002.001.10.xsd | d14da6304db5178b1afc7d8ed6cc6073e6e1a143fc79d9ba66d3246d4a654e90 |
| pain.001.001.09.xsd | Customer Credit Transfer Initiation | xsd/payments_initiation/pain.001/pain.001.001.09.xsd | de038b373e47b0077b1832ddd81f4b2f1eb25d35721f62da1e38b7f5a09fda24 |
| camt.053.001.08.xsd | Bank-to-Customer Statement | xsd/cash_management/camt.053/camt.053.001.08.xsd | 338e9cb0c9989b5181802a7b773eece070d6815fc9d6483ac0579117bc24ccba |

## Updating

To update a schema to a new version:
1. Identify the new pinned commit SHA from phoughton/pyiso20022.
2. Download the new file, compute SHA-256, replace the file and the hash
   in this table.
3. Re-run xsdata generation: `uv run xsdata generate src/pactus/schemas --config .xsdata.xml`
4. Update the curated domain models in `src/pactus/core/domain.py` if
   field structures changed.
5. Bump the pinned commit SHA in this file's "Provenance" section if
   updating multiple files at once.

## Why we vendor instead of fetching at runtime

XSD compilation requires the full schema graph on disk. Vendoring makes
the build hermetic and reproducible — same source SHA, same hashes, same
generated models. Runtime fetching would introduce network dependency,
non-determinism, and a supply-chain attack surface.
