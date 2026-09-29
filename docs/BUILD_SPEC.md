# OfferProof build specification

All data, approvals, policies, rates, merchants and results are synthetic hackathon fixtures. No real Synchrony services or customer data are used.

Intended production positioning: “OfferProof deterministically enforces the exact policies and disclosure copy approved by Synchrony Legal and Compliance.” This prototype enforces **mock** approvals only; its copy is not legally approved.

## Requirements and decisions

- Five tools: start, prepare, record outcome, authorize, recover status. Structured next actions guide cold-start discovery; persisted preconditions enforce it.
- Server 1.2.0 returns exact template-based disclosure previews for every eligible offer at evaluation, before asking for selection. Full APR/deadline/payment facts and pending allocations are visible. Selection is for review, not acceptance. Previews do not issue snapshots, confirm payment or supply presentation/consent evidence; final preparation and separate acknowledgment remain required.
- Pure Python standard-library domain core; official MCP 2.x adapter, SQLite state/audit/idempotency, JSON source data, SHA-256 and HMAC evidence.
- Integer cents; Decimal calculations; UTC times; inclusive start / exclusive expiration. One selected promotion, with explicit separate-tender disposition for excluded amounts. No stacking.
- Canonical mixed cart: 70000 appliance cents + 10000 gift-card cents. DI-6M minimum 20000 (finances all 70000); EPP-12-0APR minimum 75000 (fails). Tax/shipping excluded in fixtures.
- Sofa extension: trusted `MOCK-SKU-SOFA` / `SOFA` / `GOODS`. An existing gift card is optional applied tender with exact GOODS-line allocations and consumer confirmation, separate from buying a gift card. A 75000 sofa minus 10000 applied payment leaves 65000 eligible. Version 1.1.0 offers explicitly use post-payment eligible thresholds and configured payment types; this fictional basis is not inferred from merchant law. No actual gift-card validation or redemption occurs.
- Explicit fictional jurisdiction profiles bind the complete context; unknown or conflicting context fails closed. No state-to-law inference.
- Strict schema and bounded payloads. Product prose is never used for classification or policy, and is omitted from persistence. Known synthetic SKUs/categories are checked against the registry.
- Presentation is a structured **mock renderer attestation**, not proof of a human viewing the page. Acknowledgment requires a separate affirmative consumer event after presentation. Identity fields are local mock bindings, not authentication.
- Server 1.3.0 exposes immutable disclosure issuance time, response clock and precise presentation/acknowledgment timing errors. Status provides fresh timing diagnostics for existing journeys; cached retries retain their original response. Diagnostics do not replace host event capture or relax evidence checks.
- Receipt expiry: 15 minutes, additionally bounded by offer/policy/terms/disclosure validity. Same-key retries return original semantic results; a new-key replay after authorization is blocked.
- Startup and each mutation validate configuration integrity. Mock checksums detect accidental edits; they are not signatures from Legal. Approved-mock status, distinct maker/checker and approval metadata are required.
- Stale evidence is invalidated durably. Changed cart/context requires a new evaluation; changed versions require preparation again. Never refresh and authorize in one action.
- Audit attempts commit before processing. Final audit + state + idempotency commit atomically. Audit failure blocks all tools; catastrophic process death before the first database write cannot be logged by that process.
- No website; text and structured results are the baseline. Optional MCP App only if SDK and host support are verified after core acceptance.
- Excluded standard-revolving allocation is discoverable but cannot complete here: it needs a second accepted terms/evidence flow. The supported confirmed branch is separate tender.
- Every issued disclosure is retained in an append-only snapshot table; stale state clearing never deletes issued copy or its interpolation inputs.

## Environment findings

Initial workspace contains only user prompt/reference files; preserve them. Windows launcher exists but reports no installed Python. Bundled Python 3.12.14 x64 is available for core development; target remains Windows Python 3.13 x64. VS Code reports 1.134.0. SDK verification/build results will be recorded in SDK_VERIFICATION.md and TEST_MATRIX.md.

Official MCP 2.2.0 was fetched and inspected. An isolated official CPython 3.13.7 embeddable runtime was obtained for target testing. Target vendor wheels were fetched, hash-locked and exercised offline; no system Python installation was changed. See the final verification artifacts for exact results. Natural-agent and real-renderer gates remain explicitly unverified.

## Non-goals

No credit decision, adverse-action notice generation, consumer reports, account access, payment processing, interest accrual, retroactive-interest calculation, minimum-payment calculation, servicing allocation, legal advice, real policy approval or claimed savings.

## Definition of done

Five discoverable tools, mixed-cart end-to-end smoke and replay block, audited failures, strict and state-machine tests with scenario traceability, durable evidence, configuration integrity, launcher/VS Code config, offline build/verify scripts and eight requested documents. Environment-dependent limitations must be explicit. No natural-language or live rehearsal success claims without artifacts.
