```text
Perform a focused audit/evidence review of OfferProof MCP. Trace every exit path for all five tools, including schema failure, validation failure, policy failure, renderer failure, decline, expiration, stale version, internal exception, and success.

Ensure each invocation attempts an ATTEMPTED audit write before business work and records a final SUCCEEDED/BLOCKED/FAILED/DECLINED/EXPIRED/UNCONFIRMED outcome. Audit writes must be transactional with the state change where appropriate. If audit persistence is unavailable, fail closed with AUDIT_UNAVAILABLE and create a sanitized operational log; do not authorize.

Verify idempotency constraints, payload-conflict detection, optimistic locking, SQLite restart persistence, exact disclosure reconstruction, cart/disclosure digests, optional event hash chain, and HMAC receipt validation. Receipts must bind journey, identities, merchant, offer, terms/disclosure/policy/presentation versions, cart/disclosure digests, timestamps, locale, channel, renderer, and expiry. Test forgery, replay, expiration, cross-agent, cross-merchant, stale cart, stale policy, and stale terms.

Do not store unnecessary PII and do not leak stack traces, paths, keys, SQL, or raw account data. Add tests for any missing path, run the relevant suites, and report exact results.
```