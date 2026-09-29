ORDERED TRANSCRIPTION OF ALL 19 UPLOADED IMAGES
====================================================

Notes:
- Images are transcribed in the exact upload order.
- Overlapping/duplicate screenshots are intentionally preserved rather than silently removed.
- [cropped], [obscured], or [unclear] means the original screenshot does not visibly contain enough information to recover the missing text with confidence.
- Browser/application UI words are included when they are legible.
- Image 1 is entirely black and contains no readable text.

IMAGE 1 — 1000334910.jpg
------------------------
OfferProof MCP: what the internal docs say, and a master prompt
for Codex

The internal docs give you useful patterns for promo types, disclosure presentation, error envelopes and
hackathon rules. They don't give you authoritative rules for how eligibility is calculated, how disclosure versions
are approved, how jurisdiction is decided, how long audit records are kept, or any baseline metrics. Those gaps
are marked Not found below, and the master prompt at the end treats them as fictional placeholders.

How to read this:

• Owner = the Confluence page author or last editor. It is not a confirmed accountable owner unless the page
  says so.

• Dates are last-modified dates.

• Status: Current = recent working or reference doc. Historical = more than 12 months old. Inference = my own
  design recommendation, not from a source.

• I left out merchant numbers, environment URLs, mock-server URLs, live APR values and any test-applicant
  records that appeared in search results. None of them should go into the repo.

A. Findings with references

1. Promotion catalog and eligibility

Finding | Source · owner · date | Status / confidence

Promo lookup comes from
PromoLookupService. The HS
endpoint (sale-slip lookup) returns
managePromotion (min/max
purchase, start/end dates),
paymentPlan (disclosure text,
HTML, monthly_paymentFactor),
[unclear field names], and a
[unclear]PriceList / specialPromoList
at split. HA returns no disclosure
fields and is sourced from offerDb,
"which may not be upto date". Plan
numbers are program scoped and
do not match across flows.

HA vs HS — PromoLookupServ
ice Comparison · Asish Ghimire ·
2026-08-14

Current · High, as a field pattern. It
is a comparison page, not a
system-of-record spec.


IMAGE 2 — 1000334887.jpg
------------------------

Visible document text:

"UI must not rely on HA for legal copy." Integrators should check
eligibility against HS
managePromotion min/max and
dates.

Same

Current · High

Pre-apply promo discovery uses
merchant/provider context, product
type, channel, amount thresholds,
promo configuration and effective
dates. It explicitly excludes credit
decisioning, acceptance and
authorization.

Promotion Display (Pre-Apply D
iscovery) · 2026-08-05

Current · Medium

H&W: promotional financing applies
to purchases of $200 or more.
Below that, standard terms apply.

Promo Disclosures - Revolve -
Health & Wellness (CareCredit) Ma
rketing Promo Disclosures ·
Clarinda Gurr · 2026-09-23

Current · High (H&W on[cropped])

One client disclosure requires the
qualifying amount to be "on one
receipt", with a threshold measured
after discount.

WAVE 09 F&D disclosures
(attachment) · 2026-09-25

Current · Client-specific[cropped]

The HS payment-estimator mockup
says the estimate "excludes taxes
and delivery".

Promos Email:Mock[cropped]
(attachment) · 2026-04-22

Current · Low. It covers
display, not eligibility.

Partial approval must be disclosed

MPQ Disclosure Requirements
[lower source text obscured]

Current · High, for MPQ[cropped]

Describe what you want to know or do next


IMAGE 3 — 1000334888.jpg
------------------------
Visible browser/UI text:
[cropped tab fragment]
Synchrony-preview...
how to set intellij s...
view-source:
Create

Visible document text:

"UI must not rely on HA for legal
copy." Integrators should check
eligibility against HS
managePromotion min/max and
dates.

Same

Current · High

Pre-apply promo discovery uses
merchant/provider context, product
type, channel, amount thresholds,
promo configuration and effective
dates. It explicitly excludes credit
decisioning, acceptance and
authorization.

Promotion Display (Pre-Apply D
iscovery) · 2026-08-05

Current · Medium

H&W: promotional financing applies
to purchases of $200 or more.
Below that, standard terms apply.

Promo Disclosures - Revolve -
Health & Wellness (CareCredit) Ma
rketing Promo Disclosures ·
Clarinda Gurr · 2026-09-23

Current · High (H&W only)

One client disclosure requires the
qualifying amount to be "on one
receipt", with a threshold measured
after discount.

WAVE 09 F&D disclosures
(attachment) · 2026-09-25

Current · Client-specific only

The HS payment-estimator mockup
says the estimate "excludes taxes
and delivery".

Promos Email:Mock[cropped]
(attachment) · 2026-04-22

Current · Low. It covers estimator
display, not eligibility.

Partial approval must be disclosed

MPQ Disclosure Requirements
[lower source text obscured]

Current · High, for MPQ

Describe what you want to know or do next
Auto


IMAGE 4 — 1000334890.jpg
------------------------
Visible browser/UI text:
[cropped address-bar text]
Synchrony-preview...
how to set intellij s...
view-source:
Create

Visible document text begins in the middle of a row:

need for another payment
method"). Checkout may involve
split tender. Multiple offers must
have equal prominence, with none
pre-selected.

[first name/source preceding this is cropped] Calvert · 2026-09-08

Cart total vs. eligible-item subtotal,
how excluded lines (e.g. gift cards)
are handled, stacking, multi-promo
precedence, tax/shipping in
eligibility, the owning team, and
change versioning.

—

Not found

2. Plan families

Family | Internal codes seen | Evidence | Confidence

Deferred interest

WPDI; FPDI (fixed-pay
deferred interest)

Promotion Types and
language for Home Spec
ialty · Todd Kryszczak ·
2026-05-05; H&W page

High

Equal pay, no interest

EPNI; EPNIIO / RIMP
(reduced intro payment);
EPNIIOPF (with promo
fee)

Promo Disclosures -
Revolve - Home Specialt
y Marketing Promo Discl
osures · 2026-07-16

High

Reduced APR, fixed term

FPRR / FPRA / FPRI /
FRRA / EPP (spelling
[bottom obscured])

H&W, HS pages;
PromoLookup page

Medium. Naming isn't
consistent (see D).

Describe what you want to know or do next


IMAGE 5 — 1000334891.jpg
------------------------
Standard revolving | PPPP | PromoLookup; H&W | High

Custom amortization;
cashback revolving | — | Not found | —

Installment (Pay Later) |
Standard, AutoPay
discount, waived interest,
intro rate (listed only) |
HS Promotion Types
page |
Low

Disclosure facts each family needs (from the H&W page):

• Deferred interest: "No Interest if Paid in Full Within XX Months", the retroactive-interest statement, and the
minimum-payment statement. The suggested payment is the greater of (amount ÷ months, rounded up) or the
current minimum payment.

• EPNI: amount ÷ months, rounded up to the next whole dollar. The last payment(s) may be lower because of
that rounding.

• Fixed reduced APR: amount × factor %, rounded up. Show total payments with interest and the promo period.

• All families: regular account terms, "New Accounts" APRs, and existing-cardholder language.

Approved partner-facing names: Not found. The closest reference is Workfront-approved title copy, dated
12/2025 on the H&W page.

Confusable or changing phrases:

• B2B currently says "0% APR and Equal Monthly Payments Required Until Paid in Full", and there is work to
change it to "0% APR with Equal Monthly Payments" (H&W page).

• If a non-aggregator estimator is open to non-cardholders, it must include "G27 language" at the top of the
deferred-interest section (H&W page).

3. Disclosure content and approval


IMAGE 6 — 1000334892.jpg
------------------------
3. Disclosure content and approval

Finding | Source | Confidence

Promo title and "Learn How" copy
show a Workfront approval
("Workfront approved 12/2025 (see
Carrie Lamoreaux for WF#)";
HS/Home page cites Workfront #
on page).

H&W page;
Promo Disclosures
- Revolve - Home Marketing Prom
o Disclosures · 2026-04-28

Medium: Shows Workfront is used
for approval; not a documented
publishing workflow.

Some fields are variable: XX
months, amount, APR, factor, min
pay (which "can change during
NATUs"). Segments are included or
excluded by channel (for example,
drop the Mastercard copy in
channels without MC acquisition).

H&W page

High

API-supplied legal text must be
shown word for word, with equal
prominence and readable,
accessible typography.

MPQ Disclosure Requirements

High

Regulated values (APR, balances)
must be shown exactly as
returned; no rounding or

Account Summary V2 — Child
3 Error Handling and Troubleshoot
ing · 2026-09-24

High, as a pattern


IMAGE 7 — 1000334894.jpg
------------------------
zero.

Tamper detection for merchant-
rendered promo content: a
MutationObserver on the widget
sends partner_id, flow_type,
mutations[] and timestamp to
New Relic.

Audit Report for Merchant Cont
rolled widgets · Abhishek Kumar ·
2026-07-29

Current, in progress · High as an
analog

Prompts and scripts must be
"legal approved,
version-controlled, and audited".

AI Agents & Agentic Commerc
e Overview · Sreeni Karnati ·
2026-09-28

Informational guide - Medium

A disclosure registry/ID scheme,
locale versioning, maker/checker,
rollback, supersession,
checksums/signatures, and
emergency withdrawal.

—

Not found

4. Policy and jurisdiction

• Historical, 2022: one card's T&C says the agreement is governed by federal law and, where state law applies,
Utah law (CathayCathay T&C's). Don't generalize from it.

• State rules do change flows. For example, CA SB 639 limits what providers can do (State Regulations - H&
W Summary · 2026-09-02). SYF evaluation includes "state / legislative suspend" (API Usage Assessment
(ACG, POS, and Admin) · 2026-09-15). The MPQ page says disclosure obligations depend on "channel,
product, and jurisdiction".

• Not found: a policy service or bundle that decides which terms apply, the list of inputs it uses, and fallback
behavior when inputs are missing, conflicting or expired.

• Fictional state cap: no document covers this. It is my inference and a build constraint that any mock "state
[cropped at image bottom]


IMAGE 8 — 1000334898.jpg
------------------------
Visible browser/UI text:
Search
Create

5. Account terms and calculations

• Account-level APRs are "pulled into" the transactional disclosures (Promo Disclosures - APD OFP Languag
e comparison for L&C review - WIP), and the H&W page links a "Terms and Rates" page.

• Post-purchase servicing (active promo balances, PTI eligibility and enrollment) belongs to the Manage Pro
motion Service API Product Specification - Account Promotions (2026-09-24) and to SyPI's read-only Te
st Data Requirements - Promotional Purchases (2026-09-15). Neither is a checkout concern.

• Not found: the authoritative source for index/margin, variable/fixed indicator, payoff deadline, and final-
payment rounding rules. The only rounding guidance is the disclosure wording above.

• Inference: the prototype should not model interest accrual, deferred-interest retroactive charges, payment
allocation, minimum-payment calculation, or credit decisioning.

6. Presentation, accessibility and acknowledgment

• The MPQ page covers several points:
  ○ Disclosure timing is tied to the action: copy appears before the eligibility check, acceptance, or signing.
  ○ No consent checkbox may be pre-selected, and consent requires an affirmative act.
  ○ Durable access (print, email or a persistent link) is needed where required.
  ○ Consumer-only actions are kept separate from provider or agent actions.
  ○ Audit evidence covers UTC timestamps, disclosure version IDs, user action events, device context and
    request/response references.
  ○ Certification should test the rendered experience, not just the API.

• Customer confirmation is required before regulated actions, and consent receipts carry scope, timestamp,
partner, channel and expiry (AI Agents & Agentic Commerce Overview).

• Accessibility: the Bank standard is WCAG 2.1 AA (ADA/Accessibility, 2020, historical but states the
standard; reaffirmed by Accessibility · 2026-08-12). The 2026 audits use WCAG 2.2 AA.

• Language: Spanish must carry through the whole journey with no fallback to English mid-flow (Spanish La
nguage Support for MPQ Offer Screens (IdApply), 2026-04-21, In Review).


IMAGE 9 — 1000334899.jpg
------------------------
• Not found: a definition separating "delivery" from "verified presentation"; a renderer evidence schema (digest,
scroll, font); which promos need acknowledgment; how to record decline or timeout.

7. Audit and evidence

• The Agentic Overview calls for multi-hop correlation audit, tool-level scopes, policy-as-code outside the
model, and kill switches (by partner, agent, tool or route).

• The RAG Threat Model: Security Objectives, Assets, Trust Boundaries, Threats Analysis and Risk Register
(2026-09-14) lists immutable audit fields: user, tenant, request ID, timestamp, prompt hash, authorization and
policy decisions, tool invocation.

• The target-state deployment says "Zero content in logs, zero server-side session persistence" (Agentic Co
mmerce Deployment Reference · 2026-08-04; owner during the POC is the Method Residency Pod).

• Not found: an event taxonomy, retention period, the accountable audit owner, and an incident/reconciliation
process. Whether failed attempts must be logged is also not stated. I recommend logging them (inference).

8. Partner/MCP contract

• Headers: X-SYF-Request-TrackingId must be unique per request, and X-SYF-Request-CorrelationId should
be included (Account Promotions API spec).

• Error envelope: code, message, trackingId, transient. A 400 adds errors[], a 422 adds
businessErrors[], and codes are dotted strings (LTMS - Partner API build (Clover) · 2026-08-16).

• Gateway codes such as application.businessError and gateway.service.unavailable are defined in the
Swagger Spec - Common Def Updates for error codes and description (2026-04-17).

• Route on code, never on message, and don't show message to consumers (Account Summary V2).

• Trust boundary: user and retrieved content is untrusted (RAG Threat Model TB 1/TB 4). "Consumer-safe copy"
mappings exist, but the Account Summary catalog is still marked TBD.

• Not found: minimum partner-supplied cart/renderer fields, and an approved list of identifiers that are safe for
synthetic data.


IMAGE 10 — 1000334900.jpg
-------------------------
9. Security and privacy

• Hackathon FAQ: "Can I use SYF data? Absolutely not! No use of Non-prod or Prod DB or APIs and Apigee
proxy end-points." Build mock data with Kaggle or SYF GPT (MCP First Hackathon Details & FAQ Page (Sep
t. 28 29 2026) · Sophia Lugo · 2026-09-27).

• Copilot: no sensitive or proprietary information in prompts (Copilot Rules of Participation).

• PII in logs: never in cleartext; no logging of auth headers or tokens; no full-body logging for PAN, SSN or
credentials (Define PII Masking Standards and Implementation Patterns for Java APIs · owner Application
Engineering + Security · 2026-08-13). Part of this page was blocked by Atlassian Guard, so my view of it is
partial.

• Secrets: Vault, AWS Secrets Manager and similar (Secrets Management Blueprint: Draft, draft,
2026-09-17). The published Data Protection (2026-09-04) also applies.

• SSNs, credit scores, account numbers: the "no SYF data" rule covers these. Barring the prototype from
accepting them at all is my recommended constraint (high confidence).

10. Developer and demo environment

Item | Documented | Source

Python

"3.11+ recommended" / "3.11 or
later". Python is mass-provisioned.
No Python 3.13 policy found.

MCP Hackathon - Build Tutoria
l · Matthew Nova · 2026-09-23;
MCP Hackathon Guide - Build a
nd Demo Your MCP Server ·
Prabakaran Anandaraj ·
2026-09-24

SDK

Pin mcp==2.0.*. Use from
mcp.server.mcpserver import
[cropped at image bottom]


IMAGE 11 — 1000334901.jpg
-------------------------
mcp.server.mcpserver import
MCPServer and
run(transport="stdio"). Spec
change of 28 Jul 2026: no session
handshake and no in-memory
state. Roots, Sampling, server
Logging and HTTP+SSE are
deprecated.

VS Code / Copilot

"VS Code 1.13 or newer" with
Copilot Chat Agent mode. VS Code
caps active tools at 128.
tool_search can return 403 on
the SYF network; the workaround
is #tool-name or a custom UI.

Guide

Node

Needed for npx MCP Inspector.

Tutorial

Postman

The hackathon has a mocked-API
Postman workspace. Keep URLs
out of .env.example.

FAQ; Tutorial

Local storage

"Write it to a file or a database and
hand the caller back an ID."

Guide

MCP Apps

Not supported by Bedrock
AgentCore. One pilot used
Node/Express instead, and "does
not follow the model for how SYF
wants to deploy MCPs".

ARB ChatGPT App · 2026-08-31


IMAGE 12 — 1000334902.jpg
-------------------------
Approved dependency mirrors,
vendoring, code scanning,
OS/architecture list

Not found

—

11. Metrics

No measured baselines were found for partner-integration effort, disclosure defects, legal review cycle time, audit
reconciliation effort or incidents. The hackathon problem statement is qualitative only. Select Pay's figures (for
example, disclosure acknowledgment above 95%) are targets, not baselines, so don't cite them as savings.

B. Unanswered questions and who to ask

The owners below come from page authorship or roles named in the sources. Please confirm them.

Question | Suggested owner

Eligibility base (cart vs. eligible subtotal), excluded
items, stacking, tax/shipping, how rule changes are
approved and versioned

PromoLookupService owner (Asish Chimire's team);
Sales Slip promo API field-mapping owner Gari Arken
(per the Home page)

Approved partner-facing plan names; FPRR naming;
G27 usage

Clarinda Gurr (disclosure pages); Carrie Lamoreaux
(Workfront approvals); Daniel McElhannon (EPNI title
change)

Disclosure registry, versioning, withdrawal,
checksums

Marketing/Legal disclosure owners via Workfront
(TBD)

Jurisdiction policy inputs and fallbacks

Legal/Compliance (TBD); State Regulations page
[cropped at image bottom]


IMAGE 13 — 1000334903.jpg
-------------------------
[cropped continuation from previous screenshot:]
checksums
(TBD)

Jurisdiction policy inputs and fallbacks

Legal/Compliance (TBD); State Regulations page
owners

Renderer evidence and acknowledgment rules

Jane Calvert (MPQ disclosure taxonomy); Legal

Audit taxonomy, retention, reconciliation owner

TBD; Method Residency Pod / SYF infrastructure
workstream for the target state

Python 3.13, dependency mirror, scanning

Hackathon leads Matthew Nova / Prabakaran
Anandaraj; Sophia Lugo for logistics

Baseline metrics

Agentic Commerce stakeholders (Lauren Ozimek,
Alexander Bronze per the Agentic Commerce Han
doff Hub by the Method Residency Pod)

C. Synthetic data dictionary (all values fictional)

Entity.field | Type / format | Example (fictional) | Notes

merchant.merchant_id

MOCK-MER-[0-9]{4}

MOCK-MER-0001

Never 16 digit. Real MIDs
are 16 digits.

program.program_id

MOCK-PRG-[A-Z]{3}

MOCK-PRG-HOM

channel

enum ONLINE_AGENT,
IN_STORE_ASSISTED,
CALL_CENTER


IMAGE 14 — 1000334904.jpg
-------------------------
CALL_CENTER

promo.promo_id /
version

MOCK-PROMO-### / semver

MOCK-PROMO-101 / 1.2.0

promo.plan_family

enum
DEFERRED_INTEREST,
EQUAL_PAY_NO_INTEREST,
REDUCED_APR_FIXED_TERM
, STANDARD_REVOLVING

Mock codes only. Real
codes (WPDI, etc.) are
kept in a separate
mapping resource.

promo.min_purchase_cen
ts /
max_purchase_cents

int

50000

Money is always integer
cents.

promo.term_months,
promo.mock_apr_bps,
promo.mock_payment_fac
tor_bps

int

24, 999, 200

Labeled FICTIONAL

promo.effective_start/
end

ISO date

promo.eligible_categor
y_ids[] /
excluded_item_types[]

list

["CAT-APPL"] /
["GIFT_CARD"]

promo.stacking_policy

enum NONE,
SINGLE_PROMO_PER_CART

Mock default NONE

[bottom row begins but is cut]


IMAGE 15 — 1000334905.jpg
-------------------------
cart.cart_id, lines[]:
{sku, category_id,
item_type, qty,
unit_price_cents},
tax_cents,
shipping_cents

Structured fields only; no
free text

disclosure.disclosure_
id, version, locale
(en-US, es-US),
channel, status
(APPROVED_MOCK,
WITHDRAWN),
effective/review
dates, segments[]
{segment_id,
protected:boolean,
text}, allowed_vars[],
sha256

text begins MOCK
DISCLOSURE — NOT
APPROVED LEGAL COPY

Never copy real approved
copy

policy_bundle.bundle_i
d, version, signature,
expires_at,
mock_state_rules()

MOCK-STATE-ZZ

Every rule has
fictional: true

presentation_evidence

{offer_id,
disclosure_id,
version,
rendered_sha256,
locale, renderer_id,
[cropped at image bottom]


IMAGE 16 — 1000334906.jpg
-------------------------
sha256

policy_bundle.bundle_i
d, version, signature,
expires_at,
mock_state_rules()

MOCK-STATE-ZZ

Every rule has
fictional: true

presentation_evidence

{offer_id,
disclosure_id,
version,
rendered_sha256,
locale, renderer_id,
renderer_version,
placement_order[],
viewport_visible_ms,
a11y_checks[],
shown_at_utc}

acknowledgment

{ack_id, offer_id,
outcome
ACCEPTED/DECLINED/TIME
OUT/RENDER_FAILED,
affirmative_action:boo
lean, captured_at_utc}

agent.agent_id,
partner_id,
session_nonce

MOCK-AGT-###

audit_event

{event_id, prev_hash,
[cropped at image bottom]

Append-only


IMAGE 17 — 1000334907.jpg
-------------------------
audit_event

{event_id, prev_hash,
hash, event_type,
tracking_id,
correlation_id,
idempotency_key,
actor, reason_code,
ts_utc}

Append-only
JSONL/SQLite with a
hash chain

Consumer

consumer_ref = random
UUID only

No name, SSN, DOB,
score, account number or
PAN

D. Conflicts and review flags

1. Plan-name drift: FPRR vs FPRA vs FRRA vs FPRI vs EPP, and the EPNI title is changing. Legal/Marketing
review needed.

2. HA vs HS: HA has no legal copy and may use stale offerDB data. Don't treat either as the system of record
without owner confirmation.

3. HS fixed-pay (FPRR/FPRA) OFP language is marked "TBD" on the Promotion Types page.

4. WCAG 2.1 AA (the stated Bank standard) vs 2.2 AA (used in 2026 audits). Use 2.2 AA as the stricter choice
and confirm with the ADA lead.

5. The informational overview describes an initialize handshake, but the hackathon guide says no
handshake after 28 Jul 2026. Follow the guide for the build.

6. "VS Code 1.13 or newer" looks like a typo (possibly 1.103). Confirm with the hackathon leads.

7. The tutorial uses httpx verify=False and pip --trusted-host. Don't carry either into OfferProof. InfoSec
review is needed if they're required.

Describe what you want to know or do next


IMAGE 18 — 1000334908.jpg
-------------------------
[cropped continuation:]
review is needed if they're required.

8. Hazards in search results: real-looking MIDs and QA URLs (PromoLookup page) and a test-applicant record
with PII fields (an attachment). Don't mirror any of them. This is a data handling flag.

9. Real disclosure pages contain live APRs and approved copy. Paraphrasing them into mock text could look like
approved copy, so use obviously fictional text instead.

10. Any state-cap or jurisdiction logic is fictional and needs a Legal disclaimer.

E. Constraints for the build spec

1. Mock data only. No SYF prod or non-prod DBs, APIs or Apigee endpoints. Reject SSN, credit score, consumer-
report data, account/PAN/CVV, DOB and income at the schema level.

2. Use the MCP pattern from the hackathon guide: mcp==2.0.*, MCPServer, stdio, stateless tools, and persisted
state referenced by IDs.

3. Handlers stay thin, with service and mock repository layers behind them.

4. Deterministic policy-as-code. The LLM never decides eligibility or authorization.

5. Return protected disclosure segments word for word with a SHA-256 hash. Partners and agents may fill only
the allowed variables. Any mismatch in the rendered hash blocks authorization.

6. Authorization only proceeds if every check passes: valid, unexpired promo and disclosure versions; a valid
mock policy bundle; presentation evidence that matches the hash; and an affirmative acknowledgment where
required. Otherwise block with a stable reason code.

7. Log every attempt, including failures, as an append-only, hash-chained event with tracking and correlation IDs
and an idempotency key. No PII and no free text in logs.

8. Use the SYF style error envelope (code, message, trackingId, transient) with dotted offerproof.* codes.
Route on code only.

9. Treat partner and agent free text as untrusted. Accept only structured fields and ignore any instructions
embedded in them.

Describe what you want to know or do next


IMAGE 19 — 1000334909.jpg
-------------------------
[cropped continuation from item 6:]
mock policy bundle; presentation evidence that matches the hash; and an affirmative acknowledgment whe[cropped]
required. Otherwise block with a stable reason code.

7. Log every attempt, including failures, as an append-only, hash-chained event with tracking and correlation [cropped]
and an idempotency key. No PII and no free text in logs.

8. Use the SYF style error envelope (code, message, trackingId, transient) with dotted offerproof.* cod[cropped]
Route on code only.

9. Treat partner and agent free text as untrusted. Accept only structured fields and ignore any instructions
embedded in them.

10. Every mock APR, factor and state rule is labeled FICTIONAL and is not a legal conclusion.

11. Out of scope: interest accrual, deferred-interest retroactive calculation, payment allocation, minimum paymen[cropped]
credit decisions, and real payment authorization.

12. Secrets and URLs go in .env (git ignored) or the mcp.json env block. Commit only .env.example.

Master prompt for Codex

Describe what you want to know or do next

Auto

Uses AI. Verify results.
