from offerproof.models.contracts import Block
from offerproof.security.digests import instant


class LegalPolicyResolver:
    def __init__(self, repository):
        self.repo = repository

    def resolve(self, context, terms, *, merchant, channel, program):
        profile = self.repo.active(self.repo.get("jurisdiction-profiles", context["profile_id"]))
        if any(context.get(k) != v for k, v in profile["matches"].items()):
            raise Block("POLICY_REVIEW_REQUIRED")
        if (context["account_program"] != program or context["origination_channel"] != channel
                or context["merchant_location"] != merchant["location"] or terms["program_id"] != program):
            raise Block("POLICY_REVIEW_REQUIRED")
        policy = self.repo.active(self.repo.get("policy-bundles", profile["policy_id"]))
        transaction = instant(context["transaction_at"])
        if not instant(policy["effective_at"]) <= transaction < instant(policy["expires_at"]):
            raise Block("POLICY_REVIEW_REQUIRED")
        rate = policy["effective_terms"]["standard_apr_override_bps"]
        return {"policy_id": policy["id"], "policy_version": policy["version"],
                "legal_approval_id": policy["legal_approval_id"], "effective_terms": {
                    "standard_apr_bps": terms["standard_apr_bps"] if rate is None else rate,
                    "apr_type": terms["apr_type"], "apr_source": terms["id"] if rate is None else policy["id"]},
                "explanation_code": policy["explanation_code"], "source_system": policy["source_system"],
                "label": "Mock policy applied", "profile": profile, "bundle": policy}
