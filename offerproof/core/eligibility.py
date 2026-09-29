from offerproof.models.contracts import Block
from offerproof.security.digests import normalized_cart


def product_catalog(repo):
    return [{"sku": p["id"], "category": p["category"], "item_type": p["item_type"]}
            for p in repo.all("products")]


def tender_totals(cart):
    by_line = {line["line_id"]: 0 for line in cart["lines"]}
    for tender in cart.get("applied_tenders", []):
        for allocation in tender["line_allocations"]:
            by_line[allocation["line_id"]] += allocation["amount_cents"]
    return by_line, sum(t["amount_cents"] for t in cart.get("applied_tenders", []))


def cart_summary(cart):
    _, applied = tender_totals(cart)
    return {"cart_total_cents": cart["total_cents"], "applied_tender_cents": applied,
        "remaining_balance_cents": cart["total_cents"] - applied,
        "gift_card_purchase_cents": sum(line["unit_price_cents"] * line["quantity"]
            for line in cart["lines"] if line["item_type"] == "GIFT_CARD"),
        "applied_tenders_are_mock": True}


def allocation_reconciles(allocation, cart):
    _, applied = tender_totals(cart)
    return (allocation.get("applied_tender_cents", 0) == applied
            and not allocation.get("applied_tender_confirmation_required", False)
            and allocation["financed_cents"] + allocation["excluded_cents"] + applied == cart["total_cents"])


def validate_cart(cart, repo):
    if cart["currency"] != "USD":
        raise Block("UNSUPPORTED_CURRENCY")
    if len({line["line_id"] for line in cart["lines"]}) != len(cart["lines"]):
        raise Block("SCHEMA_VALIDATION_FAILED")
    total = cart["tax_cents"] + cart["shipping_cents"]
    for line in cart["lines"]:
        try:
            product = repo.get("products", line["sku"])
        except Block:
            raise Block("PRODUCT_NOT_CONFIGURED", result={"supported_products": product_catalog(repo),
                "instruction": "Use an exact configured SKU/category pair for the actual product, or request a mock catalog extension. Never substitute an unrelated product."}) from None
        product = repo.active(product)
        if line["category"] != product["category"] or line["item_type"] != product["item_type"]:
            raise Block("SCHEMA_VALIDATION_FAILED")
        total += line["unit_price_cents"] * line["quantity"]
    if total != cart["total_cents"]:
        raise Block("SCHEMA_VALIDATION_FAILED")
    tenders = cart.get("applied_tenders", [])
    if len({t["tender_id"] for t in tenders}) != len(tenders):
        raise Block("TENDER_ALLOCATION_INVALID")
    lines = {line["line_id"]: line for line in cart["lines"]}
    for tender in tenders:
        allocations = tender["line_allocations"]
        if len({a["line_id"] for a in allocations}) != len(allocations) or sum(a["amount_cents"] for a in allocations) != tender["amount_cents"]:
            raise Block("TENDER_ALLOCATION_INVALID")
        for allocation in allocations:
            target = lines.get(allocation["line_id"])
            if target is None or target["item_type"] != "GOODS":
                raise Block("TENDER_ALLOCATION_INVALID")
    by_line, applied = tender_totals(cart)
    if applied > total or any(by_line[line["line_id"]] > line["unit_price_cents"] * line["quantity"] for line in cart["lines"]):
        raise Block("TENDER_ALLOCATION_INVALID")
    return normalized_cart(cart)


def evaluate(cart, context, terms, policy, repo):
    results = []
    applied_by_line, applied_total = tender_totals(cart)
    for offer in repo.all("offers"):
        eligible, excluded = [], []
        for line in cart["lines"]:
            gross = line["unit_price_cents"] * line["quantity"]
            entry = {"line_id": line["line_id"], "gross_amount_cents": gross,
                     "applied_tender_cents": applied_by_line[line["line_id"]],
                     "amount_cents": gross - applied_by_line[line["line_id"]]}
            if line["category"] in offer["eligible_categories"] and line["item_type"] not in offer["excluded_item_types"]:
                eligible.append(entry)
            else:
                excluded.append({**entry, "reason_code": "ITEM_TYPE_EXCLUDED"})
        subtotal = sum(line["amount_cents"] for line in eligible)
        subtotal += cart["tax_cents"] if offer["tax_eligible"] else 0
        subtotal += cart["shipping_cents"] if offer["shipping_eligible"] else 0
        gross_eligible = sum(line["gross_amount_cents"] for line in eligible)
        gross_eligible += cart["tax_cents"] if offer["tax_eligible"] else 0
        gross_eligible += cart["shipping_cents"] if offer["shipping_eligible"] else 0
        excluded_cents = cart["total_cents"] - applied_total - subtotal
        reasons = []
        if any(t["tender_type"] not in offer["allowed_applied_tender_types"] for t in cart.get("applied_tenders", [])) or (applied_total and not offer["allow_mixed_tender"]):
            reasons.append("TENDER_POLICY_UNSUPPORTED")
        if subtotal < offer["minimum_cents"]:
            reasons.append("ELIGIBLE_SUBTOTAL_BELOW_MINIMUM")
        if subtotal > offer["maximum_cents"]:
            reasons.append("ELIGIBLE_SUBTOTAL_ABOVE_MAXIMUM")
        if (context["merchant_id"] not in offer["merchant_ids"] or context["program_id"] not in offer["program_ids"]
                or context["channel"] not in offer["channels"] or terms["account_scope"] != offer["account_scope"]
                or context["account_terms_id"] != offer["terms_id"]
                or context["jurisdiction"]["profile_id"] not in offer["jurisdiction_profile_ids"]
                or policy["policy_id"] not in offer["policy_bundle_ids"]
                or context["jurisdiction"]["product_legal_type"] != offer["product_legal_type"]):
            reasons.append("OFFER_SCOPE_MISMATCH")
        try:
            repo.active(offer, "OFFER_EXPIRED")
        except Block:
            reasons.append("OFFER_EXPIRED")
        if excluded_cents and not (offer["allow_partial_financing"] and offer["allow_mixed_tender"]):
            reasons.append("ITEM_TYPE_EXCLUDED")
        results.append({"offer_id": offer["id"], "name": offer["name"], "plan_type": offer["plan_type"],
            "eligible": not reasons, "reason_codes": reasons, "minimum_eligible_cents": offer["minimum_cents"],
            "eligibility_basis": offer["eligibility_basis"], "gross_eligible_subtotal_cents": gross_eligible,
            "applied_tender_cents": applied_total, "applied_tender_to_eligible_cents": gross_eligible - subtotal,
            "eligible_subtotal_cents": subtotal, "excluded_cents": excluded_cents,
            "eligible_lines": eligible, "excluded_lines": excluded,
            "allocation": {"financed_cents": subtotal, "excluded_cents": excluded_cents,
                           "applied_tender_cents": applied_total, "applied_tenders": cart.get("applied_tenders", []),
                           "applied_tender_confirmation_required": bool(applied_total),
                           "excluded_disposition": "SEPARATE_TENDER_OR_STANDARD_REVOLVING" if excluded_cents else "NONE",
                           "confirmation_required": bool(excluded_cents)} if not reasons else None})
    return results
