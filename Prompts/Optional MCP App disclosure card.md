```text
The core OfferProof MCP server and structured fallback must already be passing before this task. Verify that the installed official MCP Python SDK 2.x and installed VS Code build support MCP Apps using their actual current documentation/examples. If support is absent or cannot be tested, document the gap and do not invent APIs.

If verified, implement one accessible MCP App disclosure card for the `prepare_offer_disclosure` result. It must show the eligible amount, excluded gift-card amount, selected plan/type, protected warning and headline, payoff/APR facts, policy/terms/disclosure versions, and Acknowledge/Decline controls. The control must invoke or produce valid input for `record_disclosure_outcome`; it must not mutate authorization state on its own. After successful recording, show a green Offer Trust Passport/receipt state, using text/icons in addition to color.

Keep the plain structured/text result complete for clients without Apps. Test both paths. Verify keyboard access, screen-reader labels, protected-copy integrity, error states, and VS Code configuration/feature flags. Run all core tests afterward and report exact results and any client limitation.
```