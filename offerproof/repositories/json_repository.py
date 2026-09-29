"""Approved-mock configuration loader. Reads a bounded set of fixed file names."""
import json
import re
import string
from copy import deepcopy
from offerproof.config import DATA
from offerproof.models.contracts import Block, validate, validate_request
from offerproof.models.data_contracts import document_schema
from offerproof.security.digests import digest, instant, utcnow

FILES = ("products", "merchants", "offers", "disclosures", "policy-bundles", "jurisdiction-profiles",
         "account-terms", "renderer-profiles", "reason-codes", "test-carts")
ALLOWED_VARS = {"term_months", "payoff_date", "standard_apr", "apr_type", "monthly_payment",
                "final_payment", "total_payments", "promo_apr", "finance_cost", "schedule",
                "apr_source", "eligible_amount", "excluded_amount", "excluded_disposition", "policy_id",
                "reward_rate_percent", "reward_cap", "reward_vesting_days", "cart_total", "applied_tender_amount"}


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


class JsonRepository:
    def __init__(self, path=DATA, clock=utcnow):
        self.path, self.clock = path, clock
        self.records = self.read()

    def read(self):
        try:
            collections = {}
            for name in FILES:
                file = self.path / f"{name}.json"
                if file.stat().st_size > 1000000:
                    raise ValueError("Fixture size")
                data = json.loads(file.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
                validate(data, document_schema(name))
                if data["data_classification"] != "SYNTHETIC_HACKATHON_DATA" or data["not_for_production"] is not True:
                    raise ValueError("Fixture classification")
                records = data["records"]
                if len({r["id"] for r in records}) != len(records):
                    raise ValueError("Duplicate ID")
                collections[name] = {r["id"]: r for r in records}
                for record in records:
                    if name not in ("reason-codes", "test-carts"):
                        self.validate_approval(record)
                        if name != "offers":
                            self.active(record)
            self.validate_links(collections)
            return collections
        except (Block, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError):
            raise Block("POLICY_REVIEW_REQUIRED") from None

    def reload(self):
        self.records = self.read()
        return self

    def get(self, collection, ident):
        try:
            return deepcopy(self.records[collection][ident])
        except KeyError:
            raise Block("POLICY_REVIEW_REQUIRED") from None

    def all(self, collection):
        return [self.get(collection, key) for key in sorted(self.records[collection])]

    def validate_approval(self, record):
        if (record["status"] != "APPROVED_MOCK" or record["maker"] == record["checker"]
                or not record["legal_approval_id"].startswith("MOCK-")
                or record["not_for_production"] is not True
                or record["data_classification"] != "SYNTHETIC_HACKATHON_DATA"
                or not record["version"] or not record["source_system"]):
            raise ValueError("Approval")
        if record["checksum"] != digest({k: v for k, v in record.items() if k != "checksum"}):
            raise ValueError("Checksum")
        start, end = instant(record["effective_at"]), instant(record["expires_at"])
        if not (instant(record["approved_at"]) <= start < end
                and start <= instant(record["review_at"]) < end):
            raise ValueError("Dates")
        # Offers may legitimately be expired and must still appear in the catalog.
        for field in ("predecessor", "rollback_reference"):
            if record[field] is not None and not isinstance(record[field], str):
                raise ValueError("Version reference")

    def active(self, record, code="POLICY_REVIEW_REQUIRED"):
        now = self.clock()
        if not instant(record["effective_at"]) <= now < min(instant(record["expires_at"]), instant(record["review_at"])):
            raise Block(code)
        return record

    def validate_links(self, c):
        for profile in c["jurisdiction-profiles"].values():
            if profile["policy_id"] not in c["policy-bundles"]:
                raise ValueError("Policy reference")
            if len(profile["matches"]) != 10:
                raise ValueError("Context inputs")
        for policy in c["policy-bundles"].values():
            rate = policy["effective_terms"]["standard_apr_override_bps"]
            if policy["fictional"] is not True or (rate is not None and (type(rate) is not int or not 0 <= rate <= 10000)):
                raise ValueError("Policy terms")
        for offer in c["offers"].values():
            for collection, field in [("disclosures", "disclosure_id"), ("account-terms", "terms_id")]:
                target = c[collection][offer[field]]
                version_field = "disclosure_version" if collection == "disclosures" else "terms_version"
                if target["version"] != offer[version_field]:
                    raise ValueError("Version reference")
            for ident in offer["merchant_ids"]:
                if ident not in c["merchants"]:
                    raise ValueError("Merchant reference")
            for ident in offer["policy_bundle_ids"]:
                if ident not in c["policy-bundles"]:
                    raise ValueError("Policy reference")
            for ident in offer["jurisdiction_profile_ids"]:
                if ident not in c["jurisdiction-profiles"]:
                    raise ValueError("Profile reference")
            if not any(r["presentation_policy_id"] == offer["presentation_policy_id"] and
                       r["presentation_policy_version"] == offer["presentation_policy_version"]
                       for r in c["renderer-profiles"].values()):
                raise ValueError("Renderer reference")
            if (type(offer["minimum_cents"]) is not int or type(offer["maximum_cents"]) is not int
                    or not 0 <= offer["minimum_cents"] <= offer["maximum_cents"]
                    or type(offer["term_months"]) is not int or not 0 <= offer["term_months"] <= 120):
                raise ValueError("Offer amount")
            if offer["allow_multi_promo"] or offer["reward_stacking"] != "NONE":
                raise ValueError("Unsupported stacking")
            disclosure = c["disclosures"][offer["disclosure_id"]]
            if (disclosure["plan_type"] != offer["plan_type"] or disclosure["product_legal_type"] != offer["product_legal_type"]
                    or disclosure["template_id"] != offer["template_id"] or disclosure["template_version"] != offer["template_version"]):
                raise ValueError("Template family mismatch")
            if offer["plan_type"] == "CUSTOM_AMORTIZATION" and sum(offer["custom_schedule_bps"]) != 10000:
                raise ValueError("Custom schedule")
            if offer["plan_type"] in ("DEFERRED_INTEREST", "EQUAL_PAY_NO_INTEREST", "REDUCED_APR_FIXED_TERM", "CUSTOM_AMORTIZATION") and not offer["term_months"]:
                raise ValueError("Term required")
            if offer["plan_type"] == "EQUAL_PAY_NO_INTEREST" and offer["promo_apr_bps"] != 0:
                raise ValueError("True zero APR required")
            if offer["plan_type"] == "DEFERRED_INTEREST" and offer["promo_apr_bps"] is not None:
                raise ValueError("Deferred interest has no zero APR representation")
            if offer["plan_type"] in ("DEFERRED_INTEREST", "CASHBACK_REVOLVING") and re.search(r"(?<![\d.])0(?:\.0+)?\s*%", offer["name"]):
                raise ValueError("Misleading offer name")
            if offer["plan_type"] == "CUSTOM_AMORTIZATION" and (offer["promo_apr_bps"] != 0 or len(offer["custom_schedule_bps"]) != offer["term_months"]):
                raise ValueError("Custom schedule/template mismatch")
            if offer["plan_type"] == "REDUCED_APR_FIXED_TERM" and offer["promo_apr_bps"] is None:
                raise ValueError("Configured rate required")
            if offer["plan_type"] == "CASHBACK_REVOLVING" and offer["reward"] is None:
                raise ValueError("Reward terms required")
        for d in c["disclosures"].values():
            variables = set()
            for _, field, spec, conversion in string.Formatter().parse(d["template"]):
                if field:
                    if field not in ALLOWED_VARS or spec or conversion:
                        raise ValueError("Template placeholder")
                    variables.add(field)
            if variables != set(d["allowed_vars"]) or not d["template"].startswith("MOCK DISCLOSURE"):
                raise ValueError("Template variables")
            lower = d["template"].lower()
            if d["plan_type"] == "DEFERRED_INTEREST":
                if re.search(r"(?<![\d.])0(?:\.0+)?\s*%", lower) or "no interest if paid in full" not in lower or "from the purchase date" not in lower or "may not pay off" not in lower:
                    raise ValueError("Deferred wording")
            elif d["plan_type"] in ("EQUAL_PAY_NO_INTEREST", "CUSTOM_AMORTIZATION"):
                if "from the purchase date" in lower or "if paid in full" in lower:
                    raise ValueError("Wrong no-interest wording")
            elif d["plan_type"] == "CASHBACK_REVOLVING":
                if re.search(r"(?<![\d.])0(?:\.0+)?\s*%", lower) or "not interest-free financing" not in lower:
                    raise ValueError("Reward wording")
        for case in c["test-carts"].values():
            validate_request("start_offer_journey", case["request"])
