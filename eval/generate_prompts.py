"""Generate a 200-case cold-start evaluation corpus, not execution evidence."""
import json
from pathlib import Path

verbs = ["Buy", "Help me purchase", "Compare ways to pay for", "Find financing for", "Can I finance", "Evaluate payment options for", "Walk me through buying", "Check offers for", "Explain the plans for", "Choose a suitable option for"]
preferences = ["I want to avoid surprise interest and stay near $120 per month.",
    "My monthly target is $120. Explain any deadline risk.", "I have no payment preference yet.",
    "I care more about rewards than monthly payments.", "I plan to repay within six months."]
styles = ["Use the attached synthetic cart.", "Please show all options, including why some fail.",
          "Don't assume the cart total equals the financed subtotal.", "Ask me before recording any acknowledgment."]
target = Path(__file__).resolve().parent / "natural-prompts.jsonl"
with target.open("w", encoding="utf-8") as stream:
    index = 0
    for verb in verbs:
        for preference in preferences:
            for style in styles:
                index += 1
                stream.write(json.dumps({"case_id": f"NL-{index:03}", "prompt": f"{verb} this $700 appliance and $100 gift card using the Synchrony option. {preference} {style}",
                    "cart_fixture": "demo-data/mixed-cart.json", "expected_first_tool": "start_offer_journey",
                    "execution_status": "NOT_RUN"}) + "\n")
print(f"Generated {index} prompts; none executed.")
