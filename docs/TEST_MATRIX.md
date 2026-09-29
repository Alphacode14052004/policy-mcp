# Verification and scenario traceability

The latest machine-readable test result is `eval/results/tests-presentation-timing.json`; it includes exact interpreter/platform, count and every test ID/status. Prior target runs remain in `tests-disclosure-previews.json`, `tests-sofa-redemption.json` and `tests-offline.json`. The comparison-only artifact is `eval/results/sofa-disclosure-previews.json`, with a readable rendering in `sofa-offer-comparison.md`; the complete automated sofa flow is `sofa-preview-final-flow.json`. Earlier smoke and benchmark artifacts are preserved. These artifacts are synthetic and contain no customer evidence.

Latest target run on Windows x64 CPython 3.13.7: **95 tests passed, 0 failures, 0 errors, 0 skips**, including presentation timing diagnostics, disclosures before selection, sofa/payment scenarios and complete MCP SDK flows. Prior PowerShell offline verification and smoke passed with 61 tests. The earlier 1,000-call malformed-core benchmark p95 is **43.3809 ms**; it was not rerun for these extensions. Its workload limits are described below; this is not an end-to-end or all-tools latency claim.

The 32 requested scenarios map as follows. “PASS” means an executed deterministic test; scenario 2 distinguishes discovery proof from a live natural-language claim.

| # | Requested scenario | Test/control | Actual status |
|---:|---|---|---|
| 1 | Happy DI through authorization | `test_01_happy_path_receipt_passport`, MCP happy path | PASS |
| 2 | Natural intent, no scripted tool instructions | `test_02_discovery_has_self_describing_cold_start_contracts` verifies discovery metadata; 200-prompt corpus and evaluation protocol exist | Discovery PASS; **live Copilot NOT RUN**, no connected judged session was executed |
| 3 | Lazy authorization first | `test_03_lazy_agent_cannot_authorize_first` | PASS |
| 4 | Changed cart after acknowledgment | `test_04_changed_cart_invalidates_receipt` | PASS |
| 5 | Terms version change | `test_05_terms_version_changed` | PASS |
| 6 | Offer expires mid-journey | `test_06_offer_expires_mid_journey` | PASS |
| 7 | Ineligible category / trusted SKU | `test_07_category_registry_cannot_be_overridden`; mixed-cart excluded line reasons | PASS |
| 8 | No promo / standard fallback | `test_08_no_promotion_standard_fallback` | PASS |
| 9 | Duplicate acknowledgment / authorization | `test_09_idempotent_ack_and_authorization` checks one side effect | PASS |
| 10 | Concurrent expected version | `test_10_concurrent_same_version_only_one_advances` | PASS |
| 11 | Product prompt injection | `test_11_prompt_injection_ignored_and_not_persisted` | PASS |
| 12 | Paraphrase / shorten protected text | `test_12_paraphrase_request_and_wrong_digest_blocked` | PASS |
| 13 | Lost context | `test_13_context_loss_recovers` | PASS |
| 14 | Ambiguous/missing preferences | `test_14_missing_preferences_omits_recommendation`; deterministic tie behavior in recommendation | Missing preferences PASS; live preference clarification NOT RUN |
| 15 | Omitted presentation sections | `test_15_omitted_presentation_sections_are_logged` | PASS |
| 16 | $800 total / $700 eligible EPP threshold | `test_16_mixed_cart_threshold_on_700_not_800` | PASS |
| 17 | DI $700 qualifies / excluded $100 confirmed | `test_17_excluded_balance_requires_confirmation` | PASS |
| 18 | DI mislabeled 0% | `test_18_deferred_interest_mislabeled_zero_fails`; offer-name hardening test | PASS |
| 19 | True-zero plan paired with DI copy | `test_19_true_zero_plan_with_deferred_copy_fails` | PASS |
| 20 | Jurisdiction policy version changes | `test_20_policy_change_invalidates` | PASS |
| 21 | Billing/context change unknown policy | `test_21_context_change_fails_closed`; full fictional cap profile test | PASS |
| 22 | Cashback is not interest-free | `test_22_cashback_never_interest_free`; reward facts from configuration test | PASS |
| 23 | Sensitive fields rejected | `test_23_sensitive_fields_rejected_without_logging`; nested schema and audit-ID tests | PASS |
| 24 | Adverse-action boundary | `test_24_adverse_action_routes_without_notice` | PASS |
| 25 | Audit unavailable | `test_25_audit_failure_blocks_authorization`; final-write rollback test | PASS |
| 26 | Corrupt source JSON / broken references | `test_26_corrupt_json_and_broken_references`; startup reference test | PASS |
| 27 | Same key / different payload | `test_27_idempotency_conflict_different_payload` | PASS |
| 28 | SQLite survives restart | `test_28_restart_keeps_state_and_signing_key` | PASS |
| 29 | Money/allocation/final payment reconciliation | `test_29_allocation_and_payment_totals`; unit schedules and tax/shipping tests | PASS |
| 30 | Unsupported currency/locale/renderer | `test_30_unsupported_currency_locale_renderer` | PASS |
| 31 | stdout remains MCP JSON-RPC | `test_31_stdout_contains_only_jsonrpc` launches actual subprocess from different cwd | PASS |
| 32 | Forgery/expiry/identity/replay | `test_32_forgery_identity_expiry_and_replay`; expiry and cross-journey tests | PASS |

Additional tests cover audit append-only triggers/hash chain, separate presentation before consent, explicit decline and expiry, no-ack policy requiring a signed presentation receipt, all six disclosure families, draft/unchecked policies, renderer-version change, exact dynamic cashback facts, immutable snapshots after invalidation, false/unsupported tender confirmation, strict integer types and month-end rounding.

Delayed acknowledgment is also tested: presentation older than 15 minutes invalidates downstream evidence and returns a usable disclosure-preparation recovery action.

The 13 added tests comprise 12 sofa/payment regressions and one complete official SDK sofa flow. They check the $750 sofa threshold, $850 sofa plus purchased gift card, $650 remaining after existing gift payment, exact disclosure amounts, independent payment/excluded-purchase confirmations, receipt bindings, changed-payment rejection, strict allocation/schema rejection with audit, per-offer payment policy, unknown-product catalog recovery and canonical ordering. Discovery also verifies the trusted sofa mapping and payment guidance. The user shared a successful live evaluation transcript, but a complete live disclosure/consent/authorization flow remains unverified.

The subsequent ten preview regressions verify exact template text and schedules before selection, all six families, standard-only fallback, pending allocations, no issuance/consent/authorization side effects, misuse of preview evidence, final reissuance and separate acknowledgment, recovery/idempotency, terms changes and migration of old comparisons. SDK discovery and happy paths assert preview guidance/content and server version 1.2.0. The comparison-only CLI returns two sofa previews and stays at OFFERS_EVALUATED; the final-flow fixture still authorizes with separate simulated evidence and blocks changed-cart replay. Neither fixture establishes that a live Copilot chat displayed the disclosures.

## Commands actually executed

The 1.3.0 timing extension adds ten domain regressions and one official SDK regression. They reproduce all three reported bad timestamps, check issuance/future/900-second boundaries at microsecond precision, preserve separate acknowledgment requirements, retain clocks on cached retries, expose fresh status for legacy journeys without rewriting snapshots, preserve expired-evidence recovery and distinguish non-timing failures. Simulated recovery uses controlled test events; it does not claim a live renderer captured anything. SDK assertions now use the application's current version.

The separate `presentation-timing-recovery.json` probe used a fresh official SDK stdio subprocess and the configured launcher to read both user-reported journeys. Both remained DISCLOSURE_ISSUED/version 2 with original issuance times, fresh clocks and no presentation/receipt/authorization recorded. Only status was requested; no live consumer evidence was submitted.

The following target-runtime commands were run from the repository (the local runtime path is relative to this workspace):

```powershell
& ./.build/python313/python.exe scripts/run_tests.py --output eval/results/tests-target.json
& ./scripts/verify_offline.ps1 -Python (Join-Path $PWD '.build/python313/python.exe') -PythonArgs @()
& ./scripts/smoke_test.ps1 -Python (Join-Path $PWD '.build/python313/python.exe') -PythonArgs @()
& ./.build/python313/python.exe eval/benchmark.py --calls 1000 --fixture-repetitions 20
& ./.build/python313/python.exe scripts/export_contracts.py
& ./.build/python313/python.exe scripts/run_tests.py --output eval/results/tests-sofa-redemption.json
& ./.build/python313/python.exe scripts/demo.py --scenario sofa-gift-card-redemption --output eval/results/sofa-redemption-smoke.json
& ./.build/python313/python.exe scripts/run_tests.py --output eval/results/tests-disclosure-previews.json
& ./.build/python313/python.exe scripts/demo.py --scenario sofa-gift-card-redemption --preview-only --output eval/results/sofa-disclosure-previews.json
& ./.build/python313/python.exe scripts/demo.py --scenario sofa-gift-card-redemption --output eval/results/sofa-preview-final-flow.json
& ./.build/python313/python.exe scripts/run_tests.py --output eval/results/tests-presentation-timing.json
```

Earlier core and SDK tests ran with the bundled CPython 3.12.14 development runtime; `tests-development.json` preserves that intermediate result. The latest target artifact is the presentation-timing run; the preceding offline artifact preserves the packaging checks. PowerShell script parser checks reported zero syntax errors. Calling `build_vendor.ps1` with Python 3.12 intentionally failed its version guard before vendor deletion, as designed. The full normal-Python venv build path is unverified here; actual cp313 vendor files were separately built and tested.

## Actual measurement scope and remaining gates

`benchmark.json` records 1,000 direct-core malformed/adversarial calls across ten families, all blocked, and 20 automated successful synthetic journeys with receipts and changed-cart replay blocks. Its p95 is **only this malformed core-call workload**, excludes MCP/LLM/human time, and does not establish a universal tool latency SLO. The actual number is preserved in the artifact; no baseline savings are claimed.

Successful authorizations exercised by tests/fixtures have valid bound receipts. Known sequence/stale-change attacks in this suite produce no unauthorized success. All exercised MCP output envelopes validate against the published JSON Schema. Same-key retries do not duplicate authorization or acknowledgment side effects. This is bounded test evidence, not proof of absence of every future bypass.

Remaining unverified gates: VS Code Copilot natural prompt behavior, 200 live prompts, 20 consecutive live human rehearsals, real rendered accessibility and durable consumer delivery, optional MCP App support, default Python-launcher availability on the target, and the full standard venv vendor-build script. Production identity, policy publishing/signatures and certified human presentation are outside the hackathon implementation.
