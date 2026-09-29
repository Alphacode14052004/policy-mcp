# Reusable prompt for the OfferProof pitch

Paste the prompt below into an AI presentation tool or coding assistant. Attach the latest build specification and real test evidence. Keep the evidence-status rules even when shortening the prompt.

```text
Act as a hackathon pitch coach and presentation designer. Create an editable seven-slide pitch deck for a five-minute live presentation at Synchrony's MCP hackathon, plus timed speaker notes. The challenge is to build an Offers and Disclosures MCP. The judges are a VP Technical Product Manager in Contact Center Technologies and an AVP Senior Cloud Engineer. Explain customer decision quality and support review value, backed by the MCP contracts, durable state and evidence checks. Do not invent their personal preferences or the rubric's weights.

Project: OfferProof MCP, a proposed server-side checkpoint for promotional eligibility, disclosure evidence and mock checkout authorization in an AI-assisted shopping journey. The build is in progress. Leave clear, editable spaces for a verified demo screenshot or recording and measured results. Do not fill these spaces with invented data or generated product screenshots.

Core story: An AI agent can explain and orchestrate a checkout, while deterministic server rules check eligibility and required evidence. The business hypothesis is fewer incorrect promotional decisions and easier reconstruction of what happened. These benefits need evaluation.

Use these project sources, with newer runnable evidence taking precedence over design intent:
- docs/BUILD_SPEC.md and docs/PLAN.md
- Prompts/Rovo-data.md, the supplied transcription of background findings. Distinguish its documented patterns, missing information and design inferences. Do not treat it as an independently verified source of current law or production policy.
- offerproof/models/contracts.py and offerproof/security/digests.py
- The latest test matrix, saved outputs, benchmark records and rehearsal recordings, if available
- The actual hackathon challenge statement and judging rubric, if I supply them

Evidence status as of the initial deck on 29 September 2026: the repository contains five tool schemas plus validation and hashing foundations. No end-to-end MCP run, authorization replay result, measured baseline, measured savings or full test report was found. Do not describe proposed behavior as demonstrated. Recheck the latest repository before updating these statements.

Synthetic scenario:
- $700 appliance plus $100 gift card gives an $800 cart.
- Only the $700 appliance qualifies in the fictional fixture. The gift card requires an explicit separate-tender choice.
- EPP-12-0APR requires $750 of eligible purchases, so it fails by $50.
- DI-6M has a fictional $200 minimum and qualifies on purchase amount.
- Deferred interest is conditional. Do not label it 0% APR, equate eligibility with suitability, promise that the user's payment preference will be met, or invent a minimum-payment calculation.
- Natural customer prompt: "Buy this $700 appliance and $100 gift card using the Synchrony option that best fits me. I want to avoid surprise interest and keep payments near $120 a month."
- Intended flow: discover tools, evaluate offers, prepare exact versioned mock disclosure, record renderer attestation, capture separate affirmative consumer acknowledgment, issue a cart-bound mock receipt, and reject that receipt after a cart change.
- Renderer attestation does not prove that a person read the page. The receipt does not constitute real payment authorization, customer authentication or legal approval.

Use this seven-slide structure and timing, totaling exactly 300 seconds:
1. OfferProof and the customer problem: 20 seconds
2. The $800 cart / $700 eligible example: 40 seconds
3. The five-tool design and implementation status: 40 seconds
4. The checkout walkthrough with a large space reserved for the verified demo: 100 seconds
5. Positive and negative acceptance cases with blank actual-result fields: 40 seconds
6. Measurable outcomes with blank counts/timing fields and clearly labeled proposed targets: 40 seconds
7. Proposed pilot and closing ask: 20 seconds

Quantification:
- Primary correctness measure: decisions matching the independently labeled expected outcomes / all evaluated cases. Include both valid and invalid cases and report the counts.
- Safety measure: invalid attempts that received mock authorization / all attempts expected to block. Target zero in the defined suite. Do not generalize beyond that suite.
- Evidence completeness: successful mock authorizations with all required, valid and correctly bound evidence / all successful mock authorizations. If the denominator is zero, report N/A.
- Operational value: paired review/reconstruction time for identical cases and completion requirements. Report sample size, median seconds and calculation method. Count incomplete tasks separately.
- Present targets, synthetic calculations, projections and observed results with different explicit labels. Use targets until actual measurements exist.
- Never fabricate a pass rate, prevented incident count, ROI, revenue uplift, customer satisfaction result, legal compliance conclusion or time-saving percentage.

Style:
- A concise, confident, plain-language pitch with one clear idea per slide.
- Dark charcoal background, warm yellow emphasis and readable light text. This is a design choice, not an official Synchrony template.
- Editable text, tables and a simple cart breakdown chart. Large type and generous whitespace.
- Use genuine screenshots only when available. Do not fabricate a product screenshot, successful tool output or audit record.
- Keep detailed implementation and sources in notes. Keep material synthetic-data and unverified-result labels visible on slides.
- Use mock data only, with no real customer data, credentials, internal endpoints or live Synchrony service connections.

Deliver the editable PPTX, a five-minute talk track, a clearly labeled fallback walkthrough, a measurement worksheet and concise answers to likely judge questions. If I provide a rubric, map its actual criteria to specific slides without inventing rubric weights.
```
