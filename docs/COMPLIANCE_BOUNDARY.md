# Compliance and data boundary

Intended production positioning: **“OfferProof deterministically enforces the exact policies and disclosure copy approved by Synchrony Legal and Compliance.”** In this repository every approval is `APPROVED_MOCK`, every policy is fictional and every disclosure begins **MOCK DISCLOSURE — NOT APPROVED LEGAL COPY**. There is no claim of legal approval or regulatory compliance.

This is an engineering control-routing matrix, not an interpretation of applicable law or legal advice. Categories were requested in the build brief; authoritative owners, applicability and approved content remain to be confirmed externally.

| Control category | Mock route / implemented boundary | Required authoritative approval before production |
|---|---|---|
| TILA / Regulation Z | `REG_Z_REVIEW`; separate plan templates, exact structured rate/payment facts | Legal approves product scope, advertisements and account-specific disclosure requirements |
| Deferred interest / servicing | `DEFERRED_INTEREST_SERVICING_BOUNDARY`; conditional headline, purchase-date interest risk, payoff deadline and minimum-payment warning | Legal and servicing owners approve wording and separate allocation calculations |
| UDAAP | `UDAAP_WORDING`; blocks DI “0%” labels and true-zero/DI template mismatch | Legal approves all names, prominence and consumer journey |
| ECOA / Regulation B | `REG_B_NOTICE_ROUTING`; no credit decision; adverse-action-like fields route to authoritative notice process with a stable non-discriminatory boundary reason | Authorized decision/notice systems and counsel |
| FCRA / Regulation V | `FCRA_REPORT_BOUNDARY`; rejects consumer-report and score fields | Authorized consumer-report flows, scope and consent |
| MLA / SCRA | `MLA_SCRA_ROUTING`; synthetic source/result are routing context only; unknown profile blocks | Authoritative status source and approved legal policy |
| State law / preemption | `STATE_PREEMPTION_REVIEW`; match charter, issuer, product/program, merchant/channel, residence/billing, status source/result and transaction date | Legal publishes the approved jurisdiction policy; no address-to-cap shortcut |
| E-SIGN | `ESIGN_PRESENTATION`; delivery differs from structured mock presentation and separate affirmative acknowledgment | Valid consent design, durable access and evidentiary sufficiency |
| GLBA / privacy / security | `GLBA_MINIMIZATION`; no real accounts, reports or identifiers; sanitized audit and generated local key | Security/privacy threat model, retention and incident response |
| Accessibility / language | `ACCESSIBILITY_LANGUAGE`; required keyboard/screen-reader/no-color checks in renderer attestation; unsupported locale fails | Real rendered WCAG/language certification; en-US-only mock does not certify accessibility |

## Approval and publication model

All protected records include immutable ID/version, effective/expiration/review dates, status, distinct maker/checker, mock approval ID/time, predecessor/rollback reference, source system and content checksum. Loader rejects missing or mismatched checksums, unsupported fields, draft/withdrawn status, invalid intervals, expired current policies, conflicting context and broken references. Different families cannot share incompatible disclosure copy. Approved placeholders are explicit and contain no expressions, attribute lookups or format conversions.

Checksums detect accidental or uncoordinated changes; a local editor who can recompute checksums is inside the demo trust boundary. A production publisher must authenticate approvers, sign release bundles, retain version history, support revocation/withdrawal and controlled rollback. Rolling back still changes protected record digests and forces new consumer evidence. Never recompute checksums to legitimize unapproved production content.

`MOCK_STATE_CAP` is an explicitly fictional profile with a fictional APR override. Output says **Mock policy applied**. It does not say a state law requires a cap. This implementation makes no conclusion about federal preemption or actual state law.

## Presentation, allocation and privacy limitations

Evaluation includes full protected disclosure previews for all eligible offers so consumers can review terms before selecting. The text is generated from the same versioned mock templates as final disclosure, with pending allocation confirmations explicitly identified. Generation is audited separately and does not establish that a human saw the preview. Tool delivery alone cannot force a language model to display it; live display must still be verified. Selection is not consent. Final preparation revalidates current terms, and final presentation and affirmative acknowledgment are separately required.

The baseline accepts a **MOCK_RENDERER_ATTESTATION** with content digest, sections, order, locale, renderer version, timestamps, viewport, visible duration and accessibility/prominence checks. An agent can manufacture these fields in a local test, so the receipt proves the server accepted those assertions, not actual human viewing. A separate affirmative consumer event is required and the consent must not be preselected. Optional prompts and the automated fixture driver are helpers, never permission to fabricate live consumer consent.

Server 1.3.0 exposes issuance/server clocks and specific presentation timing failures. These diagnostics neither capture renderer events nor establish visibility or consent. The host must supply actual display and consumer events; if it cannot, the live journey stops before acknowledgment. No timestamp is automatically filled from server time, and timing checks remain unchanged. Chat task checklists are host planning UI and have no role in the server's disclosure state or authorization decision.

The excluded gift card offers the discovery disposition `SEPARATE_TENDER_OR_STANDARD_REVOLVING`, but this build can complete only the explicitly confirmed `SEPARATE_TENDER` branch. A standard-revolving branch needs its own accepted terms and evidence. No allocation represents post-purchase payment allocation. No interest accrual, retroactive charges, account minimum payment, underwriting, acceptance, real checkout processing, or adverse-action notice is calculated.

An existing gift card used as payment is a separate synthetic model: `cart.applied_tenders` allocates a stated mock amount to GOODS lines. It is not a purchased gift-card product, verified card balance, reservation or redemption. Offer version 1.1.0 explicitly bases eligibility on the remaining eligible amount after that payment; this is a fictional configuration choice and must not be presented as actual merchant policy. The consumer confirms the applied amount, and the cart/allocation digests bind it through disclosure and authorization.

Strict schemas reject SSN/credit score/report/account/PAN/CVV/DOB/income/credential/contact fields and obvious sensitive string patterns. This is not a general PII detector; operators must supply synthetic input only. Display prose is not persisted. Audit holds opaque references and versions, not raw request bodies, tokens, or consumer text. Runtime data, keys and logs are ignored by version control. No real data, endpoint URLs, merchant identifiers or copied internal legal text from the user's research were imported.
