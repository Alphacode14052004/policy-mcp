import copy
from datetime import timedelta
from decimal import Decimal
from offerproof.config import SYNTHETIC
from offerproof.core.calculations import add_months, dollars, schedule
from offerproof.models.contracts import Block
from offerproof.security.digests import digest, instant, iso, text_digest

MAX_PRESENTATION_AGE_SECONDS = 900
TIMING_INSTRUCTION = (
    "Use actual UTC timestamps captured with renderer and consumer events. "
    "Display the final canonical text before capturing presentation. "
    "Server clock values and bounds are diagnostic, not events to copy. "
    "If the host cannot capture an event, report that limitation and do not submit guessed evidence.")


def presentation_timing(issued_at, now):
    return {"issued_at": issued_at, "server_time": iso(now),
        "earliest_acceptable_rendered_at": iso(max(instant(issued_at), now - timedelta(seconds=MAX_PRESENTATION_AGE_SECONDS))),
        "latest_acceptable_rendered_at": iso(now),
        "maximum_age_seconds": MAX_PRESENTATION_AGE_SECONDS,
        "bounds_evaluated_at_validation": True, "clock": "UTC", "instruction": TIMING_INSTRUCTION}


def presentation_failure(check, field, message, issued_at, now, *, received_at=None, extra=None):
    details = {"check": check, "field": field, "message": message,
        "timing": presentation_timing(issued_at, now)}
    if received_at is not None:
        details["received_at"] = received_at
    if extra:
        details.update(extra)
    raise Block("PRESENTATION_EVIDENCE_INVALID", result={"presentation_error": details})


def resolve_context(request, repo):
    from offerproof.core.policy_resolver import LegalPolicyResolver
    terms = repo.active(repo.get("account-terms", request["account_terms_id"]))
    merchant = repo.active(repo.get("merchants", request["merchant_id"]))
    if request["program_id"] not in merchant["program_ids"] or request["channel"] not in merchant["channels"]:
        raise Block("POLICY_REVIEW_REQUIRED")
    renderer = repo.active(repo.get("renderer-profiles", request["renderer_id"]), "PRESENTATION_CAPABILITY_UNSUPPORTED")
    if request["locale"] not in renderer["locales"]:
        raise Block("UNSUPPORTED_LOCALE")
    if (request["channel"] not in renderer["channels"] or not {"EXACT_TEXT", "AFFIRMATIVE_CONSENT"}.issubset(renderer["capabilities"])):
        raise Block("PRESENTATION_CAPABILITY_UNSUPPORTED")
    policy = LegalPolicyResolver(repo).resolve(request["jurisdiction"], terms, merchant=merchant,
                                               channel=request["channel"], program=request["program_id"])
    return terms, policy, renderer


def versions(request, offer, terms, policy, disclosure, renderer, repo):
    # Bind complete protected records as well as displayable versions. Even an
    # improperly republished edit retaining its version invalidates old evidence.
    records = {"offer": offer, "terms": terms, "policy": policy["bundle"], "profile": policy["profile"],
               "disclosure": disclosure, "renderer": renderer,
               "merchant": repo.get("merchants", request["merchant_id"]),
               "products": [repo.get("products", line["sku"]) for line in request["cart"]["lines"]]}
    return {key: digest(value) for key, value in records.items()}


def prepare(request, evaluation, offer, allocation, repo):
    terms, policy, renderer = resolve_context(request, repo)
    disclosure = repo.active(repo.get("disclosures", offer["disclosure_id"]))
    if disclosure["locale"] != request["locale"] or disclosure["channel"] != request["channel"]:
        raise Block("UNSUPPORTED_LOCALE")
    if (offer["presentation_policy_id"] != renderer["presentation_policy_id"] or
            offer["presentation_policy_version"] != renderer["presentation_policy_version"]):
        raise Block("PRESENTATION_CAPABILITY_UNSUPPORTED")
    cents = evaluation["eligible_subtotal_cents"]
    payments = schedule(cents, offer)
    amounts = payments["payments_cents"]
    standard = policy["effective_terms"]
    payoff = add_months(instant(request["jurisdiction"]["transaction_at"]), offer["term_months"])
    facts = {"eligible_amount_cents": cents, "excluded_amount_cents": evaluation["excluded_cents"],
        "cart_total_cents": request["cart"]["total_cents"], "applied_tender_cents": evaluation["applied_tender_cents"],
        "gross_eligible_subtotal_cents": evaluation["gross_eligible_subtotal_cents"], "eligibility_basis": offer["eligibility_basis"],
        "plan_name": offer["name"], "plan_type": offer["plan_type"], "term_months": offer["term_months"],
        "standard_apr_bps": standard["standard_apr_bps"], "promo_apr_bps": offer["promo_apr_bps"],
        "apr_type": standard["apr_type"], "apr_source": standard["apr_source"],
        "payoff_date": payoff.date().isoformat() if offer["term_months"] else None, **payments,
        "deferred_interest_risk": offer["plan_type"] == "DEFERRED_INTEREST", "reward": offer["reward"]}
    variables = {"term_months": offer["term_months"], "payoff_date": facts["payoff_date"],
        "standard_apr": f"{Decimal(standard['standard_apr_bps']) / 100:.2f}", "apr_type": standard["apr_type"].lower(),
        "promo_apr": f"{Decimal(offer['promo_apr_bps'] or 0) / 100:.2f}",
        "monthly_payment": dollars(amounts[0]) if amounts else "not estimated",
        "final_payment": dollars(amounts[-1]) if amounts else "not estimated",
        "total_payments": dollars(sum(amounts)) if amounts else "not estimated",
        "finance_cost": dollars(payments["finance_cost_cents"] or 0),
        "schedule": ", ".join(dollars(x) for x in amounts), "apr_source": standard["apr_source"],
        "eligible_amount": dollars(cents), "excluded_amount": dollars(evaluation["excluded_cents"]),
        "cart_total": dollars(request["cart"]["total_cents"]), "applied_tender_amount": dollars(evaluation["applied_tender_cents"]),
        "excluded_disposition": allocation["excluded_disposition"], "policy_id": policy["policy_id"],
        "reward_rate_percent": f"{Decimal((offer['reward'] or {}).get('rate_bps', 0)) / 100:.2f}",
        "reward_cap": dollars((offer["reward"] or {}).get("cap_cents", 0)),
        "reward_vesting_days": (offer["reward"] or {}).get("vesting_days", 0)}
    interpolation = {key: variables[key] for key in disclosure["allowed_vars"]}
    text = disclosure["template"].format(**interpolation)
    ids = {"offer_id": offer["id"], "offer_version": offer["version"], "terms_id": terms["id"], "terms_version": terms["version"],
        "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
        "legal_approval_id": policy["legal_approval_id"], "disclosure_legal_approval_id": disclosure["legal_approval_id"],
        "disclosure_id": disclosure["id"], "disclosure_version": disclosure["version"],
        "template_id": disclosure["template_id"], "template_version": disclosure["template_version"],
        "presentation_policy_id": renderer["presentation_policy_id"], "presentation_policy_version": renderer["presentation_policy_version"]}
    return {"canonical_text": text, "canonical_text_must_not_be_modified": True,
        "protected_segments": disclosure["protected_segments"], "facts": facts, "versions": ids,
        "disclosure_digest": text_digest(text), "cart_digest": digest(request["cart"]),
        "allocation": allocation, "eligible_lines": evaluation["eligible_lines"], "excluded_lines": evaluation["excluded_lines"],
        "interpolation_inputs": interpolation, "record_digests": versions(request, offer, terms, policy, disclosure, renderer, repo),
        "presentation_requirements": {"evidence_label": "MOCK_RENDERER_ATTESTATION",
            "renderer_id": renderer["id"], "renderer_version": renderer["renderer_version"],
            "locale": request["locale"], "channel": request["channel"], "required_sections": renderer["required_sections"],
            "placement_order": renderer["required_sections"], "prominence_checks": renderer["prominence_checks"],
            "a11y_checks": renderer["a11y_checks"], "minimum_visible_ms": renderer["minimum_visible_ms"],
            "acknowledgment_required": offer["acknowledgment_required"], "consent_preselected": False,
            "maximum_age_seconds": MAX_PRESENTATION_AGE_SECONDS, "timestamp_instruction": TIMING_INSTRUCTION},
        "valid_until": iso(min(map(instant, [offer["expires_at"], offer["review_at"], terms["expires_at"], terms["review_at"],
            policy["bundle"]["expires_at"], policy["bundle"]["review_at"], disclosure["expires_at"], disclosure["review_at"],
            renderer["expires_at"], renderer["review_at"]]))), "policy_label": "Mock policy applied", "warning": SYNTHETIC}


def preview(request, evaluation, offer, repo):
    """Render protected copy for comparison without issuance or consent side effects."""
    allocation = copy.deepcopy(evaluation["allocation"])
    pending = []
    if allocation["applied_tender_confirmation_required"]:
        pending.append("applied_tender_confirmation")
    if allocation["confirmation_required"]:
        pending.append("allocation_confirmation")
        # Only this disposition can complete in the mock checkout. Do not imply
        # either confirmation or a supported standard-revolving split.
        allocation["excluded_disposition"] = "separate tender, pending your confirmation"
    rendered = prepare(request, evaluation, offer, allocation, repo)
    payment_kind = rendered["facts"]["kind"]
    if payment_kind == "ILLUSTRATIVE_PAYOFF_NOT_MINIMUM":
        payment_explanation = ("Suggested payoff schedule, not the account minimum payment. "
            "The displayed total assumes payment in full by the promotional deadline; "
            "it excludes any deferred interest charged if that condition is not met.")
    elif payment_kind == "REVOLVING_NO_PAYOFF_ESTIMATE":
        payment_explanation = "Monthly payment, total borrowing cost and payoff date are not estimated. See the standard purchase APR and exact terms in the disclosure."
    else:
        payment_explanation = "Configured mock schedule estimate, including final-payment rounding. This does not calculate the account minimum payment."
    fields = ("canonical_text", "canonical_text_must_not_be_modified", "protected_segments", "facts", "versions",
        "disclosure_digest", "cart_digest", "allocation", "interpolation_inputs", "record_digests", "valid_until", "warning")
    return {**{key: rendered[key] for key in fields},
        "stage": "PRE_SELECTION_PREVIEW", "evaluated_at": iso(repo.clock()),
        "selection_is_acceptance": False, "is_final_disclosure": False,
        "pending_confirmations": pending, "payment_explanation": payment_explanation,
        "consumer_notice": "Read this disclosure before choosing an offer to review. "
            + ("Payment arrangements shown here still need your confirmation. " if pending else "")
            + "Selecting an offer does not accept its terms. A final disclosure and separate acknowledgment follow.",
        "display_instruction": "Show canonical_text verbatim and the full payment schedule before asking for an offer selection. Give the warnings equal prominence to the payment amount. Do not treat a preview as presented or acknowledged final disclosure."}


def verify_presentation(evidence, prepared, issued_at, now):
    requirements = prepared["presentation_requirements"]
    rendered = instant(evidence["rendered_at"])
    if rendered < instant(issued_at):
        presentation_failure("RENDERED_AT_BEFORE_ISSUANCE", "evidence.rendered_at",
            "The claimed display time is before final disclosure issuance. Display the issued copy and capture a new renderer event.",
            issued_at, now, received_at=evidence["rendered_at"])
    if rendered > now:
        presentation_failure("RENDERED_AT_IN_FUTURE", "evidence.rendered_at",
            "The claimed display time is later than server validation. Check the renderer clock and capture an actual display event; do not backdate it.",
            issued_at, now, received_at=evidence["rendered_at"])
    if (now - rendered).total_seconds() > MAX_PRESENTATION_AGE_SECONDS:
        presentation_failure("RENDERED_AT_TOO_OLD", "evidence.rendered_at",
            "The display event is older than the permitted 900 seconds. Display the current final disclosure again and capture a fresh event.",
            issued_at, now, received_at=evidence["rendered_at"])
    for field in ("locale", "channel", "renderer_version"):
        if evidence[field] != requirements[field]:
            presentation_failure("PRESENTATION_CONTEXT_MISMATCH", "evidence." + field,
                "The renderer event does not match the issued disclosure's presentation context.", issued_at, now)
    checks = {
        "protected_text_digest": evidence["protected_text_digest"] == prepared["disclosure_digest"],
        "placement_order": evidence["placement_order"] == requirements["placement_order"],
        "required_sections_shown": set(evidence["required_sections_shown"]) == set(requirements["required_sections"]),
        "prominence_checks": set(requirements["prominence_checks"]).issubset(evidence["prominence_checks"]),
        "a11y_checks": set(requirements["a11y_checks"]).issubset(evidence["a11y_checks"]),
        "visible_duration_ms": evidence["visible_duration_ms"] >= requirements["minimum_visible_ms"],
        "scroll_visibility_attested": evidence["scroll_visibility_attested"],
    }
    failed = [field for field, passed in checks.items() if not passed]
    if failed:
        presentation_failure("PRESENTATION_REQUIREMENTS_FAILED", "evidence",
            "The renderer evidence failed content or visibility checks. Correct the actual presentation and capture fresh evidence.",
            issued_at, now, extra={"failed_checks": failed})


def verify_acknowledgment_timing(acknowledgment, presentation, issued_at, now):
    captured = instant(acknowledgment["captured_at"])
    if captured < instant(presentation["rendered_at"]):
        presentation_failure("ACKNOWLEDGMENT_BEFORE_PRESENTATION", "acknowledgment.captured_at",
            "Acknowledgment must follow the accepted presentation. Capture a new affirmative consumer event; do not invent its time.",
            issued_at, now, received_at=acknowledgment["captured_at"], extra={"accepted_rendered_at": presentation["rendered_at"]})
    if captured > now:
        presentation_failure("ACKNOWLEDGMENT_IN_FUTURE", "acknowledgment.captured_at",
            "The claimed acknowledgment time is later than server validation. Check the capture clock and submit an actual consumer event.",
            issued_at, now, received_at=acknowledgment["captured_at"], extra={"accepted_rendered_at": presentation["rendered_at"]})
