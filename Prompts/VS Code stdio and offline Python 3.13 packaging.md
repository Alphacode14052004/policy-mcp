```text
Make OfferProof MCP reliably runnable in VS Code GitHub Copilot Agent mode on Windows with Python 3.13 and no pip use on the target machine.

Inspect and fix `run_mcp.py`, `.vscode/mcp.json`, dependency pins, `vendor/README.md`, and the PowerShell build/verify/smoke scripts. Use the current installed official MCP Python SDK 2.x API after inspecting its docs/examples; do not use obsolete or guessed APIs. Pin the exact verified versions. The build script must populate `vendor/` on a compatible Windows x64 Python 3.13 machine rather than copying a virtual environment. The launcher must prepend repository and vendor paths before imports and must be independent of caller cwd.

Protect stdio JSON-RPC: no debug or application logging may reach stdout. Direct diagnostics to SQLite, a rotating file, or stderr. Add an automated test that detects stdout contamination. Verify the server starts, tools/resources/prompts enumerate, and the canonical mixed-cart smoke journey completes. Where the current machine cannot prove Windows or VS Code behavior, produce reproducible checks and state the limitation rather than claiming success.

Also document why stdio is the local-demo choice and why authenticated Streamable HTTP is the production roadmap. Postman must not be required. Report commands, results, and the exact VS Code demo steps.