# OfferProof MCP

**Synthetic promotion gateway and evidence layer for agentic commerce.** Given a cart, OfferProof evaluates line items, returns every offer, issues exact versioned disclosure copy, records structured presentation and affirmative acknowledgment, and blocks checkout when protected facts change.

**SYNTHETIC HACKATHON DATA — NOT APPROVED LEGAL COPY. NOT FOR PRODUCTION.** All rates, approvals, policies, account references, merchants and outcomes are fictional. No Synchrony production or non-production services are called.

Intended production positioning: **“OfferProof deterministically enforces the exact policies and disclosure copy approved by Synchrony Legal and Compliance.”** This implementation enforces mock approvals only. It does not decide the law, make credit decisions, access consumer reports, process payments or implement servicing allocation.

## Quick start

The included local `vendor/` build targets **Windows x64 Python 3.13**. With a populated vendor bundle and registered Python 3.13:

```powershell
./scripts/verify_offline.ps1
./scripts/smoke_test.ps1
py -3.13 run_mcp.py
```

The last command speaks MCP on stdin/stdout; it is not a web server. **Waiting without further output is expected:** version 1.3.0 writes one startup line to stderr, then waits for an MCP client. Stdout stays reserved for JSON-RPC. Press Ctrl+C to stop a manually launched instance; VS Code launches its own process. In VS Code, open this folder, open `.vscode/mcp.json`, start `offerProof`, resolve workspace/MCP trust prompts, then open Copilot Chat in Agent mode. Attach `demo-data/mixed-cart.json` and enter:

> Buy this $700 appliance and $100 gift card using the Synchrony option that best fits me. I want to avoid surprise interest and keep payments near $120 a month.

No tool names, custom agent file or slash prompt are needed in that prompt. Discovery descriptions explain the sequence. The live Copilot cold-start evaluation has **not** been run here; automated SDK discovery and workflow tests are separate evidence.

This computer initially had no registered Python. An official embeddable 3.13.7 runtime was fetched to `.build/python313/` for isolated verification. Locally, run `& ./.build/python313/python.exe scripts/demo.py`. **The active `.vscode/mcp.json` already uses this local interpreter.** For a target with registered Python 3.13, copy `.vscode/mcp.python-launcher.example.json` over `.vscode/mcp.json`. On a target with a direct Python executable but no launcher, use its full path or `python` and omit `-3.13`. `.build/` is not transferred as part of the source, so update the interpreter path when transferring the project.

For a fresh clone without vendor packages, build on a compatible full Python 3.13 Windows x64 machine using `./scripts/build_vendor.ps1`, then transfer the source and populated vendor directory. Do not copy a virtual environment. Details and integrity checks: [vendor guide](vendor/README.md).

## Sofa with an existing gift card

Restart `offerProof` after updating the code, then use a fresh Agent chat and attach [the sofa payment fixture](demo-data/sofa-gift-card-redemption.json). Use a new start idempotency key for each new attempt; retrying an old key preserves its original result.

> Buy this $750 sofa using my existing $100 gift card as payment. Compare financing for the remaining balance. I want to avoid surprise interest and keep payments near $120 a month.

The registered product is `MOCK-SKU-SOFA` / `SOFA` / `GOODS`. The purchase total stays **$750**. The existing gift card is an `applied_tenders` entry, leaving **$650** to finance. Do not add it as a positive product line: that would mean buying a new gift card and make the purchase total $850. If the customer's meaning is ambiguous, clarify it first.

Mock offer version 1.1.0 explicitly applies thresholds to the eligible balance **after** payment. DI-6M qualifies for $650; EPP-12-0APR fails its $750 minimum. This is a fictional configured rule, not a claim about real merchant terms. Preparation requires confirmation of the $100 mock payment. No gift-card balance is checked and no redemption occurs.

```powershell
& ./.build/python313/python.exe scripts/demo.py --scenario sofa-gift-card-redemption
```

This command runs an automated fixture with simulated presentation and consent. The live agent must still ask the consumer to choose an offer and acknowledge the exact disclosure.

## Disclosures before selection

Since server version **1.2.0**, `disclosure_preview` is included on every eligible offer, including the standard fallback. The first response contains exact mock disclosure text, APRs, deadline, complete payment schedule, financed/applied/excluded amounts and pending payment confirmations. Copilot is instructed to display this information **before asking which offer the consumer wants to review**. Selection does not accept terms.

For the $650 sofa balance, the DI preview includes the purchase-date interest warning, March 29, 2027 deadline, five suggested $109 payments and a final $105. It labels these as payoff suggestions, not account minimum payments, and explains that the illustrated total excludes deferred interest if the deadline condition is missed. The standard option contains its exact mock terms and no invented payoff estimate.

After selection and payment confirmation, the server revalidates the current terms and issues a final disclosure. It must be displayed again before separate presentation/acknowledgment and authorization. A preview cannot serve as consent, a receipt or final presentation evidence. Old saved comparisons without previews require a fresh journey; original idempotency responses are preserved.

To inspect only the comparison, without selecting or simulating consent:

```powershell
& ./.build/python313/python.exe scripts/demo.py --scenario sofa-gift-card-redemption --preview-only --output eval/results/sofa-disclosure-previews.json
```

Restart the **VS Code-owned** server through `MCP: List Servers` → `offerProof` → Restart Server, then use `MCP: Reset Cached Tools`. Restarting a terminal process does not restart Copilot's connection. The workspace configuration now uses [VS Code's development file watcher](https://code.visualstudio.com/api/extension-guides/ai/mcp) for server Python and mock JSON changes. In MCP Output, the startup line should identify `OfferProof 1.3.0`; evaluation/status results also return `server_version`. Use a fresh start key for a new cart, or read status to recover an existing issued journey.

## Presentation timing recovery

Server **1.3.0** returns final disclosure `issued_at`, response `server_time`, status timing bounds and specific `result.presentation_error` details. Future, pre-issuance and older-than-15-minute presentation events are distinguished from acknowledgment timing and other evidence failures. Identical idempotent retries retain their original response and clock; status supplies a fresh clock, and corrected requests need a new key.

Display the final disclosure before capturing the actual renderer event. Never fill event timestamps from these diagnostic fields or guess them. A synthetic transaction date does not freeze the server's real UTC clock. If the host cannot capture required display checks and consumer events, explain that limitation and stop before acknowledgment. This update fixes diagnostics and recovery; it does not add a chat renderer integration. See [timing contract](docs/TOOL_CONTRACTS.md#presentation-timing-and-recovery-server-130) and [demo recovery](docs/DEMO_RUNBOOK.md#recovery-and-fallback).

## What the demo proves

| Fact | Deterministic result |
|---|---|
| Cart total | $800 |
| Eligible appliance subtotal | $700 |
| Gift card | $100 excluded; consumer must confirm separate tender |
| EPP-12-0APR minimum | $750 eligible subtotal: **ineligible** |
| DI-6M minimum | $200 threshold: **all $700** qualifies |
| Illustrative DI payoff | Five $117 payments and one $115 payment; not an account minimum |
| Protected warning | “No interest if paid in full,” with retroactive-interest risk; never a 0% claim |
| Evidence | Signed receipt plus a five-stage Offer Trust Passport |
| Changed-cart replay | Blocked with `CART_DIGEST_MISMATCH` |

DI can rank closest to the supplied payment target while retaining a deadline risk penalty. The consumer must accept that tradeoff; no eligible plan in this mixed-cart fixture guarantees the requested combination of no surprise interest and $120 payments. All eligible alternatives stay visible. Cashback is a separate reward dimension.

## Architecture and commands

Five self-describing tools call a transport-independent service. Pure rules resolve eligibility, calculations, legal-policy bundles and disclosure templates. SQLite atomically persists state, final audit outcomes, immutable disclosure snapshots and idempotency results; a separately committed attempt precedes business processing. SHA-256 binds canonical facts and HMAC signs evidence with a local generated demo key.

```powershell
py -3.13 scripts/run_tests.py
py -3.13 scripts/demo.py --output eval/results/smoke.json
py -3.13 eval/benchmark.py --calls 1000 --fixture-repetitions 20
```

Core tests also run without SDK dependencies using `scripts/run_tests.py --core-only`; MCP tests then skip explicitly. Actual results, platform and per-test status live in [TEST_MATRIX](docs/TEST_MATRIX.md) and `eval/results/`. Generated prompts and automated fixture repetitions are not live agent evaluations or human-consent evidence.

## Boundaries and handoff

- Structured **mock renderer attestation** is not authenticated proof that a human saw a disclosure. The demo does not have a certified renderer. Do not represent an agent's invented evidence as verified human presentation.
- Caller identities and approval metadata are synthetic bindings, not enterprise authentication. Local checksum validation is not a Legal signature or protection against a privileged operator editing both files and checksums.
- Only en-US/USD and one promotion are supported, with confirmed mock gift-card payment and confirmed separate tender for excluded purchases. Standard-revolving disposition of an excluded gift card requires a separate terms/consent flow and is blocked in this build.
- Unknown, conflicting, unsigned/unchecked, withdrawn or expired mock policies fail closed. State alone never determines an APR.
- No optional MCP App or separate website was built. SDK/host App compatibility, interactive accessibility and live Copilot execution remain unverified.
- Offline packaging is platform specific; local audit hash chains and SQLite triggers are not external immutability or a blockchain.

Start with [five-minute demo](docs/DEMO_RUNBOOK.md), [tool contracts](docs/TOOL_CONTRACTS.md), [architecture](docs/ARCHITECTURE.md), [mock dictionary](docs/MOCK_DATA_DICTIONARY.md), [compliance boundary](docs/COMPLIANCE_BOUNDARY.md), [build decisions](docs/BUILD_SPEC.md), and [SDK verification](docs/SDK_VERIFICATION.md). User-provided `Prompts/` and `.history/` files were preserved.

# policy-mcp
