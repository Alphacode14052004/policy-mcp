from offerproof.core.calculations import schedule


def recommend(evaluations, preferences, repo):
    if not preferences:
        return {"offer_id": None, "explanation": "Preferences are needed before recommending an offer.", "scores": []}
    scored = []
    for result in evaluations:
        if not result["eligible"]:
            continue
        offer = repo.get("offers", result["offer_id"])
        payments = schedule(result["eligible_subtotal_cents"], offer)["payments_cents"]
        penalty, reasons = 0, []
        if preferences.get("avoid_surprise_interest") and offer["plan_type"] == "DEFERRED_INTEREST":
            penalty += 100
            reasons.append("DEFERRED_INTEREST_DEADLINE_RISK")
        if "target_monthly_cents" in preferences:
            difference = abs(payments[0] - preferences["target_monthly_cents"]) if payments else 100000
            penalty += difference // 100
            reasons.append("PAYMENT_TARGET_DISTANCE" if payments else "REVOLVING_PAYMENT_NOT_ESTIMATED")
        if "payoff_horizon_months" in preferences:
            penalty += abs(offer["term_months"] - preferences["payoff_horizon_months"]) * 10 if payments else 1000
        if preferences.get("reward_preference") and offer["plan_type"] == "CASHBACK_REVOLVING":
            penalty -= 20
            reasons.append("REWARD_PREFERENCE_ONLY_NOT_INTEREST_SAVINGS")
        scored.append({"offer_id": offer["id"], "penalty": penalty, "reason_codes": reasons,
                       "estimated_first_payment_cents": payments[0] if payments else None})
    scored.sort(key=lambda result: (result["penalty"], result["offer_id"]))
    ambiguous = len(scored) > 1 and scored[0]["penalty"] == scored[1]["penalty"]
    return {"offer_id": scored[0]["offer_id"] if scored and not ambiguous else None, "scores": scored,
            "scoring_inputs": preferences, "commercial_steering_inputs": [],
            "explanation": "Lowest transparent penalty among eligible options. Deferred interest has surprise-interest risk; a recommendation is not acceptance. Confirm that tradeoff with the consumer." if not ambiguous else "Preferences do not distinguish the leading offers; ask for a payoff horizon."}
