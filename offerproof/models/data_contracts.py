"""Strict source-data schemas: approvals are data, never inferred from prose."""
from offerproof.models.contracts import BOOL, ID, TIME, HASH, JURISDICTION, SCHEMAS, array, integer, obj, string

NULLABLE_ID = {"anyOf": [ID, {"type": "null"}]}
NULLABLE_RATE = {"anyOf": [integer(0, 10000), {"type": "null"}]}
MARK = {"data_classification": string(enum=["SYNTHETIC_HACKATHON_DATA"]), "not_for_production": {"type": "boolean", "enum": [True]}}
APPROVAL = {**MARK, "id": ID, "version": ID, "effective_at": TIME, "expires_at": TIME, "review_at": TIME,
    "status": string(enum=["APPROVED_MOCK"]), "maker": ID, "checker": ID, "legal_approval_id": ID,
    "approved_at": TIME, "predecessor": NULLABLE_ID, "rollback_reference": NULLABLE_ID,
    "source_system": ID, "checksum": HASH}
FAMILIES = ["DEFERRED_INTEREST", "EQUAL_PAY_NO_INTEREST", "REDUCED_APR_FIXED_TERM", "CUSTOM_AMORTIZATION", "CASHBACK_REVOLVING", "STANDARD_REVOLVING"]
RECORDS = {
    "products": obj({**APPROVAL, "category": ID, "item_type": ID}),
    "merchants": obj({**APPROVAL, "program_ids": array(ID, 10, 1), "channels": array(ID, 10, 1), "location": ID}),
    "account-terms": obj({**APPROVAL, "program_id": ID, "currency": string(enum=["USD"]),
        "standard_apr_bps": integer(0, 10000), "apr_type": string(enum=["VARIABLE", "FIXED"]), "apr_source": ID, "account_scope": ID}),
    "policy-bundles": obj({**APPROVAL, "fictional": {"type": "boolean", "enum": [True]},
        "effective_terms": obj({"standard_apr_override_bps": NULLABLE_RATE}), "control_routes": array(ID, 20, 10), "explanation_code": ID}),
    "jurisdiction-profiles": obj({**APPROVAL, "policy_id": ID, "matches": obj({k: v for k, v in JURISDICTION["properties"].items() if k not in ("profile_id", "transaction_at")})}),
    "renderer-profiles": obj({**APPROVAL, "renderer_version": ID, "presentation_policy_id": ID, "presentation_policy_version": ID,
        "locales": array(ID, 10, 1), "channels": array(ID, 10, 1), "capabilities": array(ID, 10),
        "required_sections": array(ID, 10, 1), "prominence_checks": array(ID, 10, 1), "a11y_checks": array(ID, 10, 1), "minimum_visible_ms": integer(1, 60000)}),
    "disclosures": obj({**APPROVAL, "template_id": ID, "template_version": ID,
        "plan_type": string(enum=FAMILIES), "product_legal_type": ID, "locale": ID, "channel": ID,
        "template": string(8000), "allowed_vars": array(ID, 20, 1), "protected_segments": array(ID, 10, 1)}),
    "offers": obj({**APPROVAL, "name": string(100), "plan_type": string(enum=FAMILIES), "product_legal_type": ID,
        "minimum_cents": integer(), "maximum_cents": integer(1), "eligible_categories": array(ID, 20, 1),
        "excluded_item_types": array(ID, 20), "tax_eligible": BOOL, "shipping_eligible": BOOL,
        "eligibility_basis": string(enum=["ELIGIBLE_BALANCE_AFTER_APPLIED_TENDER"]),
        "allowed_applied_tender_types": array(string(enum=["GIFT_CARD"]), 1),
        "merchant_ids": array(ID, 20, 1), "program_ids": array(ID, 20, 1), "channels": array(ID, 10, 1),
        "account_scope": ID, "term_months": integer(0, 120), "promo_apr_bps": NULLABLE_RATE,
        "apr_source": string(enum=["ACCOUNT_TERMS", "OFFER"]), "allow_partial_financing": BOOL, "allow_mixed_tender": BOOL,
        "allow_multi_promo": BOOL, "reward_stacking": string(enum=["NONE"]), "terms_id": ID, "terms_version": ID,
        "disclosure_id": ID, "disclosure_version": ID, "template_id": ID, "template_version": ID,
        "regulatory_profile": ID, "policy_bundle_ids": array(ID, 10, 1), "jurisdiction_profile_ids": array(ID, 10, 1),
        "presentation_policy_id": ID, "presentation_policy_version": ID, "acknowledgment_required": BOOL,
        "custom_schedule_bps": array(integer(0, 10000), 120), "reward": {"anyOf": [obj({"rate_bps": integer(0, 10000),
            "cap_cents": integer(), "vesting_days": integer(0, 365), "reversal": string(enum=["ON_RETURN"])}), {"type": "null"}]}}),
    "reason-codes": obj({"id": ID, "version": ID, "message": string(500), "recovery": ID}),
    "test-carts": obj({"id": ID, "request": SCHEMAS["start_offer_journey"]}),
}


def document_schema(name):
    return obj({**MARK, "schema_version": string(enum=["1"]), "records": array(RECORDS[name], 100, 1)})
