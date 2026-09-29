# OfferProof five-minute speaker script

Audience: VP Technical Product Manager, Contact Center Technologies, and AVP Senior Cloud Engineer.

The seven slide slots total exactly 300 seconds. Actual speaking time needs rehearsal. The deck intentionally reserves spaces for your demo and results while the build is in progress. Speaker notes are also embedded in the PowerPoint.

## SLIDE 1 · 0:00–0:20 · 20 seconds
Imagine an AI shopping assistant that finds a financing offer but misses which items qualify or which disclosure the customer must acknowledge. OfferProof is our proposal for adding a verifiable checkpoint before promotional checkout. This hackathon prototype uses synthetic data and mock policies.

## SLIDE 2 · 0:20–1:00 · 40 seconds
Here is the mistake we want to prevent. The basket totals eight hundred dollars: a seven-hundred-dollar appliance and a hundred-dollar gift card. Our fictional twelve-month zero-percent offer requires seven hundred and fifty dollars of eligible purchases. Using the basket total would produce the wrong decision. The eligible amount is seven hundred, so the customer is fifty dollars short. The gift card needs separate payment. All these thresholds are synthetic. We are demonstrating a decision boundary, not a real Synchrony offer.

## SLIDE 3 · 1:00–1:40 · 40 seconds
OfferProof puts the checks behind five MCP tool contracts. Start evaluates the cart. Prepare binds an offer to its disclosure version. Record separates presentation from consumer acknowledgment. Authorize checks the evidence, and Recover reports the next permitted step. The agent handles the conversation, while server rules control permission to continue. The design persists journey state behind an ID, uses version checks and idempotency for retries, and binds evidence to the cart. For support teams, the intended benefit is a traceable explanation of the offer decision. Implementation is in progress.

## SLIDE 4 · 1:40–3:20 · 100 seconds
This is the natural-language request we want the agent to handle. It names the customer’s goal, not our tools. The intended flow first separates the gift card and explains why the twelve-month offer fails. Our fictional six-month deferred-interest offer qualifies on purchase amount, but eligibility alone does not make it suitable. The agent must explain the conditional interest terms and let the customer decide. It must not relabel deferred interest as zero-percent APR or promise a minimum payment.

Next, we show the exact mock disclosure, capture the renderer’s presentation attestation, and record a separate affirmative acknowledgment. The proposed Offer Trust Passport binds that evidence to the cart and the versions used. Finally, changing the cart should invalidate the old evidence and require reevaluation.

This is a planned walkthrough until a recorded end-to-end run proves it. A renderer attestation is evidence from the mock renderer, not proof that a human read the page.

## SLIDE 5 · 3:20–4:00 · 40 seconds
These are the acceptance cases that make the proposal testable. A legitimate journey with matching evidence must proceed. A changed cart, a missing acknowledgment, or altered protected text must block. Testing both sides matters: a system that blocks everything is not useful. The planned passport links the cart digest, version identifiers, event times and expiry with an HMAC. It is a local mock receipt, not legal approval or customer authentication. We need recorded test results before calling these controls demonstrated.

## SLIDE 6 · 4:00–4:40 · 40 seconds
We will quantify both decision quality and support effort. The first measure is correct outcomes across labeled valid and invalid cases. The second is invalid authorizations, with a target of zero in the test suite. The third is complete evidence for successful mock authorizations. Finally, we will compare the time a reviewer needs to reconstruct the same decision manually and with OfferProof. Our evaluation is still pending. Until those runs finish, the numbers in the target column remain goals. We are not claiming business savings yet.

## SLIDE 7 · 4:40–5:00 · 20 seconds
Our next step is a scoped pilot with one synthetic merchant journey and thirty paired review cases. We will validate the complete flow and measure whether the evidence makes review faster. OfferProof gives us a concrete way to test whether an AI-assisted checkout can explain and substantiate its promotional decision.

## The 100-second demo slot

This replaces the slide 4 narration when the implementation is ready. Use a local, synthetic cart and a real recorded result. Do not infer that the expected outputs below have already occurred.

| Within the slot | Show | Say |
|---|---|---|
| 0–15 seconds | Enter the natural customer request | "The request expresses the customer's goal. It does not tell the agent which tools to call." |
| 15–35 seconds | Actual eligibility output | "The total is $800, but only $700 qualifies. The fictional $750 minimum rules out the twelve-month offer. The gift card needs separate payment." |
| 35–60 seconds | Exact mock disclosure, renderer event and separate acknowledgment | "Deferred interest is conditional. We preserve that warning and require a separate affirmative consumer action. Eligibility does not mean this is necessarily the best choice for the customer." |
| 60–80 seconds | Actual mock receipt or passport and linked events | "This record binds the cart to the versions and events used in the decision. It gives a reviewer a specific trail to inspect." |
| 80–100 seconds | Change the cart and replay the old receipt | "The cart changed. The previous evidence must not authorize this new state." Report the actual response and reason. |

Use the canonical request from the project:

> Buy this $700 appliance and $100 gift card using the Synchrony option that best fits me. I want to avoid surprise interest and keep payments near $120 a month.

If setup or a tool call stalls for roughly ten seconds, switch to the fallback so the overall pitch remains within five minutes. Reserve the last twenty seconds of the demo slot for the changed-cart check. Do not let the product tour consume the value slide.

## Fallback script

**If a verified prior run exists:** "The live session is unavailable, so this is a recording of our synthetic test run from [date/version]. I will show the same eligible-subtotal decision and changed-cart block." Use only a recording with matching code/fixture provenance and state any material differences from the current build.

**If no verified run exists yet:** "The implementation is in progress, so I will walk through the expected behavior rather than show a completed run."

Then use this explanation while showing slides 2, 4 and 5:

"The shopper has an $800 basket, but the fictional policy excludes the $100 gift card. That leaves $700 eligible. The twelve-month offer needs $750, so it should fail. A six-month deferred-interest offer meets the purchase threshold, but the assistant must explain its conditional terms and let the customer decide.

"The next stage should preserve the exact mock disclosure and distinguish renderer presentation from the customer's affirmative acknowledgment. The proposed passport binds the resulting evidence to the cart and versions used.

"The final check is the important one. If we change the cart and reuse the previous receipt, the server should block that attempt and require a fresh evaluation. These are acceptance requirements. The blank results column will hold the actual outcomes once the implementation runs."

Stay inside the same 100-second slot. A planned walkthrough is not a substitute for measured correctness, and the result fields remain blank until there is evidence.

## Judge questions to prepare for

**Why does this need MCP?**

MCP provides the agent-facing tool interface. The reusable part is a consistent contract for starting a journey, preparing the disclosure, recording evidence, authorizing a mock outcome and recovering state. MCP alone does not enforce policy. The server's validation and state transitions must do that.

**Why not add stronger instructions to the agent prompt?**

Prompt instructions guide behavior. The proposed server rules enforce preconditions even if the agent calls tools in the wrong order or sends stale evidence. The changed-cart replay is the intended demonstration of that boundary.

**What does a contact center gain?**

A support reviewer could retrieve the offer, eligible amount, exact disclosure version and acknowledgment linked to a journey. The value hypothesis is less time reconstructing the decision. We propose paired timing tests before claiming lower handling time, fewer calls or better customer satisfaction.

**How would this scale beyond a local prototype?**

The current design uses local SQLite persistence and mock identity bindings. A production design would need authenticated callers, scoped authorization, managed state storage with concurrency guarantees, secrets and key management, trusted renderers, approved content publishing and operating controls. Those capabilities are outside the current claim. The contract and deterministic core are intended starting points, not evidence of production readiness.

**Does the passport prove the customer read the disclosure?**

No. The prototype models a renderer attestation and a separate affirmative consumer event. It does not establish comprehension or production-grade identity. The HMAC protects the mock receipt's integrity within the prototype's trust boundary.

**How do you avoid a system that blocks everything?**

Include valid journeys that must succeed as well as invalid journeys that must block. Evaluate the expected outcome and reason, not just the count of rejected requests.

**How much money does it save?**

We do not have measured savings yet. First measure correctness, evidence completeness and paired review time. A later capacity projection can multiply observed average seconds saved by the business owner's applicable review volume. That would remain a projection, not realized cash savings.

**Is this approved disclosure copy or a real Synchrony policy?**

No. All rates, policies, merchants and approvals in the prototype are fictional fixtures. The production proposition would require approved source content and policy ownership. The prototype performs no real credit decision or payment authorization.

## What to fill before presenting the completed build

- Slide 4: replace the reserved space with a verified capture, or use it as the handoff to the live application. Keep a matching local recording if available.
- Slide 5: replace each blank with the actual outcome and keep its trace reference in the notes. Preserve the distinction between expected and observed behavior.
- Slide 6: fill the numerator and denominator for each count. For review time, put baseline first and OfferProof second, and add the number of completed pairs in the notes. Leave unavailable metrics marked "Not measured".
- Update future-tense claims only after the corresponding behavior works. Keep mock-data boundaries even when the demo succeeds.
- Add your team name or presenter name to the cover if desired. Rehearse the full sequence with a timer. The allocated timing totals five minutes, but the actual delivery has not been rehearsed here.
