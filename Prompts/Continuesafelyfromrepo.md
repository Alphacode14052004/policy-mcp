Prompt 2 — Continue safely from the repository state

```text
Continue building the OfferProof MCP from the actual current repository state. First inspect the repository, `docs/BUILD_SPEC.md`, `docs/TEST_MATRIX.md`, the current diff, and recent test results. Do not assume that a prior chat summary is accurate and do not rewrite working modules unnecessarily.

Identify the highest-priority incomplete requirement, update a short plan, implement it, and run the narrow and full relevant tests. Preserve these non-negotiable contracts: five self-describing tools; deterministic line-item eligibility; versioned mock policies and canonical disclosures; presentation distinct from tool delivery; attempted and final audit events; optimistic versioning and idempotency; HMAC receipts bound to the cart and policy; fail-closed authorization; stdio-safe stdout; Python 3.13 offline packaging.

If the spec and code disagree, use the safety/legal boundary in `docs/COMPLIANCE_BOUNDARY.md` and the acceptance tests as the authority, document the discrepancy, and fix it. End with completed work, exact tests run, remaining gaps, and the next best repository task.
```