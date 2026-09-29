# Tool contracts v1

Exactly five tools are exposed. Names, descriptions, strict JSON input schemas and a shared output schema are returned through MCP discovery. Exact machine-readable contracts are in `docs/schemas/` and are generated from `offerproof/models/contracts.py` by `scripts/export_contracts.py`. Domain validation is within the audited service, so schema failures produce a sanitized envelope and audit outcome.

## Shared conventions

- Money is integer cents; quantity 1–100; 1–50 unique cart line IDs; explicit USD currency; maximum serialized request 65,536 UTF-8 bytes; bounded text and nested depth. Boolean is not accepted as integer. Unknown properties fail.
- IDs are bounded opaque ASCII tokens. Business account, merchant, agent and SKU references use synthetic `MOCK-` prefixes. Times must be ISO-8601 UTC with an explicit zero offset. These IDs are mock identity bindings, not authentication.
- Mutations use `merchant_id`, `agent_id`, `request_id`, `correlation_id`, `idempotency_key`. All mutations after start also require `journey_id` and `expected_version` equal to the last returned `journey_version`.
- A key is unique within merchant/agent across tools. Semantic digest excludes only request/correlation IDs. Identical retry returns the original response and logs the retry; different payload returns `IDEMPOTENCY_CONFLICT`. Corrected requests need a new key.
- Every response includes `status` (`COMPLETED`, `BLOCKED`, `INPUT_REQUIRED`), journey ID/state/version, reason code, safe message, result, one next action, request/correlation IDs, synthetic warning and dotted `code`, `trackingId`, `transient`. Route on code, never parse the message. Do not show raw technical messages to consumers as legal copy.
- Since server 1.3.0, newly constructed responses include UTC `server_time`. An idempotent replay preserves its original response and clock; cached responses from older versions may omit the field. Use `get_offer_journey_status` for a fresh clock. This is diagnostic information, never presentation or consent evidence.
- `next_action` contains one `tool` (actual tool name or terminal/operator action), its required input names and one instruction. `INPUT_REQUIRED` is an application envelope status, not MCP protocol elicitation. Expected consumer selection/consent is a normal part of the workflow.

## Inputs, outputs and ordering

| Tool | Input beyond shared fields | Result |
|---|---|---|
| `start_offer_journey` | `cart`, `program_id`, `channel`, `renderer_id`, `locale`, `account_terms_id`, `jurisdiction`; optional `preferences`; no prior journey/version | Server version, cart total, all eligible/ineligible offers, **full disclosure previews for every eligible offer before selection**, per-offer allocation, recommendation scoring, mock policy, standard fallback |
| `prepare_offer_disclosure` | `offer_id`; `allocation_confirmation` if excluded balance exists (`confirmed`, `excluded_disposition`, `confirmed_by`); `applied_tender_confirmation` if existing gift-card payment exists (`confirmed`, exact `applied_tender_cents`, `confirmed_by: CONSUMER`) | Exact `canonical_text`, protected indicator/segments, facts, versions/approval IDs, digests, allocation, eligible/excluded lines, immutable snapshot ID, interpolation inputs and presentation requirements |
| `record_disclosure_outcome` | Bound `renderer_id`, cart/disclosure digests, `outcome`, structured `evidence`; `acknowledgment` for ACKNOWLEDGED | Valid presentation status or signed receipt; decline/expiry result; failed evidence leaves version unchanged |
| `authorize_promotional_checkout` | Current full `cart`, full `jurisdiction`, `offer_id`, signed `receipt` | Mock decision, authorization ID/time, `payment_processed: false`, signed receipt and Offer Trust Passport |
| `get_offer_journey_status` | Journey + merchant/agent identity only; request/correlation optional; no idempotency/version | Current evaluations, preserved canonical disclosure/evidence/receipt, block reason, authorization if completed and passport |

`cart`: `cart_id`, `currency`, `lines`, `tax_cents`, `shipping_cents`, `total_cents`; optional `applied_tenders`. The total is gross purchase value before payment. Each line contains `line_id`, `sku`, `category`, `item_type`, `unit_price_cents`, `quantity`; optional `title`/`description` are untrusted and discarded from persistence. Cart digest sorts lines by ID and ignores display prose. Identity, amounts, categories, quantities, tax and shipping remain bound.

`applied_tenders`: at most ten mock payments, each with a unique `tender_id` prefixed `MOCK-`, `tender_type: GIFT_CARD`, positive `amount_cents` and exact `line_allocations` (`line_id`, positive `amount_cents`). Allocations must sum to each payment, target distinct existing GOODS lines within that payment, and cumulatively never exceed a line's gross value. Tender and allocation order are normalized for digesting; omitted and empty tender lists are equivalent. Amounts, references and line allocations remain bound to disclosure and receipt. No real card numbers, balance verification or redemption are supported.

The registered sofa is `MOCK-SKU-SOFA` / `SOFA` / `GOODS`; mappings are exposed in start-tool discovery and the catalog resource. Unknown SKUs return `PRODUCT_NOT_CONFIGURED` with supported mappings and `REQUEST_MOCK_CATALOG_UPDATE`, not a legal-policy conclusion. Never substitute an unrelated product to pass eligibility.

All current offers explicitly configure `eligibility_basis: ELIGIBLE_BALANCE_AFTER_APPLIED_TENDER` and `allowed_applied_tender_types`. The server returns gross eligible value, applied payment, net eligible value, excluded balance and the basis used. Invalid allocations return `TENDER_ALLOCATION_INVALID`; a disallowed payment type returns `TENDER_POLICY_UNSUPPORTED`. Missing, false or wrong-amount payment confirmation returns `APPLIED_TENDER_CONFIRMATION_REQUIRED` without advancing. Purchased gift cards remain excluded product lines, independently of existing gift-card payment.

`jurisdiction`: `profile_id`, `issuer_charter`, `issuer_location`, `product_legal_type`, `account_program`, `origination_channel`, `merchant_location`, `consumer_residence_state`, `billing_state`, `servicemember_status_source`, `servicemember_status_result`, `transaction_at`. All context must match an approved mock profile. Current full context is resubmitted at authorization so address changes cannot hide behind a prior digest.

`preferences` supports optional `avoid_surprise_interest`, `target_monthly_cents`, `payoff_horizon_months`, `reward_preference`. No recommendation is invented if preferences are absent or tied. Transparent penalties compare eligible options: DI deadline risk +100; monthly distance in whole dollars (no revolving estimate adds 1000); payoff horizon distance ×10 (no schedule adds 1000); explicit cashback preference −20. No merchant compensation or placement input exists. The reward score never claims an interest saving.

`evidence`: `attestation_type: MOCK_RENDERER_ATTESTATION`, `rendered_at`, `locale`, `channel`, `renderer_version`, `viewport`, `required_sections_shown`, `protected_text_digest`, `placement_order`, `prominence_checks`, `a11y_checks`, `visible_duration_ms`, `scroll_visibility_attested`. Exact requirements come from preparation. Evidence must be within the issuance window, no later than server time and no older than 15 minutes.

`acknowledgment`: `actor: CONSUMER`, `action: ACKNOWLEDGE`, opaque `event_id`, UTC `captured_at`, `affirmative_action: true`. The journey must already be presented, and the evidence must equal that accepted presentation. No combined presentation/acknowledgment shortcut.

`receipt`: `payload` + hexadecimal `signature`. Payload binds receipt/journey, agent/merchant, offer, terms/policy/disclosure/presentation IDs and versions, record/cart/context/allocation/disclosure digests, presentation and acknowledgment times, locale/channel/renderer/version and expiry. HMAC is checked in constant time; a receipt from another journey, caller, altered cart or stale version cannot authorize. Even when acknowledgment is configured off, a signed presentation receipt is required.

## Worked call sequence

Since server 1.2.0, each eligible `offers[]` entry (and `standard_fallback`) includes `disclosure_preview`: exact `canonical_text`, protected-text marker, facts including complete payment schedule/APR/payoff date, source versions/digests, allocation, interpolation inputs, `evaluated_at`, `valid_until`, `pending_confirmations`, payment explanation and display instruction. `stage` is `PRE_SELECTION_PREVIEW`; `selection_is_acceptance` and `is_final_disclosure` are false. Ineligible offers retain rejection reasons and do not receive a preview.

The agent must show every eligible preview's text verbatim and the payment schedule before asking for a selection. These are rendered from the same protected mock templates as final issuance. Excluded purchases are explicitly marked as requiring separate-tender confirmation. A preview neither confirms applied payment nor issues a snapshot, receipt or consent event. `DISCLOSURE_PREVIEW_GENERATED` audit events distinguish generation from final issuance. Status recovery retains the original evaluated previews and their timestamps; final preparation revalidates current records and produces current copy. Previously saved comparisons without previews must restart with a new key.

`demo-data/mixed-cart.json` is an exact start request. `scripts/demo.py` constructs the following sequence as an **automated synthetic fixture**, not a consent source for the live demo:

1. Start → `OFFERS_EVALUATED`, version 1. EPP fails at 70000 < 75000; DI qualifies at 70000 ≥ 20000. Display every eligible disclosure preview before asking which offer to review.
2. After consumer selection for review and separate-tender confirmation, prepare DI → `DISCLOSURE_ISSUED`, version 2. Selection does not accept the terms; display the freshly issued final copy.
3. Show exact text; record PRESENTED with the returned requirements → `DISCLOSURE_PRESENTED`, version 3.
4. After consumer confirmation, record ACKNOWLEDGED → `ACKNOWLEDGED`, version 4, signed receipt.
5. Submit unchanged cart/context and receipt → `AUTHORIZED`, version 5, passport.

An authorization-first attempt has no side effect and returns the actual next step. Same-version concurrent preparations yield one success and one `STALE_JOURNEY_VERSION`. Read status to recover. A changed cart becomes `INVALIDATED`; start again. Changed terms/policy can return to `OFFERS_EVALUATED`; prepare again with the new version and collect new evidence. Never silently refresh and authorize.

`demo-data/sofa-gift-card-redemption.json` supplies the second worked request: one $750 sofa and a $100 applied payment, leaving $650 eligible and $0 excluded. DI qualifies; EPP fails the $750 post-payment threshold. Preparation requires `applied_tender_confirmation: {"confirmed": true, "applied_tender_cents": 10000, "confirmed_by": "CONSUMER"}` following consumer confirmation. The disclosure records $750 purchase / $100 mock payment / $650 financed. Changing a payment amount, reference or allocation requires fresh evidence. Offer and disclosure fixtures are version 1.1.0; persisted old journeys do not gain new authorization automatically.

## Presentation timing and recovery (server 1.3.0)

Final preparation returns `result.issued_at`, captured once and retained with the immutable disclosure snapshot. Status returns `result.issued_at`, `result.prepared.issued_at` and `result.presentation_timing`, including the earliest/latest acceptable `rendered_at` and the 900-second maximum age. Older issued journeys expose their stored issuance time without rewriting the original snapshot. Timing bounds are evaluated again at validation; the clock inside an error describes validation time, while envelope `server_time` describes response construction.

`PRESENTATION_EVIDENCE_INVALID` retains its existing reason code and adds `result.presentation_error` with `check`, `field`, `message`, timing bounds and, when applicable, `received_at` or failed checks:

| Check | Meaning / recovery |
|---|---|
| `RENDERED_AT_BEFORE_ISSUANCE` | Event precedes the final disclosure. Display that disclosure and capture a new renderer event. |
| `RENDERED_AT_IN_FUTURE` | Event is later than the validation clock. Investigate the event source/clock; never substitute a guessed timestamp. |
| `RENDERED_AT_TOO_OLD` | Presentation is more than 900 seconds old. Follow the returned next action; an expired previously accepted presentation requires fresh preparation. |
| `ACKNOWLEDGMENT_BEFORE_PRESENTATION` | Consumer event precedes the accepted display event. Collect an actual affirmative event after presentation. |
| `ACKNOWLEDGMENT_IN_FUTURE` | Consumer event is later than validation time. Investigate the capture source/clock. |
| `PRESENTATION_CONTEXT_MISMATCH` / `PRESENTATION_REQUIREMENTS_FAILED` | Renderer context or required display checks failed; inspect the identified fields/checks. |
| `ACCEPTED_PRESENTATION_CHANGED` | Acknowledgment must reference exactly the presentation already accepted by the server. |
| `RENDERER_REPORTED_FAILURE` | Caller reported failed display. Do not proceed to acknowledgment. |

Recovery: read status for the existing journey, display the current final canonical text, and submit the actual renderer event with the current version and a fresh idempotency key. Never copy `issued_at`, `server_time`, journey creation time, preview time or a timing bound into event evidence. The normal server uses the actual UTC clock; synthetic transaction dates do not freeze that clock. If the host cannot capture the required event and display checks, explain that integration limitation and stop before acknowledgment. The backend does not infer visibility from tool delivery or chat text. Consumer acknowledgment and mock checkout authorization remain separate subsequent steps.

## Resources and helper prompts

Read-only resources: `offerproof://catalog/current`, `offerproof://workflow/v1`, `offerproof://reason-codes/v1`, `offerproof://policy/{policy_id}/{version}`, `offerproof://disclosure/{disclosure_id}/{version}`, `offerproof://evidence/receipt/{receipt_id}`. Resource IDs map to in-memory records, not filesystem paths. Old issued disclosures are retained as database snapshots; a current-registry version lookup does not claim to be a complete historical publishing service.

Optional prompts: `compare_promotional_offers`, `test_lazy_agent`, `explain_disclosure_receipt`, `run_demo_scenario`. None is used in the primary judged cold start. The complete stable reason catalog and single recovery mappings are in `mock-data/reason-codes.json`.
