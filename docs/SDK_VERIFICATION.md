# Environment and SDK verification

Verified environment: Windows 11 x64; VS Code CLI reports 1.134.0. `py -0p` initially reported **No installed Pythons found**. The bundled development interpreter is CPython 3.12.14 x64. An isolated official CPython 3.13.7 Windows x64 embeddable distribution was fetched under `.build/python313/` for target-runtime checks, without changing the system installation.

Official MCP **2.2.0** and all 28 transitive dependencies were fetched into isolated build paths. Exact package versions and wheel hashes are in `requirements.lock`; the populated target `vendor/` contains cp313/win_amd64 wheels and compatible pure-Python/abi3 wheels. `vendor/manifest.json` records package versions and per-file hashes. Source control ignores package contents and runtime artifacts.

Inspected installed source before authoring the adapter:

- `mcp/server/mcpserver/server.py`: `MCPServer`, public `list_tools`, `call_tool`, `resource`, `prompt`, and `run(transport="stdio")`.
- `mcp/types` / `mcp_types`: `Tool`, `ToolAnnotations`, `CallToolResult`, `TextContent`; snake_case fields `input_schema`, `output_schema`, `structured_content`, `is_error`.
- `mcp/client/client.py` and `_memory.py`: official `Client(server)` in-memory transport; discovery, resources, prompts and calls exercised in contract tests.
- `mcp/server/stdio.py` and Windows utility modules: `pywin32` bootstrap requires trusted `.pth` processing for a `pip --target` bundle. Launcher uses `site.addsitedir(vendor)` in addition to path prepending.

Official references: [Python SDK repository](https://github.com/modelcontextprotocol/python-sdk), [v2 migration overview](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md), [MCP package](https://pypi.org/project/mcp/2.2.0/), [CPython verification runtime release](https://www.python.org/downloads/release/python-3137/). Installed source and executed tests, not guessed examples, determined the adapter.

The package fetch was repository-local. Pip emitted an unrelated pre-existing bundled Flask/Jinja dependency warning while resolving `--target`; the isolated MCP imports, contract tests and target-runtime suite passed. No bundled runtime packages were replaced.

## Verified / unverified boundary

- Official SDK in-memory discovery and complete five-stage journey: verified by tests.
- Windows 3.13 SDK import, actual stdio subprocess JSON-RPC and startup from a different working directory: verified by tests.
- Offline SDK import and core smoke with socket connect/DNS functions blocked: verified by `scripts/offline_check.py`. This is not an OS-level network-disable test.
- PowerShell offline verification and smoke: results recorded in TEST_MATRIX and artifacts.
- Latest target suite after the presentation timing fix: 95 passed, zero failures/errors/skips on CPython 3.13.7 (`tests-presentation-timing.json`), including the reported timing failures, recovery, legacy cached responses, preview contracts and complete mixed-cart/sofa MCP SDK flows. Earlier preview, sofa and offline suites remain recorded at 84, 74 and 61 tests.
- Application version 1.3.0 is returned in server discovery and evaluation/status results; the launcher emits its version banner on stderr only. Exactly five tools remain. The VS Code configuration now enables documented `dev.watch` patterns for server Python and mock JSON changes; automatic reload in the user's live VS Code session is not asserted by SDK tests. Timing diagnostics do not implement host-side renderer or consumer-event capture.
- A fresh official SDK stdio subprocess using the configured VS Code command read both user-reported issued journeys successfully with server 1.3.0. `eval/results/presentation-timing-recovery.json` records their original issuance times, fresh clocks and unchanged DISCLOSURE_ISSUED/version 2 states. No presentation, acknowledgment or authorization was submitted. This verifies status recovery, not Copilot's currently connected process or live event capture.
- Target vendor wheels: fetched, hash locked, imported and exercised on actual Windows Python 3.13.7.
- Full `build_vendor.ps1` venv/ensurepip path on a normal installed Python 3.13: not executed here because only an embeddable 3.13 runtime was available. Its syntax, bounded path checks and incompatible-interpreter behavior were checked. The local build used explicit pip target flags from the available 3.12 build interpreter; no virtual environment was transferred.
- The active `.vscode/mcp.json` uses this workspace's verified `.build/python313/python.exe`. `.vscode/mcp.python-launcher.example.json` preserves the `py -3.13` configuration for a target with registered Python. Update the interpreter path when transferring the project. Copilot Agent UI launch, trust prompts and the 200 natural prompts are unverified.
- Optional MCP App: omitted. End-to-end installed SDK/VS Code App support and a rendered accessible card were not demonstrated. No unverified feature flag or invented SDK API is documented.

The development 3.12 tests and final target 3.13 tests are different environments; use the target artifacts for offline handoff. A source-only checkout has no vendor binaries until the build script runs or a verified vendor bundle is transferred.
