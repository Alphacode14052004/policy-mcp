import copy
import json
import unittest
from datetime import timedelta
from offerproof.models.contracts import Block
from offerproof.security.digests import iso
from tests.helpers import Harness


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)

    def test_no_ack_policy_still_requires_signed_presentation_receipt(self):
        self.h.edit("offers", "DI-6M", lambda r: r.update(acknowledgment_required=False))
        p = self.h.prepared()
        presented = self.h.call("record_disclosure_outcome", self.h.record_payload(p, p["result"]))
        self.assertIsNotNone(presented["result"]["receipt"])
        auth = self.h.auth_payload(presented)
        no_receipt = copy.deepcopy(auth)
        no_receipt.pop("receipt")
        self.assertEqual(self.h.call("authorize_promotional_checkout", no_receipt)["reason_code"], "RECEIPT_INVALID")
        auth["idempotency_key"] += "-valid"
        self.assertEqual(self.h.call("authorize_promotional_checkout", auth)["journey_state"], "AUTHORIZED")

    def test_all_plan_families_produce_matching_canonical_copy(self):
        self.h.request["cart"]["lines"][0]["unit_price_cents"] = 100001
        self.h.request["cart"]["total_cents"] = 110001
        for offer in self.h.service.repo.all("offers"):
            self.h.request["idempotency_key"] = offer["id"]
            r = self.h.start()
            p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r, offer["id"]))
            self.assertEqual(p["reason_code"], "OK", p)
            self.assertEqual(p["result"]["facts"]["plan_type"], offer["plan_type"])
            self.assertTrue(p["result"]["canonical_text_must_not_be_modified"])

    def test_new_offer_name_cannot_mislabel_deferred_interest(self):
        self.h.edit("offers", "DI-6M", lambda r: r.update(name="Mock 0% interest"))
        self.assertEqual(self.h.start()["reason_code"], "POLICY_REVIEW_REQUIRED")

    def test_reward_facts_come_from_config(self):
        self.h.edit("offers", "CASHBACK-REV", lambda r: r["reward"].update(rate_bps=150, cap_cents=3000, vesting_days=45))
        self.h.request["cart"]["lines"][0]["unit_price_cents"] = 100000
        self.h.request["cart"]["total_cents"] = 110000
        p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(self.h.start(), "CASHBACK-REV"))
        text = p["result"]["canonical_text"]
        for value in ("1.50%", "$30.00", "45 days"):
            self.assertIn(value, text)

    def test_unsigned_policy_fails_startup(self):
        path = self.h.data / "policy-bundles.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["records"][0].pop("checksum")
        path.write_text(json.dumps(document), encoding="utf-8")
        self.assertEqual(self.h.start()["reason_code"], "POLICY_REVIEW_REQUIRED")

    def test_draft_policy_fails_closed(self):
        self.h.edit("policy-bundles", "MOCK_DEFAULT", lambda r: r.update(status="DRAFT"))
        self.assertEqual(self.h.start()["reason_code"], "POLICY_REVIEW_REQUIRED")

    def test_renderer_version_change_invalidates_receipt(self):
        r, _ = self.h.acknowledged()
        self.h.edit("renderer-profiles", "MOCK-RENDERER-CHAT", lambda v: v.update(renderer_version="2.0.0"))
        result = self.h.call("authorize_promotional_checkout", self.h.auth_payload(r))
        self.assertEqual(result["reason_code"], "DISCLOSURE_DIGEST_MISMATCH")
        self.assertEqual(result["journey_state"], "OFFERS_EVALUATED")

    def test_tax_shipping_excluded_but_allocation_reconciles(self):
        self.h.request["cart"].update(tax_cents=1001, shipping_cents=999, total_cents=82000)
        p = self.h.prepared()["result"]
        self.assertEqual(p["allocation"]["financed_cents"], 70000)
        self.assertEqual(p["allocation"]["excluded_cents"], 12000)

    def test_unconfirmed_or_standard_tender_never_silently_assigned(self):
        r = self.h.start()
        p = self.h.prepare_payload(r)
        p["allocation_confirmation"]["excluded_disposition"] = "STANDARD_REVOLVING"
        blocked = self.h.call("prepare_offer_disclosure", p)
        self.assertEqual(blocked["reason_code"], "ALLOCATION_CONFIRMATION_REQUIRED")
        self.assertEqual(blocked["next_action"]["tool"], "CONFIRM_SEPARATE_TENDER")

    def test_rejected_presentation_does_not_issue_receipt(self):
        p = self.h.prepared()
        record = self.h.record_payload(p, p["result"], "PRESENTATION_FAILED")
        result = self.h.call("record_disclosure_outcome", record)
        self.assertEqual(result["journey_state"], "DISCLOSURE_ISSUED")
        self.assertNotIn("receipt", result["result"])

    def test_snapshot_survives_stale_evidence_invalidation(self):
        r, _ = self.h.acknowledged()
        p = self.h.auth_payload(r)
        p["cart"]["lines"][0]["unit_price_cents"] += 1
        p["cart"]["total_cents"] += 1
        self.h.call("authorize_promotional_checkout", p)
        with self.h.service.store.connect() as c:
            row = c.execute("SELECT body FROM disclosure_snapshots WHERE journey_id=?", (r["journey_id"],)).fetchone()
            self.assertIn("No interest if paid in full", json.loads(row[0])["canonical_text"])

    def test_sensitive_request_identifier_is_not_written_to_audit(self):
        p = copy.deepcopy(self.h.request)
        p["request_id"] = "000-00-0000"
        self.assertEqual(self.h.start(p)["reason_code"], "PROHIBITED_SENSITIVE_DATA")
        self.assertNotIn("000-00-0000", str(self.h.events()))

    def test_delayed_acknowledgment_has_valid_repreparation_recovery(self):
        p = self.h.prepared()
        record = self.h.record_payload(p, p["result"])
        r = self.h.call("record_disclosure_outcome", record)
        self.h.clock.now += timedelta(minutes=16)
        late = {**record, **self.h.base(r), "outcome": "ACKNOWLEDGED", "acknowledgment": {
            "actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-LATE-EVENT",
            "captured_at": iso(self.h.clock()), "affirmative_action": True}}
        response = self.h.call("record_disclosure_outcome", late)
        self.assertEqual(response["reason_code"], "PRESENTATION_EVIDENCE_INVALID")
        self.assertEqual(response["next_action"]["tool"], "prepare_offer_disclosure")
        prepared_again = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(response))
        self.assertEqual(prepared_again["reason_code"], "OK")
