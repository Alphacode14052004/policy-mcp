# How to quantify OfferProof

Measure the quality of the completed offer journey first. Then measure how much easier that journey is to review. A count of tools or lines of code shows implementation scope, but does not establish customer or business value.

## What the current evidence supports

Repository review on 29 September 2026 found five tool schemas in `offerproof/models/contracts.py`, schema-validation logic, and hashing utilities. The build specification describes a broader intended system. No end-to-end server results, replay-block report, baseline timing data or complete test matrix were present in the reviewed files.

The $800 total, $700 eligible subtotal, $100 exclusion and $50 shortfall are calculations from a **synthetic specification**, not observed customer outcomes or measured software results. The pitch deck deliberately labels behavior as planned and performance as proposed targets. Recheck these labels after the implementation changes.

## The evaluation scorecard

| Metric | Calculation | Proposed acceptance target | Evidence to save |
|---|---|---|---|
| Decision correctness | Decisions matching the labeled expected outcome / all evaluated cases × 100 | 100% in the fixed acceptance suite | Case ID, expected offer/subtotal/outcome, actual result, reason code, trace |
| Unsafe acceptance | Attempts expected to block that received mock authorization / all expected-block attempts × 100 | 0% in the defined adversarial suite | The attempted bypass, expected block reason and actual result |
| Evidence completeness | Successful mock authorizations containing every required valid evidence item / all successful mock authorizations × 100 | 100% | A linked cart digest, offer/policy/terms/disclosure versions, presentation attestation, required affirmative acknowledgment, expiry and verifiable receipt |
| Review time | Compare elapsed seconds for reconstructing the same cases using the baseline workflow and OfferProof evidence | Establish a baseline, then set a target | Start/end times, reviewer, case ID, completion quality, interruptions |
| Demo reliability | Complete successful rehearsals / all attempted rehearsals | Proposed readiness goal: 20/20 consecutive runs | Per-run timestamp, final outcome, intervention count and failure reason |

An empty denominator is **N/A**, never 100%. Report numerators and denominators with every percentage. An expected block counts as correct only if it blocks for the expected reason. A crash, missing output or timeout is a failure for the correctness evaluation. Track those failures separately too.

The build plan mentions 32 scenarios. That number is a planned scope, not a measured result or a supplied, complete list. Locate or finish the traceable case matrix before saying "32/32 passed."

## A practical pilot

1. Freeze the code version and fictional fixtures. Record the evaluation date and runtime. Define expected answers independently of the system's output.
2. Build a balanced case set: valid journeys, threshold boundaries, excluded items, changed carts, missing acknowledgment, altered disclosure text, expired evidence, unknown context and receipt reuse. Give every case an expected outcome and reason.
3. Run the same cases through the implementation and save structured results. A system that blocks all requests must fail the valid cases.
4. For review time, start with **30 synthetic cases** and have reviewers reconstruct the eligible amount, selected offer, disclosure version, acknowledgment and final outcome in both workflows. Thirty is a proposed pilot size, not a statistical guarantee.
5. Alternate which workflow the reviewer uses first and randomize case order to reduce learning effects. Use the same task and completion standard. Record unsuccessful attempts rather than dropping them.
6. Report actual sample size, successes and failures. For paired completed cases, show the median baseline time, median OfferProof time and median per-case difference. Do not imply that subtracting two medians equals the median paired difference.
7. If using a percentage, state the method: aggregate time reduction = `(sum of baseline seconds - sum of OfferProof seconds) / sum of baseline seconds × 100` over the same paired completed cases. Report excluded or incomplete pairs alongside it.
8. Keep software latency separate from human review time. End-to-end agent time, server execution time and reviewer time measure different things. Only report p95 after recording enough timestamped observations and explaining the workload.

## Honest wording for the pitch

**Before measurements:** "Our targets are correct outcomes on every labeled acceptance case, no invalid authorizations in our adversarial suite, and complete evidence for each successful mock journey. We will compare reviewer time on the same cases."

**After measurements:** "On [N] synthetic cases, [X] matched the expected outcome. We observed [U] invalid authorizations across [B] expected-block attempts. [E] of [A] successful authorizations contained complete evidence. Across [P] completed paired reviews, total review time decreased by [R]%, using the same completion standard."

Fill these brackets only from saved results. If a result misses the target, report it and explain the limitation.

## Turning time into a business projection

Once a baseline exists, a simple capacity estimate is:

`monthly hours of reviewer capacity released = applicable monthly reviews × observed average seconds saved per review / 3,600`

Use the **mean paired difference** for an aggregate-hours projection and show the median separately for a typical case. Obtain the applicable review volume from the business owner. Deduct new operating effort when estimating net benefit. Multiplying hours by a documented loaded hourly cost produces an estimated labor-capacity value, not necessarily cash savings. Keep avoided incidents and revenue uplift out of the pitch until data supports them.

## Lightweight worksheet to fill

For functional cases, record:

`run_id, code_version, case_id, expected_outcome, expected_reason, actual_outcome, actual_reason, correctness_pass, expected_block, mock_authorized, evidence_complete, trace_path`

For paired timing, record:

`pair_id, case_id, reviewer_id, workflow_order, baseline_seconds, offerproof_seconds, baseline_complete, offerproof_complete, quality_check_pass, interruption_note`

Use synthetic reviewer IDs and references rather than personal or customer information. Keep raw evidence local. The fields above are a worksheet schema, not fabricated measurements.
