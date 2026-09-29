import copy
import unittest

from offerproof.models.contracts import ENVELOPE, validate
from offerproof.security.digests import text_digest
from tests.helpers import Harness
from tests.scenarios.test_sofa_tender import sofa_request


class DisclosurePreviewTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)
        self.h.request = sofa_request()

    def start(self):
        response = self.h.start()
        validate(response, ENVELOPE)
        self.assertEqual(response["reason_code"], "OK", response)
        return response

    def preview(self, response, offer="DI-6M"):
        return next(item for item in response["result"]["offers"] if item["offer_id"] == offer)["disclosure_preview"]

    def test_sofa_disclosures_are_available_before_any_selection(self):
        r = self.start()
        self.assertEqual(r["journey_state"], "OFFERS_EVALUATED")
        self.assertTrue(r["result"]["comparison_only"])
        self.assertFalse(r["result"]["selection_is_acceptance"])
        self.assertIn("Before asking for a selection", r["next_action"]["instruction"])
        for item in r["result"]["offers"]:
            self.assertEqual("disclosure_preview" in item, item["eligible"])
        di = self.preview(r)
        for phrase in ("interest will be charged from the purchase date", "2027-03-29", "23.45% variable",
                       "Minimum monthly payments are required", "not the account minimum payment", "$650.00", "$100.00"):
            self.assertIn(phrase, di["canonical_text"])
        self.assertEqual(di["facts"]["payments_cents"], [10900] * 5 + [10500])
        self.assertEqual(di["facts"]["total_payments_cents"], 65000)
        self.assertIn("excludes any deferred interest", di["payment_explanation"])
        self.assertEqual(di["pending_confirmations"], ["applied_tender_confirmation"])
        standard = self.preview(r, "STANDARD-REV")
        self.assertIn("Standard purchase APR 23.45% variable", standard["canonical_text"])
        self.assertIsNone(standard["facts"]["total_payments_cents"])
        self.assertEqual(standard["facts"]["payments_cents"], [])

    def test_previews_use_exact_versioned_templates_for_every_eligible_family(self):
        cart = self.h.request["cart"]
        cart["lines"][0]["unit_price_cents"] = cart["total_cents"] = 120000
        r = self.start()
        self.assertEqual(sum(item["eligible"] for item in r["result"]["offers"]), 6)
        for item in r["result"]["offers"]:
            p = item["disclosure_preview"]
            template = self.h.service.repo.get("disclosures", p["versions"]["disclosure_id"])
            self.assertEqual(p["canonical_text"], template["template"].format(**p["interpolation_inputs"]))
            self.assertEqual(p["disclosure_digest"], text_digest(p["canonical_text"]))
            self.assertTrue(p["canonical_text_must_not_be_modified"])
            self.assertEqual(p["facts"]["plan_type"], item["plan_type"])

    def test_preview_does_not_issue_disclosure_confirm_tender_or_record_consent(self):
        r = self.start()
        p = self.preview(r)
        self.assertFalse(p["is_final_disclosure"])
        self.assertFalse(p["selection_is_acceptance"])
        self.assertTrue(p["allocation"]["applied_tender_confirmation_required"])
        self.assertNotIn("applied_tender_confirmed_by", p["allocation"])
        with self.h.service.store.connect() as connection:
            journey = self.h.service.store.load(connection, r["journey_id"])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM disclosure_snapshots").fetchone()[0], 0)
        for key in ("prepared", "presentation", "receipt", "acknowledgment", "authorization"):
            self.assertNotIn(key, journey)
        events = self.h.events()
        self.assertEqual(sum(e["event_type"] == "DISCLOSURE_PREVIEW_GENERATED" for e in events), 2)
        self.assertFalse(any(e["event_type"] in {"DISCLOSURE_ISSUED", "ACKNOWLEDGMENT_RECEIVED", "PROMOTION_AUTHORIZED"} for e in events))

    def test_preview_cannot_be_used_as_presentation_acknowledgment_or_authorization(self):
        r = self.start()
        p = self.preview(r)
        # Even evidence for identical final copy issued in another journey must
        # not turn this journey's preview into an issued/presented disclosure.
        other_request = copy.deepcopy(self.h.request)
        other_request["idempotency_key"] += "-other-evidence"
        other = self.h.start(other_request)
        other_final = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(other))["result"]
        self.assertEqual(other_final["disclosure_digest"], p["disclosure_digest"])
        for outcome in ("PRESENTED", "ACKNOWLEDGED"):
            payload = self.h.record_payload(r, other_final, outcome)
            self.assertEqual(self.h.call("record_disclosure_outcome", payload)["reason_code"], "INVALID_STATE_TRANSITION")
        auth = {**self.h.base(r), "cart": self.h.request["cart"], "jurisdiction": self.h.request["jurisdiction"], "offer_id": "DI-6M"}
        self.assertEqual(self.h.call("authorize_promotional_checkout", auth)["reason_code"], "INVALID_STATE_TRANSITION")
        request = self.h.prepare_payload(r)
        request.pop("applied_tender_confirmation")
        self.assertEqual(self.h.call("prepare_offer_disclosure", request)["reason_code"], "APPLIED_TENDER_CONFIRMATION_REQUIRED")

    def test_selected_preview_is_reissued_as_final_before_separate_consent(self):
        r = self.start()
        preview = self.preview(r)
        p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r))
        self.assertEqual(p["reason_code"], "OK", p)
        self.assertEqual(p["result"]["canonical_text"], preview["canonical_text"])
        self.assertFalse(p["result"]["allocation"]["applied_tender_confirmation_required"])
        self.assertIn("snapshot_id", p["result"])
        self.assertNotIn("receipt", p["result"])
        with self.h.service.store.connect() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM disclosure_snapshots").fetchone()[0], 1)
        premature = self.h.record_payload(p, p["result"], "ACKNOWLEDGED")
        self.assertEqual(self.h.call("record_disclosure_outcome", premature)["reason_code"], "DISCLOSURE_NOT_PRESENTED")

    def test_status_and_idempotent_retry_preserve_the_comparison(self):
        r = self.start()
        self.assertEqual(self.h.start(), r)
        status = self.h.call("get_offer_journey_status", {"journey_id": r["journey_id"],
            "merchant_id": self.h.request["merchant_id"], "agent_id": self.h.request["agent_id"]})
        self.assertEqual(status["result"]["offers"], r["result"]["offers"])
        self.assertIn("Before asking for a selection", status["result"]["presentation_guidance"])
        self.assertEqual(sum(e["event_type"] == "DISCLOSURE_PREVIEW_GENERATED" for e in self.h.events()), 2)

    def test_previews_keep_excluded_purchase_confirmation_pending(self):
        from scripts.demo import fixture
        self.h.request = fixture()
        r = self.start()
        p = self.preview(r)
        self.assertEqual(p["pending_confirmations"], ["allocation_confirmation"])
        self.assertIn("separate tender, pending your confirmation", p["canonical_text"])
        self.assertTrue(p["allocation"]["confirmation_required"])
        final = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r))["result"]
        self.assertNotEqual(p["disclosure_digest"], final["disclosure_digest"])
        self.assertFalse(final["allocation"]["confirmation_required"])

    def test_standard_only_fallback_still_has_disclosure_before_selection(self):
        self.h.request["cart"].pop("applied_tenders")
        self.h.request["cart"]["lines"][0]["unit_price_cents"] = 10000
        self.h.request["cart"]["total_cents"] = 10000
        r = self.h.start()
        self.assertEqual(r["reason_code"], "NO_ELIGIBLE_PROMOTION")
        self.assertIn("canonical_text", r["result"]["standard_fallback"]["disclosure_preview"])
        self.assertEqual(self.preview(r, "STANDARD-REV")["pending_confirmations"], [])
        self.assertNotIn("still need your confirmation", self.preview(r, "STANDARD-REV")["consumer_notice"])

    def test_final_disclosure_revalidates_terms_after_preview(self):
        r = self.start()
        original = self.preview(r)
        self.h.edit("account-terms", "MOCK-TERMS-001", lambda t: t.update(version="2.0.0", standard_apr_bps=2456))
        for offer in self.h.service.repo.all("offers"):
            self.h.edit("offers", offer["id"], lambda o: o.update(terms_version="2.0.0"))
        p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r))
        self.assertEqual(p["reason_code"], "OK", p)
        self.assertIn("24.56% variable", p["result"]["canonical_text"])
        self.assertNotEqual(p["result"]["disclosure_digest"], original["disclosure_digest"])
        self.assertEqual(p["result"]["versions"]["terms_version"], "2.0.0")

    def test_legacy_comparison_requires_new_journey_instead_of_silent_selection(self):
        r = self.start()
        with self.h.service.store.connect() as connection:
            journey = self.h.service.store.load(connection, r["journey_id"])
            for item in journey["evaluations"]:
                item.pop("disclosure_preview", None)
            self.h.service.store.save(connection, journey)
        status = self.h.call("get_offer_journey_status", {"journey_id": r["journey_id"],
            "merchant_id": self.h.request["merchant_id"], "agent_id": self.h.request["agent_id"]})
        self.assertEqual(status["next_action"]["tool"], "start_offer_journey")
        blocked = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r))
        self.assertEqual(blocked["reason_code"], "INVALID_STATE_TRANSITION")
        self.assertEqual(blocked["next_action"]["tool"], "start_offer_journey")
