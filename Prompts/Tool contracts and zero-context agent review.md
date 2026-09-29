Review OfferProof MCP as if you are a completely unfamiliar agent receiving only the MCP tool catalog and a natural user request. Inspect the registered tool names, descriptions, strict schemas, output envelopes, resources, and state machine.

The correct flow must be discoverable without a custom agent file, slash prompt, manually attached resource, or prompt that names tools:
start_offer_journey -> prepare_offer_disclosure -> record_disclosure_outcome -> authorize_promotional_checkout, with get_offer_journey_status for recovery.

Fix any ambiguity, overlap, optional-field confusion, schema weakness, or response that could make the agent skip a step. Every response must give status, journey state/version, stable reason code, and exactly one authoritative next_action. A lazy authorization-first call must be safely redirected. Canonical disclosure cannot be rewritten. Tool delivery cannot be treated as proof of presentation. Expected acknowledgment is allowed, but no human hint should be needed to recover from a normal state transition.

Create or strengthen MCP contract tests, including an SDK in-memory client test if supported by the installed official SDK. Also test schema generation and deterministic output ordering. Run tests and report concrete failures fixed, exact commands, and remaining client-specific uncertainty.
```