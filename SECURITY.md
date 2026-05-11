# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

Older versions are not supported. Please upgrade to 1.0.x before reporting.

## Reporting a vulnerability

Use **GitHub's private vulnerability reporting**: go to the Security tab of this repository and click **Report a vulnerability**. Do not open a public issue.

Reports are acknowledged within 72 hours. Once triaged, a coordinated disclosure timeline is agreed with the reporter. We aim to ship a fix and publish a security advisory within the agreed window.

Do not include exploit code or sensitive reproduction details in any public channel before the advisory is published.

## Scope

**In scope:**

- Parsing logic in `pactus/core/parsers.py` and the domain models it populates
- MCP transport layer (`mcp_server.py`) and its input handling
- Build and release pipeline (CI workflows, dependency pinning, PyPI publishing)

**Out of scope:**

- Vulnerabilities in upstream dependencies (`fastmcp`, `xsdata`, `lxml`, `pydantic`). Report these to the respective upstream projects.
- Vulnerabilities that require a malicious Claude Desktop configuration file already in place. That scenario assumes a compromised user environment, which is outside this project's threat model.

## Coordinated disclosure

The default disclosure deadline is **90 days** from initial report acknowledgement. This may be shortened (with reporter agreement) if a fix is straightforward, or extended (with reporter agreement) if the fix requires coordination with upstream dependencies or downstream integrators. After the deadline, or upon fix release, a GitHub Security Advisory will be published.
