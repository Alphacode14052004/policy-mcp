
```text
Diagnose why a zero-context agent skips or reorders OfferProof steps. Use tool catalog/schema/output evidence, not a custom agent prompt, as the primary fix.

Inspect descriptions, required inputs, common response envelope, `next_action`, state transitions, status recovery, and errors. Reproduce: authorization-first; disclosure without journey; acknowledgment without presentation; changed cart after acknowledgment; and context loss. The agent should receive exactly one valid next action in each state and should not need a human hint.

Do not weaken the gateway, combine all logic into one opaque tool, treat tool delivery as presentation, or put critical instructions only in a resource/prompt. Improve tool descriptions and typed contracts, then add contract tests using the actual MCP catalog. Report the root cause, changes, and test proof.
```