# Five-minute OfferProof demo

Everything shown is synthetic; approval metadata and renderer evidence are mock. Intended production positioning: **“OfferProof deterministically enforces the exact policies and disclosure copy approved by Synchrony Legal and Compliance.”** The demo does not prove legal approval, real human viewing, underwriting or payment processing.

## Before judging: binary gates

- [ ] Compatible Windows x64 Python 3.13 interpreter is configured in `.vscode/mcp.json`; `offerProof` starts and lists exactly five tools.
- [ ] `scripts/verify_offline.ps1` passes with populated vendor and no pip installation. Network-disabled startup/smoke artifact is available.
- [ ] Workspace/MCP trust and execution permissions were resolved before the timer.
- [ ] Runtime database/key paths are writable. Stop the server before `scripts/reset_demo.ps1`, then restart it.
- [ ] Only OfferProof tools are enabled in the Agent chat where practical. Start a fresh chat with no custom agent file, helper prompt or manually attached resource.
- [ ] `demo-data/mixed-cart.json` is attached. Use a new start idempotency key after a prior run unless the database was reset.
- [ ] Presenter has a text/structured fallback and a saved smoke artifact.
- [ ] Live renderer attestation is described as mock; consumer confirmation is never invented or preselected.
- [ ] Twenty consecutive **live** rehearsals are logged in `eval/rehearsals.csv` if achieved. Currently the file is blank: automated fixture repetitions are not live rehearsals.

## Exact natural prompt

> Buy this $700 appliance and $100 gift card using the Synchrony option that best fits me. I want to avoid surprise interest and keep payments near $120 a month.

Attach or paste `demo-data/mixed-cart.json`. Do not tell the agent which tools to call. A normal offer/tradeoff choice, separate-tender confirmation and affirmative acknowledgment are expected consumer inputs, not corrective tool instructions. Never respond with tool names to rescue the main story and still call it a zero-hint success.

## Timed story

| Time | Presenter / agent action | Visible proof and binary gate |
|---|---|---|
| 0:00–0:35 | “Agentic partners face fragmented eligibility, legal copy and evidence rules. OfferProof executes versioned policy and preserves proof.” Enter the natural prompt. | Agent's first tool is `start_offer_journey`; no hint given. |
| 0:35–1:20 | Show the eligibility comparison, every eligible offer's exact disclosure preview, payment schedule and warnings before asking for a selection. | $800 total ≠ $700 eligible; EPP minimum $750 fails; gift card excluded. Full preview text is visible for DI and standard revolving. |
| 1:20–1:55 | Explain DI-6M's conditional terms and recommendation tradeoff. Ask which offer the consumer wants to review and confirm $100 separate tender if chosen. | $200 is a threshold, all $700 finances; DI is never called 0%; selection is for review, not consent. |
| 1:55–2:45 | Agent prepares disclosure and displays exact canonical text with warning, deadline, fictional APR, suggested payoff amounts and version IDs. | Exact text unchanged; required sections/order/prominence visible; mock renderer attestation recorded separately from delivery. |
| 2:45–3:25 | Agent asks for affirmative consumer acknowledgment. Consumer acknowledges or declines. | Consent request is explicit. ACKNOWLEDGED only follows PRESENTED; receipt appears only after valid required evidence. A decline closes the journey. |
| 3:25–4:05 | Agent authorizes unchanged synthetic cart/context. | Green/positive state may be described in text; signed receipt and five-stage passport show IDs and digests. It is a mock authorization, not a payment. |
| 4:05–4:35 | Second beat: change the appliance by $1, keep the old receipt, attempt authorization. | `CART_DIGEST_MISMATCH`; no new authorization. This is the deliberate adversarial demonstration after the primary natural flow. |
| 4:35–5:00 | Show actual verification artifacts and future integration boundary. | Measured vs target labels visible; no fabricated business savings; finish before five minutes. |

Example DI outcome: five suggested $117 payoff payments and a final $115 (not the account minimum). The model must explain that the plan has deadline risk; the stated preferences do not make a conditional DI plan a guarantee against surprise interest. The consumer can decline or choose standard terms.

## Sofa payment variant

Server 1.3.0 includes both eligible disclosure previews before selection and presentation timing diagnostics. The fresh `demo-data/sofa-disclosures-before-selection.json` request and `eval/results/sofa-offer-comparison.md` example demonstrate the expected comparison output. The latter is generated from an actual automated evaluation, not proof of live Copilot display. Confirm `OfferProof 1.3.0` in the VS Code MCP Output startup line; restarting a terminal server does not refresh Copilot's server.

Restart `offerProof` after the sofa/tender update to refresh code and discovery schemas. Start a fresh chat, attach `demo-data/sofa-gift-card-redemption.json`, and use a fresh start idempotency key. Say: “Buy this $750 sofa using my existing $100 gift card as payment. Compare financing for the remaining balance.” Expected evaluation: $750 purchase, $100 mock payment, $650 eligible, $0 excluded; DI qualifies and EPP fails its explicitly configured $750 post-payment minimum. Confirm the applied amount and offer choice before preparation, then follow the same presentation/acknowledgment sequence. Buying a new $100 gift card instead is a different $850 cart with $750 eligible and $100 excluded. The payment model does not check a real balance or redeem value.

An unknown SKU returns `PRODUCT_NOT_CONFIGURED` with catalog recovery. It does not establish that a sofa is legally ineligible. Reusing the old blocked request's idempotency key returns its original result; use a new key for corrected input. `scripts/demo.py --scenario sofa-gift-card-redemption` exercises the synthetic flow automatically, without live consumer evidence.

## Recovery and fallback

If the agent loses context or receives `STALE_JOURNEY_VERSION`, it follows the contract's status-recovery action. Use the returned version and fresh idempotency key for the corrected call. Do not claim a no-hint run if the presenter supplies corrective tool instructions.

For `PRESENTATION_EVIDENCE_INVALID`, inspect `result.presentation_error.check` and read status for the same journey. Version 1.3.0 exposes final `issued_at`, fresh `server_time` and current timing bounds. The reported live failures were an event in the future followed by retries before issuance. Display the final text first and use a captured renderer event, never a guessed timestamp or copied clock value. Corrected submissions need a fresh idempotency key; repeating the old key returns the original failure and its original clock. The transaction date in a mock cart does not freeze the running server's UTC clock.

An issued disclosure is ready for review, not accepted. Remaining stages are recorded presentation, separate affirmative consumer acknowledgment, and mock checkout authorization. A host-generated todo list does not advance those stages. If the host only prints the text and cannot capture display checks and consumer events, the live flow remains incomplete; an event-capture integration is still needed. The timing fix does not implement that host integration.

If a cart changes, start a new journey. If terms or policy change, prepare new copy and collect new evidence. If policy is unknown, route to authoritative review; no agent-written rule fills the gap. If an excluded balance is not confirmed, stop for the consumer's decision. If declined, end the journey.

If the renderer cannot provide the structured mock evidence, authorization must stay blocked. For presentation continuity, show the canonical text and saved `eval/results/smoke.json`, explicitly labeled **recorded automated synthetic fixture**. The fallback terminal command is `py -3.13 scripts/demo.py`; locally without registered Python use `& ./.build/python313/python.exe scripts/demo.py`. That driver simulates fixture consent and does not count as a live natural-agent run.

No separate website or optional MCP App is required. App compatibility and visual accessibility are unverified; text/structured results remain the baseline.

## Exact judging rubric

| Category | Weight | Required proof in the build/demo | Concrete artifact | Live-demo moment / yes-no gate |
|---|---:|---|---|---|
| Impact of Solution | 35% | 10%: real high-friction Synchrony problem; 5%: clear/quantified benefit with honest measured-vs-target labels; 20%: compelling, feasible, strategically valuable use case. | README problem and mixed-cart example; MEASUREMENTS.csv; benchmark.json; ARCHITECTURE production roadmap | 0:00 problem; 0:35 eligibility x-ray; 4:35 actual test/benchmark proof. Gate: no invented savings. |
| Gap Analysis Depth | 15% | 5%: explicit current-state vs. new AI workflow; 10%: root causes, evidence, and non-obvious gaps such as eligible subtotal, presentation proof, jurisdiction resolution, and servicing boundaries. | Gap table below; COMPLIANCE_BOUNDARY; TEST_MATRIX | 0:35 subtotal vs total; 1:55 delivery vs presentation; 4:05 stale proof. Gate: all four named gaps are visible. |
| Technical Approach & Execution | 30% | 10%: natural intent prompt with no scripted tool instructions; 10%: clean autonomous execution without corrective hints or unhandled errors; 10%: robust, understandable tools, resources/prompts, schemas, errors, state, evidence, and tests. | TOOL_CONTRACTS; exact schema exports; SDK contract tests; tests-offline.json; rehearsal log | 0:00 natural first call; 1:55 exact disclosure; 3:25 evidence; 4:05 block. Gate: first tool correct, zero corrective hints, no unhandled errors, each evidence precondition satisfied. |
| Pitch & Deliverables | 20% | 10%: completes within five minutes; 10%: organized, engaging, clear pitch that names the capability and makes the value/evidence visible. | Timed runbook; README; passport in smoke artifact | Finish by 5:00; show five-stage evidence. Gate: timer <300 seconds and capability named. |

## Gap analysis

| Current fragmented integration | Root cause / evidence boundary | New workflow |
|---|---|---|
| Partners interpret thresholds from a cart total | Mixed cart contains excluded items; test scenario 16 demonstrates wrong eligibility if $800 is used | Per-offer eligible lines/subtotal, rejected tiers and allocation confirmation |
| A disclosure lookup is treated as checkout readiness | Tool delivery does not demonstrate presentation or acknowledgment | Persisted issuance → presentation → acknowledgment → authorization |
| Address is treated as a legal rule | Full legal context and authoritative policy source are required; actual law is outside this prototype | Full mock profile resolution; unknown context blocks |
| Displayed wording drifts from plan type | DI, true-zero and rewards have different claims | Family-specific canonical templates and wording validation |
| Audit reconstruction depends on mutable current copy | Versions may change mid-journey | Immutable disclosure snapshots, record digests and signed evidence |
| Checkout and servicing allocations are conflated | Excluded purchase disposition does not define later payment allocation | Single promotion + separate tender; servicing explicitly excluded |

The supplied research describes qualitative patterns and gaps, not measured business baselines. Source observations were treated as design context; no internal document wording, live APR or environment endpoint was copied into the executable fixtures.
