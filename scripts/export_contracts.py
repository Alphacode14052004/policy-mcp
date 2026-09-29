"""Export reviewable schema artifacts and a field-complete fixture dictionary."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from offerproof.config import ROOT
from offerproof.models.contracts import ENVELOPE, SCHEMAS
from offerproof.models.data_contracts import document_schema
from offerproof.repositories.json_repository import FILES

directory = ROOT / "docs/schemas"
directory.mkdir(parents=True, exist_ok=True)
for name, schema in {**SCHEMAS, "response-envelope": ENVELOPE, **{f"data-{name}": document_schema(name) for name in FILES}}.items():
    (directory / f"{name}.json").write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}, indent=2) + "\n", encoding="utf-8")

OWNERS = {"products": "Mock product registry", "merchants": "Mock partner registry", "offers": "Mock product policy publisher",
    "disclosures": "Mock Legal/Compliance copy publisher", "policy-bundles": "Mock Legal/Compliance policy publisher",
    "jurisdiction-profiles": "Mock authoritative jurisdiction router", "account-terms": "Mock terms registry",
    "renderer-profiles": "Mock presentation policy publisher", "reason-codes": "OfferProof contract owner", "test-carts": "Demo/test fixture owner"}
MEANING = {
    "data_classification": "Always SYNTHETIC_HACKATHON_DATA.", "not_for_production": "Always true.", "schema_version": "Version of the source-document schema.",
    "id": "Immutable identifier within this collection.", "version": "Published record or catalog version.",
    "effective_at": "Inclusive UTC validity start.", "expires_at": "Exclusive UTC validity end.", "review_at": "Required review deadline; record is blocked at/after this time.",
    "status": "Only APPROVED_MOCK is executable; not a real approval.", "maker": "Synthetic publishing actor.", "checker": "Distinct synthetic review actor.",
    "legal_approval_id": "Mock approval reference.", "approved_at": "Mock approval UTC timestamp, no later than effective start.",
    "predecessor": "Prior version reference or null for initial version.", "rollback_reference": "Rollback reference or null; current data still needs fresh evidence.",
    "source_system": "Fictional authoritative registry label.", "checksum": "SHA-256 of canonical record excluding checksum.",
    "minimum_cents": "Eligibility threshold, never a cap on the amount financed.", "maximum_cents": "Maximum eligible subtotal.",
    "term_months": "Configured term; zero means no revolving payoff schedule.", "promo_apr_bps": "Fictional promotional basis points, or null where not a true promotional APR.",
    "standard_apr_bps": "Fictional standard account APR in basis points.", "standard_apr_override_bps": "Fictional approved-profile override; null uses account terms.",
    "template": "Protected synthetic copy; only declared named placeholders may be filled.", "allowed_vars": "Complete whitelist of approved interpolation names.",
    "matches": "All context fields must match; no billing-state-only inference.", "custom_schedule_bps": "Configured shares of principal, sum 10000; final installment absorbs cent rounding.",
    "reward": "Separate reward dimension; never an interest-rate or payoff claim.", "required_sections": "Required visible section names in exact presentation order.",
    "capabilities": "Renderer capabilities required before disclosure issuance.", "minimum_visible_ms": "Minimum claimed visibility duration for mock attestation.",
    "request": "Exact synthetic start request; strict input schema applies.", "unit_price_cents": "Integer unit price; multiplied by quantity.",
    "total_cents": "Gross purchase total: line extensions + tax + shipping, before applied payment.", "transaction_at": "Synthetic scenario transaction date; policy must be effective on it.",
    "eligibility_basis": "Explicit fictional threshold basis: eligible balance after applied tender, not a real merchant rule.",
    "allowed_applied_tender_types": "Existing payment types allowed by this mock offer; empty rejects all applied tender.",
    "applied_tenders": "Existing mock gift-card payments, distinct from gift cards being purchased; no redemption occurs.",
    "tender_id": "Opaque MOCK- payment reference, never a real gift-card number.", "tender_type": "Only GIFT_CARD is supported in this synthetic payment model.",
    "amount_cents": "Positive mock payment or line allocation amount in integer cents.",
    "line_allocations": "Exact allocation to GOODS lines; sum equals tender amount, cumulative payment cannot exceed each line total.",
    "tax_eligible": "Whether tax contributes to this offer's eligible subtotal.", "shipping_eligible": "Whether shipping contributes to eligible subtotal.",
    "allow_partial_financing": "Allows financing eligible subset only.", "allow_mixed_tender": "Allows confirmed separate handling of excluded balance and configured applied payment types.",
    "allow_multi_promo": "False: multiple promotion allocation is not implemented.", "reward_stacking": "NONE: rewards and promotions are not stacked.",
    "message": "Sanitized developer-facing explanation, not consumer legal copy.", "recovery": "One terminal/operator recovery action for this stable reason code.",
}


def walk(value, path="", collected=None):
    collected = {} if collected is None else collected
    if isinstance(value, dict):
        for key, item in value.items():
            field = f"{path}.{key}" if path else key
            kind = "object" if isinstance(item, dict) else "array" if isinstance(item, list) else "boolean" if isinstance(item, bool) else "integer" if isinstance(item, int) else "null" if item is None else "string"
            example = json.dumps(item, ensure_ascii=False) if kind not in ("object", "array") else ("[]" if item == [] else "See child fields / source JSON")
            if len(example) > 90:
                example = example[:87] + "..."
            if field not in collected or collected[field][0] == "null":
                collected[field] = (kind, example, MEANING.get(key, "Configured synthetic " + key.replace("_", " ") + "; see exact schema and source values."))
            walk(item, field, collected)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                walk(item, path + "[]", collected)
    return collected


lines = ["# Mock data dictionary", "", "Generated by `scripts/export_contracts.py` from every mock JSON record. Exact strict schemas are in `docs/schemas/data-*.json`. All values and ownership labels are fictional; no real accountable owner is asserted.", "",
    "Money uses integer cents, rates use basis points (100 = 1%), timestamps are UTC, records use immutable IDs and explicit versions. Every document is classified SYNTHETIC_HACKATHON_DATA and not_for_production. Protected records carry checksums and approval metadata; reason/test catalogs are non-policy reference data.", "",
    "The canonical $200 DI value is a minimum eligibility threshold; the appliance finances $700. A purchased $100 gift card is excluded and needs separate tender. The sofa fixture instead uses an existing $100 gift card as mock payment on a $750 purchase, leaving $650 eligible. Thresholds explicitly use eligible balance after payment. Tax/shipping are excluded. No real redemption occurs and no value describes real Synchrony terms.", ""]
for name in FILES:
    document = json.loads((ROOT / "mock-data" / f"{name}.json").read_text(encoding="utf-8"))
    lines.extend([f"## {name}.json", "", "Mock owner: " + OWNERS[name] + ".", "", "| Field | Type | Example | Meaning |", "|---|---|---|---|"])
    for field, (kind, example, meaning) in walk(document).items():
        lines.append(f"| `{field}` | {kind} | `{example.replace('|', '/').replace('`', '')}` | {meaning} |")
    lines.append("")
(ROOT / "docs/MOCK_DATA_DICTIONARY.md").write_text("\n".join(lines), encoding="utf-8")
print("Exported strict schemas and complete mock field dictionary.")
