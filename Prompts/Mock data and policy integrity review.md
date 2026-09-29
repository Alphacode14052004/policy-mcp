
## Prompt 3 — Mock data and policy integrity review

```text
Act as the data-contract and policy-as-data reviewer for OfferProof MCP. Inspect every file under `mock-data/` and `demo-data/`, plus the loaders, schemas, disclosures, calculations, and referential-integrity tests. All records are synthetic hackathon data.

Verify and fix:
- explicit data classification and not-for-production markers;
- immutable IDs, versions, effective dates, legal approval metadata, predecessor/rollback, and checksums;
- references among offers, disclosures, account terms, presentation policies, renderer profiles, and jurisdiction policy bundles;
- plan families: deferred interest, true equal payment/0%, reduced APR, configured custom amortization, cashback revolving, and standard revolving;
- exact plan-specific disclosure semantics, including that deferred interest is never called 0%;
- standard APR is resolved from account terms, not hard-coded;
- integer cents, Decimal calculations, deterministic rounding, and allocation reconciliation;
- the $700 appliance + $100 gift-card scenario: $800 total, $700 eligible; EPP-12-0APR $750 threshold fails; DI-6M $200 minimum qualifies for the full eligible $700; $100 is explicitly separate and requires confirmation;
- checkout allocation is not confused with post-purchase servicing/payment allocation;
- MOCK_DEFAULT and explicitly fictional MOCK_STATE_CAP resolve through LegalPolicyResolver rather than billing-state hard-coding;
- unknown, unsigned, expired, or conflicting policy fails with POLICY_REVIEW_REQUIRED.

Add or improve startup validation and tests for every defect found. Do not invent real Synchrony terms or claim a legal conclusion. Run the relevant test suite and report exact results and changed files.
```
