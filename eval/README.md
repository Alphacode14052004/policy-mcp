# Evaluation protocol

`scripts/run_tests.py` writes per-test results. `benchmark.py` runs deterministic malformed calls and fixture journeys and writes its measured scope. `generate_prompts.py` creates 200 prompts; generating this file does not run an LLM.

Run: `py -3.13 eval/benchmark.py --calls 1000 --fixture-repetitions 20`. The latency reported there is the malformed-call workload only, not all tool types or end-to-end consumer time. No integration-hour or legal-review savings are inferred from it.

For the 200-prompt live evaluation, open a fresh VS Code Copilot Agent chat for each case, enable only OfferProof tools where practical, attach the cart, and submit only `prompt`. Record model/host/version, first tool, corrective hints (must be zero), exact disclosure display, consumer consent prompt, outcome, elapsed seconds and transcript location. A missing consent response is an expected waiting state, not a pass for authorization. Include ambiguity, refusal, decline and failure outcomes in scoring. Do not fabricate renderer evidence for a claimed human-viewing test.

For 20 consecutive **live** rehearsals, follow DEMO_RUNBOOK.md and append one row to `rehearsals.csv` each time. Automated fixture repetitions do not count. Gate: correct first tool, eligible subtotal, no hidden offers, conditional DI warning, separate tender confirmation, exact text, explicit consent, signed evidence and changed-cart block. Any failed gate resets the consecutive-success count.

Measurement worksheet: `docs/MEASUREMENTS.csv`. Establish before/after baselines using equivalent synthetic integration tasks and reviewer effort logs; document sample size and conditions. Dollar savings remain hypotheses until measured.
