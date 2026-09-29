
```text
Prepare OfferProof MCP for a five-minute SYF hackathon demo. Do not add new product scope unless needed to remove a demo blocker. Inspect the complete repository and run the canonical scenario from a clean runtime state.

The judge-facing prompt is: “Buy this $700 appliance and $100 gift card using the Synchrony option that best fits me. I want to avoid surprise interest and keep payments near $120 a month.” The cart comes from `demo-data/mixed-cart.json`. The prompt must not name tools.

Verify the demo visibly proves: zero-context tool discovery; $800 cart vs. $700 eligible-subtotal x-ray; EPP-12-0APR rejected at its $750 eligible minimum; DI-6M eligible for the $700 appliance; $100 gift card explicitly separated; exact “No interest if paid in full” warning; mock policy and disclosure versions; presentation/acknowledgment evidence; signed Offer Trust Passport; and a quick changed-cart replay that is blocked.

Tighten `docs/DEMO_RUNBOOK.md` to a timed five-minute flow. Include a 30-second problem statement, current-vs-new workflow, quantified metrics labeled as measured or target, 2.5–3 minute live demo, architecture proof, adversarial proof, and closing value. Map every rubric item to a visible sentence, screen, or test artifact. Prepare a structured fallback if the MCP App does not render. Resolve VS Code server trust/permission setup before the live run and provide a clean reset command.

Run the full tests and smoke script. If possible, run 20 consecutive rehearsals and report the actual success rate; otherwise state how many were run. End with a go/no-go checklist and the top three remaining demo risks.
```