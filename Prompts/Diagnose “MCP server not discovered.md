
```text
Diagnose why VS Code GitHub Copilot is not discovering the OfferProof stdio MCP server. Do not redesign the business logic.

Inspect `.vscode/mcp.json`, path expansion, Windows Python launcher availability, Python 3.13 selection, working directory, vendored imports, installed official MCP SDK version/API, server startup, JSON-RPC framing, stderr logs, stdout contamination, and VS Code MCP logs. Run the launcher outside VS Code in a way that does not corrupt stdio, and use an SDK in-memory client or MCP Inspector only if already available; do not introduce Node/Postman as a requirement.

Fix repository-owned defects. Preserve stdout exclusively for protocol traffic. Provide the exact root cause, changed files, verification commands, and the shortest user steps to reload/start the server. If the remaining blocker is a VS Code permission/trust prompt or unsupported client feature, say so explicitly rather than masking it in code.