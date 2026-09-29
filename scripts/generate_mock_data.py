"""Rebuild fictional, versioned fixtures. Never run against production sources."""
import json
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from offerproof.config import ROOT
from offerproof.security.digests import digest

MARK = {"data_classification": "SYNTHETIC_HACKATHON_DATA", "not_for_production": True}
START, END = "2026-01-01T00:00:00Z", "2030-01-01T00:00:00Z"


def approved(record):
    value = {**MARK, "version": "1.0.0", "effective_at": START, "expires_at": END,
        "review_at": "2029-12-01T00:00:00Z", "status": "APPROVED_MOCK",
        "maker": "MOCK-MAKER", "checker": "MOCK-CHECKER", "legal_approval_id": "MOCK-APPROVAL-001",
        "approved_at": START, "predecessor": None, "rollback_reference": None,
        "source_system": "MOCK-AUTHORITATIVE-REGISTRY", **record}
    value["checksum"] = digest(value)
    return value


def write(name, records):
    path = ROOT / "mock-data" / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({**MARK, "schema_version": "1", "records": records}, indent=2) + "\n", encoding="utf-8")


def main():
    products = [approved({"id": sku, "category": category, "item_type": kind}) for sku, category, kind in [
        ("MOCK-SKU-APPLIANCE", "APPLIANCE", "GOODS"),
        ("MOCK-SKU-SOFA", "SOFA", "GOODS"),
        ("MOCK-SKU-GIFT", "GIFT_CARD", "GIFT_CARD"),
        ("MOCK-SKU-SERVICE", "SERVICE", "SERVICE")]]
    write("products", products)
    write("merchants", [approved({"id": "MOCK-MER-0001", "program_ids": ["MOCK-PRG-HOM"],
        "channels": ["ONLINE_AGENT"], "location": "MOCK-LOCATION-A"})])
    write("account-terms", [approved({"id": "MOCK-TERMS-001", "program_id": "MOCK-PRG-HOM",
        "currency": "USD", "standard_apr_bps": 2345, "apr_type": "VARIABLE",
        "apr_source": "MOCK-TERMS-001", "account_scope": "MOCK_EXISTING_ACCOUNT"})])
    controls = ["REG_Z_REVIEW", "DEFERRED_INTEREST_SERVICING_BOUNDARY", "UDAAP_WORDING", "REG_B_NOTICE_ROUTING",
        "FCRA_REPORT_BOUNDARY", "MLA_SCRA_ROUTING", "STATE_PREEMPTION_REVIEW", "ESIGN_PRESENTATION",
        "GLBA_MINIMIZATION", "ACCESSIBILITY_LANGUAGE"]
    write("policy-bundles", [approved({"id": ident, "fictional": True,
        "effective_terms": {"standard_apr_override_bps": rate}, "control_routes": controls,
        "explanation_code": "MOCK_POLICY_APPLIED"}) for ident, rate in [
            ("MOCK_DEFAULT", None), ("MOCK_STATE_CAP", 1234)]])
    matches = {"issuer_charter": "MOCK_FEDERAL_SAVINGS_BANK", "issuer_location": "MOCK-ISSUER-A",
        "product_legal_type": "OPEN_END_REVOLVING", "account_program": "MOCK-PRG-HOM",
        "origination_channel": "ONLINE_AGENT", "merchant_location": "MOCK-LOCATION-A",
        "consumer_residence_state": "MOCK-ZZ", "billing_state": "MOCK-ZZ",
        "servicemember_status_source": "MOCK-STATUS-REGISTRY", "servicemember_status_result": "MOCK_NOT_REFERRED"}
    write("jurisdiction-profiles", [approved({"id": profile, "policy_id": policy,
        "matches": {**matches, "consumer_residence_state": state, "billing_state": state}})
        for profile, policy, state in [("MOCK_PROFILE_DEFAULT", "MOCK_DEFAULT", "MOCK-ZZ"),
                                      ("MOCK_PROFILE_CAP", "MOCK_STATE_CAP", "MOCK-YY")]])
    write("renderer-profiles", [approved({"id": "MOCK-RENDERER-CHAT", "renderer_version": "1.0.0",
        "presentation_policy_id": "MOCK-PRESENTATION-001", "presentation_policy_version": "1.0.0",
        "locales": ["en-US"], "channels": ["ONLINE_AGENT"], "capabilities": ["EXACT_TEXT", "AFFIRMATIVE_CONSENT"],
        "required_sections": ["headline", "warning", "facts", "allocation", "terms"],
        "prominence_checks": ["READABLE", "EQUAL_PROMINENCE", "WARNING_VISIBLE"],
        "a11y_checks": ["KEYBOARD", "SCREEN_READER", "NO_COLOR_ONLY"], "minimum_visible_ms": 1000})])
    definitions = [
        ("DI-6M", "DEFERRED_INTEREST", 20000, 6, None,
         "No interest if paid in full within {term_months} months. If the promotional balance is not paid in full by {payoff_date}, interest will be charged from the purchase date at the standard purchase APR applicable to the account, currently {standard_apr}% {apr_type}. Minimum monthly payments are required and may not pay off the promotional balance by the deadline. Suggested payoff amount {monthly_payment}; this is not the account minimum payment."),
        ("EPP-12-0APR", "EQUAL_PAY_NO_INTEREST", 75000, 12, 0,
         "True 0% APR with {term_months} equal monthly payments, except final-payment rounding. Scheduled payment {monthly_payment}; final payment {final_payment}. Total payments {total_payments}. No interest on this configured promotional purchase. Regular account terms apply to other purchases."),
        ("REDUCED-12", "REDUCED_APR_FIXED_TERM", 90000, 12, 789,
         "Fixed promotional APR {promo_apr}% for {term_months} months. Estimated monthly payment {monthly_payment}; final payment {final_payment}; estimated total payments {total_payments} including estimated finance cost {finance_cost}. Subsequent purchases use standard APR {standard_apr}% {apr_type}."),
        ("CUSTOM-4", "CUSTOM_AMORTIZATION", 100000, 4, 0,
         "Product-specific mock custom schedule: {schedule}. Configured no-interest schedule totals {total_payments}. Standard APR {standard_apr}% {apr_type} applies to other purchases. No schedule may be inferred from customer text."),
        ("CASHBACK-REV", "CASHBACK_REVOLVING", 100000, 0, None,
         "Cashback is a reward, not interest-free financing. Standard purchase APR {standard_apr}% {apr_type}. Mock {reward_rate_percent}% reward on eligible goods, capped at {reward_cap}, vests {reward_vesting_days} days after purchase, excludes gift cards, reverses on return, and cannot be stacked with promotions. Rewards do not reduce disclosed borrowing costs."),
        ("STANDARD-REV", "STANDARD_REVOLVING", 1, 0, None,
         "Standard revolving fallback. Standard purchase APR {standard_apr}% {apr_type} from {apr_source}. No promotional financing or payoff schedule is represented. Regular account terms apply; this is not a credit decision."),
    ]
    import string
    offers, disclosures = [], []
    for ident, family, minimum, term, apr, template in definitions:
        template = "MOCK DISCLOSURE — NOT APPROVED LEGAL COPY.\n" + template + "\nPurchase total before payment {cart_total}. Existing mock gift-card payment {applied_tender_amount}; no actual redemption is performed. Financed eligible amount {eligible_amount}. Excluded balance {excluded_amount}: {excluded_disposition}. Mock policy applied: {policy_id}."
        disclosure_id = f"MOCK-DISC-{ident}"
        disclosures.append(approved({"id": disclosure_id, "version": "1.1.0", "predecessor": f"{disclosure_id}:1.0.0", "template_id": f"MOCK-TPL-{ident}",
            "template_version": "1.1.0", "plan_type": family, "product_legal_type": "OPEN_END_REVOLVING",
            "locale": "en-US", "channel": "ONLINE_AGENT", "template": template,
            "allowed_vars": sorted({field for _, field, _, _ in string.Formatter().parse(template) if field}),
            "protected_segments": ["headline", "warning", "facts", "allocation", "terms"]}))
        offers.append(approved({"id": ident, "version": "1.1.0", "predecessor": f"{ident}:1.0.0", "name": f"Mock {ident}", "plan_type": family,
            "product_legal_type": "OPEN_END_REVOLVING", "minimum_cents": minimum,
            "maximum_cents": 2000000, "eligible_categories": ["APPLIANCE", "SOFA"],
            "eligibility_basis": "ELIGIBLE_BALANCE_AFTER_APPLIED_TENDER", "allowed_applied_tender_types": ["GIFT_CARD"],
            "excluded_item_types": ["GIFT_CARD", "SERVICE"], "tax_eligible": False, "shipping_eligible": False,
            "merchant_ids": ["MOCK-MER-0001"], "program_ids": ["MOCK-PRG-HOM"], "channels": ["ONLINE_AGENT"],
            "account_scope": "MOCK_EXISTING_ACCOUNT", "term_months": term, "promo_apr_bps": apr,
            "apr_source": "ACCOUNT_TERMS" if apr is None else "OFFER", "allow_partial_financing": True,
            "allow_mixed_tender": True, "allow_multi_promo": False, "reward_stacking": "NONE",
            "terms_id": "MOCK-TERMS-001", "terms_version": "1.0.0",
            "disclosure_id": disclosure_id, "disclosure_version": "1.1.0",
            "template_id": f"MOCK-TPL-{ident}", "template_version": "1.1.0",
            "regulatory_profile": "MOCK-REGULATORY-001", "policy_bundle_ids": ["MOCK_DEFAULT", "MOCK_STATE_CAP"],
            "jurisdiction_profile_ids": ["MOCK_PROFILE_DEFAULT", "MOCK_PROFILE_CAP"],
            "presentation_policy_id": "MOCK-PRESENTATION-001", "presentation_policy_version": "1.0.0",
            "acknowledgment_required": True, "custom_schedule_bps": [4000, 3000, 2000, 1000] if family == "CUSTOM_AMORTIZATION" else [],
            "reward": {"rate_bps": 100, "cap_cents": 2000, "vesting_days": 30, "reversal": "ON_RETURN"} if family == "CASHBACK_REVOLVING" else None}))
    write("offers", offers)
    write("disclosures", disclosures)
    codes = {
        "OK": ("Request completed using synthetic data.", "FOLLOW_WORKFLOW"),
        "PRODUCT_NOT_CONFIGURED": ("The submitted SKU is not in the mock product catalog; this is not a jurisdiction-policy decision.", "REQUEST_MOCK_CATALOG_UPDATE"),
        "TENDER_ALLOCATION_INVALID": ("Applied payment must reference purchase lines, reconcile exactly, and not exceed their amounts. A gift card being purchased is not a payment.", "CORRECT_APPLIED_TENDER_ALLOCATION"),
        "TENDER_POLICY_UNSUPPORTED": ("The selected mock offer does not support this applied payment type.", "SELECT_SUPPORTED_PAYMENT_ARRANGEMENT"),
        "APPLIED_TENDER_CONFIRMATION_REQUIRED": ("Ask the consumer to confirm the exact existing gift-card amount to apply as payment.", "CONFIRM_APPLIED_TENDER"),
        "ELIGIBLE_SUBTOTAL_BELOW_MINIMUM": ("Eligible subtotal is below this offer's minimum.", "SELECT_ELIGIBLE_OFFER"),
        "ITEM_TYPE_EXCLUDED": ("This line item is excluded from promotional financing.", "CONFIRM_ALLOCATION"),
        "OFFER_EXPIRED": ("The selected offer is outside its effective window.", "START_NEW_JOURNEY"),
        "OFFER_SCOPE_MISMATCH": ("The offer does not match the configured scope.", "SELECT_ELIGIBLE_OFFER"),
        "ELIGIBLE_SUBTOTAL_ABOVE_MAXIMUM": ("Eligible subtotal exceeds this offer's maximum.", "SELECT_ELIGIBLE_OFFER"),
        "NO_ELIGIBLE_PROMOTION": ("No promotional offer qualifies; review the standard revolving fallback.", "REVIEW_STANDARD_FALLBACK"),
        "ALLOCATION_CONFIRMATION_REQUIRED": ("Ask the consumer to confirm the excluded balance disposition.", "CONFIRM_ALLOCATION"),
        "POLICY_REVIEW_REQUIRED": ("Approved mock policy cannot be resolved for this context.", "REQUEST_AUTHORITATIVE_POLICY_REVIEW"),
        "TERMS_VERSION_CHANGED": ("Account terms changed; previous evidence is invalid.", "PREPARE_DISCLOSURE_AGAIN"),
        "POLICY_VERSION_CHANGED": ("Policy changed; previous evidence is invalid.", "PREPARE_DISCLOSURE_AGAIN"),
        "OFFER_VERSION_CHANGED": ("Offer configuration changed; reevaluate the cart.", "START_NEW_JOURNEY"),
        "CART_DIGEST_MISMATCH": ("The cart changed; previous evidence is invalid.", "START_NEW_JOURNEY"),
        "DISCLOSURE_DIGEST_MISMATCH": ("Protected disclosure text or version does not match.", "PREPARE_DISCLOSURE_AGAIN"),
        "DISCLOSURE_NOT_PRESENTED": ("Disclosure delivery does not establish presentation.", "PRESENT_DISCLOSURE"),
        "ACKNOWLEDGMENT_REQUIRED": ("Capture an affirmative consumer acknowledgment after presentation.", "CAPTURE_ACKNOWLEDGMENT"),
        "PRESENTATION_CAPABILITY_UNSUPPORTED": ("Renderer does not support the required presentation policy.", "USE_SUPPORTED_RENDERER"),
        "PRESENTATION_EVIDENCE_INVALID": ("Presentation attestation failed required checks.", "PRESENT_DISCLOSURE_AGAIN"),
        "INVALID_STATE_TRANSITION": ("This action cannot advance the current journey state.", "RECOVER_JOURNEY_STATUS"),
        "STALE_JOURNEY_VERSION": ("Another request advanced this journey.", "RECOVER_JOURNEY_STATUS"),
        "RECEIPT_INVALID": ("Receipt verification failed.", "RECOVER_JOURNEY_STATUS"),
        "RECEIPT_EXPIRED": ("The evidence receipt expired; collect new evidence.", "PREPARE_DISCLOSURE_AGAIN"),
        "IDENTITY_BINDING_MISMATCH": ("Caller identity does not match the journey.", "USE_BOUND_IDENTITY"),
        "IDEMPOTENCY_CONFLICT": ("This idempotency key belongs to a different request.", "USE_NEW_IDEMPOTENCY_KEY"),
        "AUDIT_UNAVAILABLE": ("Evidence cannot be persisted; this action is blocked.", "RESTORE_AUDIT_AND_RETRY"),
        "UNSUPPORTED_CURRENCY": ("Only the configured synthetic USD currency is supported.", "SUPPLY_SUPPORTED_CURRENCY"),
        "UNSUPPORTED_LOCALE": ("This renderer has no approved disclosure in that locale.", "REQUEST_SUPPORTED_LOCALE_JOURNEY"),
        "PROHIBITED_SENSITIVE_DATA": ("Sensitive customer or account data is prohibited.", "REMOVE_SENSITIVE_DATA"),
        "AUTHORITATIVE_NOTICE_FLOW_REQUIRED": ("No credit decision was made. Use the authoritative notice process; do not generate an adverse-action notice.", "ROUTE_TO_AUTHORITATIVE_NOTICE_FLOW"),
        "SCHEMA_VALIDATION_FAILED": ("Request does not match the strict synthetic tool schema.", "CORRECT_REQUEST_SCHEMA"),
        "INTERNAL_ERROR": ("The request could not be processed safely.", "CONTACT_DEMO_OPERATOR"),
        "DECLINED": ("Consumer declined. This journey is closed.", "END_DECLINED"),
        "EXPIRED": ("The journey expired. Its evidence cannot be used.", "START_NEW_JOURNEY"),
    }
    write("reason-codes", [{"id": code, "version": "1", "message": message, "recovery": recovery} for code, (message, recovery) in codes.items()])
    cart = {"cart_id": "MOCK-CART-001", "currency": "USD", "lines": [
        {"line_id": "line-appliance", "sku": "MOCK-SKU-APPLIANCE", "category": "APPLIANCE", "item_type": "GOODS", "quantity": 1, "unit_price_cents": 70000},
        {"line_id": "line-gift", "sku": "MOCK-SKU-GIFT", "category": "GIFT_CARD", "item_type": "GIFT_CARD", "quantity": 1, "unit_price_cents": 10000}], "tax_cents": 0, "shipping_cents": 0, "total_cents": 80000}
    request = {"cart": cart, "merchant_id": "MOCK-MER-0001", "agent_id": "MOCK-AGT-001", "program_id": "MOCK-PRG-HOM",
        "channel": "ONLINE_AGENT", "renderer_id": "MOCK-RENDERER-CHAT", "locale": "en-US", "account_terms_id": "MOCK-TERMS-001",
        "jurisdiction": {"profile_id": "MOCK_PROFILE_DEFAULT", **matches, "transaction_at": "2026-09-29T12:00:00Z"},
        "preferences": {"avoid_surprise_interest": True, "target_monthly_cents": 12000},
        "idempotency_key": "demo-start-001", "request_id": "demo-request-001", "correlation_id": "demo-correlation-001"}
    sofa = copy.deepcopy(request)
    sofa.update(idempotency_key="sofa-redemption-start-v2", request_id="sofa-redemption-request-v2", correlation_id="sofa-redemption-correlation-v2")
    sofa["cart"] = {"cart_id": "MOCK-CART-SOFA-REDEMPTION", "currency": "USD", "lines": [
        {"line_id": "line-sofa", "sku": "MOCK-SKU-SOFA", "category": "SOFA", "item_type": "GOODS", "quantity": 1, "unit_price_cents": 75000}],
        "tax_cents": 0, "shipping_cents": 0, "total_cents": 75000,
        "applied_tenders": [{"tender_id": "MOCK-GIFT-PAYMENT-001", "tender_type": "GIFT_CARD", "amount_cents": 10000,
            "line_allocations": [{"line_id": "line-sofa", "amount_cents": 10000}]}]}
    write("test-carts", [{"id": "MOCK-CASE-MIXED", "request": request}, {"id": "MOCK-CASE-SOFA-REDEMPTION", "request": sofa}])
    (ROOT / "demo-data").mkdir(exist_ok=True)
    (ROOT / "demo-data" / "mixed-cart.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    (ROOT / "demo-data" / "sofa-gift-card-redemption.json").write_text(json.dumps(sofa, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
