```text
Red-team OfferProof MCP without changing its legal/product boundary. Build table-driven and property-oriented tests for malformed carts, money overflow/rounding, corrupt JSON, unknown references, prompt injection in product and merchant text, path traversal, oversized payloads, unknown schema fields, prohibited sensitive data, SQL injection strings, invalid timestamps, unsupported currency/locale, renderer capability mismatch, stale versions, concurrent calls, duplicate idempotency keys with different payloads, receipt forgery/replay, and attempted state skipping.

Include the 32 mandatory scenarios in `docs/TEST_MATRIX.md`. Verify that deferred interest can never be mislabeled 0%, true 0% cannot use deferred-interest copy, cashback cannot be called interest-free, billing state alone cannot select a legal cap, and no tool can authorize without valid presentation/acknowledgment evidence. Verify error output is sanitized and every attempt/final outcome is logged.

Run as many generated cases as the environment permits. Record actual counts and results; do not claim 200 natural prompts, 1,000 adversarial calls, p95 latency, or 20 rehearsals unless executed. Fix defects, rerun regression tests, and leave reproducible commands and artifacts.
```
