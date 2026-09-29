"""Regression coverage for purchased gift cards versus existing mock payment."""
import copy
import json
import unittest

from offerproof.config import ROOT
from offerproof.models.contracts import ENVELOPE, validate
from offerproof.security.digests import digest, normalized_cart
from scripts.demo import fixture
from tests.helpers import Harness


def sofa_request():
    return json.loads((ROOT / "demo-data/sofa-gift-card-redemption.json").read_text(encoding="utf-8"))


class SofaTenderTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)
        self.h.request = sofa_request()

    def assertCode(self, response, code):
        validate(response, ENVELOPE)
        self.assertEqual(response["reason_code"], code, response)

    def offers(self, response):
        return {o["offer_id"]: o for o in response["result"]["offers"]}

    def test_existing_gift_payment_uses_650_not_750_or_850(self):
        r = self.h.start()
        self.assertCode(r, "OK")
        self.assertEqual(r["result"]["cart_total_cents"], 75000)
        self.assertEqual(r["result"]["applied_tender_cents"], 10000)
        self.assertEqual(r["result"]["remaining_balance_cents"], 65000)
        self.assertEqual(r["result"]["gift_card_purchase_cents"], 0)
        offers = self.offers(r)
        self.assertTrue(offers["DI-6M"]["eligible"])
        self.assertEqual(offers["DI-6M"]["eligible_subtotal_cents"], 65000)
        self.assertEqual(offers["DI-6M"]["excluded_cents"], 0)
        self.assertEqual(offers["EPP-12-0APR"]["reason_codes"], ["ELIGIBLE_SUBTOTAL_BELOW_MINIMUM"])

    def test_sofa_without_payment_meets_epp_threshold(self):
        self.h.request["cart"].pop("applied_tenders")
        r = self.h.start()
        self.assertCode(r, "OK")
        self.assertTrue(self.offers(r)["EPP-12-0APR"]["eligible"])
        self.assertEqual(self.offers(r)["EPP-12-0APR"]["eligible_subtotal_cents"], 75000)

    def test_buying_gift_card_keeps_total_850_and_financed_750(self):
        cart = self.h.request["cart"]
        cart.pop("applied_tenders")
        cart["lines"].append(fixture()["cart"]["lines"][1])
        cart["total_cents"] = 85000
        r = self.h.start()
        self.assertCode(r, "OK")
        self.assertEqual(r["result"]["gift_card_purchase_cents"], 10000)
        self.assertEqual(r["result"]["remaining_balance_cents"], 85000)
        self.assertEqual(r["result"]["applied_tender_cents"], 0)
        epp = self.offers(r)["EPP-12-0APR"]
        self.assertTrue(epp["eligible"])
        self.assertEqual(epp["eligible_subtotal_cents"], 75000)
        self.assertEqual(epp["excluded_cents"], 10000)

    def test_payment_confirmation_is_required_and_amount_bound(self):
        start = self.h.start()
        for confirmation in (None, {"confirmed": False, "applied_tender_cents": 10000, "confirmed_by": "CONSUMER"},
                             {"confirmed": True, "applied_tender_cents": 9900, "confirmed_by": "CONSUMER"}):
            with self.subTest(confirmation=confirmation):
                payload = self.h.prepare_payload(start)
                payload.pop("applied_tender_confirmation")
                if confirmation is not None:
                    payload["applied_tender_confirmation"] = confirmation
                r = self.h.call("prepare_offer_disclosure", payload)
                self.assertCode(r, "APPLIED_TENDER_CONFIRMATION_REQUIRED")
                self.assertEqual(r["journey_version"], start["journey_version"])
                self.assertEqual(r["next_action"]["tool"], "prepare_offer_disclosure")
        p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(start))
        self.assertCode(p, "OK")
        allocation = p["result"]["allocation"]
        self.assertEqual(allocation["financed_cents"], 65000)
        self.assertEqual(allocation["excluded_cents"], 0)
        self.assertEqual(allocation["applied_tender_cents"], 10000)
        for phrase in ("Purchase total before payment $750.00", "Existing mock gift-card payment $100.00", "Financed eligible amount $650.00"):
            self.assertIn(phrase, p["result"]["canonical_text"])

    def test_payment_and_excluded_purchase_need_separate_confirmations(self):
        cart = self.h.request["cart"]
        cart["lines"].append(fixture()["cart"]["lines"][1])
        cart["total_cents"] += 10000
        start = self.h.start()
        payload = self.h.prepare_payload(start)
        payload.pop("allocation_confirmation")
        self.assertCode(self.h.call("prepare_offer_disclosure", payload), "ALLOCATION_CONFIRMATION_REQUIRED")
        p = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(start))
        self.assertCode(p, "OK")
        allocation = p["result"]["allocation"]
        self.assertEqual((allocation["financed_cents"], allocation["excluded_cents"], allocation["applied_tender_cents"]), (65000, 10000, 10000))

    def test_full_journey_receipt_binds_payment_and_preserves_it_on_status(self):
        r, _ = self.h.acknowledged()
        status = self.h.call("get_offer_journey_status", {"journey_id": r["journey_id"],
            "merchant_id": self.h.request["merchant_id"], "agent_id": self.h.request["agent_id"]})
        self.assertCode(status, "OK")
        self.assertEqual(status["result"]["remaining_balance_cents"], 65000)
        receipt = r["result"]["receipt"]["payload"]
        self.assertEqual(receipt["cart_digest"], digest(normalized_cart(self.h.request["cart"])))
        self.assertEqual(receipt["allocation_digest"], digest(status["result"]["prepared"]["allocation"]))
        authorized = self.h.call("authorize_promotional_checkout", self.h.auth_payload(r))
        self.assertCode(authorized, "OK")
        self.assertEqual(authorized["journey_state"], "AUTHORIZED")
        self.assertFalse(authorized["result"]["payment_processed"])

    def test_changed_payment_amount_or_reference_invalidates_receipt(self):
        for field in ("amount", "reference"):
            with self.subTest(field=field):
                h = Harness()
                self.addCleanup(h.close)
                h.request = sofa_request()
                r, _ = h.acknowledged()
                payload = h.auth_payload(r)
                tender = payload["cart"]["applied_tenders"][0]
                if field == "amount":
                    tender["amount_cents"] -= 100
                    tender["line_allocations"][0]["amount_cents"] -= 100
                else:
                    tender["tender_id"] = "MOCK-GIFT-DIFFERENT"
                result = h.call("authorize_promotional_checkout", payload)
                self.assertCode(result, "CART_DIGEST_MISMATCH")
                self.assertEqual(result["journey_state"], "INVALIDATED")

    def test_invalid_payment_allocations_block_before_journey_and_are_audited(self):
        for case in ("duplicate_tender", "duplicate_line", "wrong_sum", "unknown_line", "overdraw", "gift_purchase", "net_total"):
            with self.subTest(case=case):
                request = sofa_request()
                request["idempotency_key"] = "bad-tender-" + case
                cart = request["cart"]
                tender = cart["applied_tenders"][0]
                allocation = tender["line_allocations"][0]
                if case == "duplicate_tender":
                    cart["applied_tenders"].append(copy.deepcopy(tender))
                elif case == "duplicate_line":
                    tender["line_allocations"].append(copy.deepcopy(allocation))
                    tender["amount_cents"] *= 2
                elif case == "wrong_sum":
                    tender["amount_cents"] += 1
                elif case == "unknown_line":
                    allocation["line_id"] = "unknown"
                elif case == "overdraw":
                    tender["amount_cents"] = allocation["amount_cents"] = 75001
                elif case == "gift_purchase":
                    cart["lines"].append(fixture()["cart"]["lines"][1])
                    cart["total_cents"] += 10000
                    allocation["line_id"] = cart["lines"][1]["line_id"]
                else:
                    cart["total_cents"] -= 10000
                code = "SCHEMA_VALIDATION_FAILED" if case == "net_total" else "TENDER_ALLOCATION_INVALID"
                r = self.h.start(request)
                self.assertCode(r, code)
                self.assertIsNone(r["journey_id"])
                events = self.h.events()
                self.assertEqual(events[-2]["outcome"], "ATTEMPTED")
                self.assertEqual(events[-1]["outcome"], "BLOCKED")

    def test_payment_schema_rejects_unsupported_types_and_nonpositive_amounts(self):
        for field, value in (("tender_type", "CASH"), ("amount_cents", -100), ("amount_cents", True), ("extra", "ignored")):
            with self.subTest(field=field, value=value):
                request = sofa_request()
                request["cart"]["applied_tenders"][0][field] = value
                self.assertCode(self.h.start(request), "SCHEMA_VALIDATION_FAILED")

    def test_offer_can_disallow_applied_gift_payment(self):
        self.h.edit("offers", "DI-6M", lambda o: o.update(allowed_applied_tender_types=[]))
        r = self.h.start()
        offer = self.offers(r)["DI-6M"]
        self.assertFalse(offer["eligible"])
        self.assertIn("TENDER_POLICY_UNSUPPORTED", offer["reason_codes"])
        self.assertCode(self.h.call("prepare_offer_disclosure", self.h.prepare_payload(r)), "TENDER_POLICY_UNSUPPORTED")

    def test_unknown_product_returns_catalog_recovery_not_jurisdiction_failure(self):
        self.h.request["cart"]["lines"][0].update(sku="MOCK-SKU-CHAIR", category="CHAIR")
        r = self.h.start()
        self.assertCode(r, "PRODUCT_NOT_CONFIGURED")
        self.assertIsNone(r["journey_id"])
        self.assertEqual(r["next_action"]["tool"], "REQUEST_MOCK_CATALOG_UPDATE")
        self.assertIn({"sku": "MOCK-SKU-SOFA", "category": "SOFA", "item_type": "GOODS"}, r["result"]["supported_products"])

    def test_payment_digest_normalizes_order_but_binds_line_allocations(self):
        cart = sofa_request()["cart"]
        second_line = copy.deepcopy(cart["lines"][0])
        second_line["line_id"] = "sofa-2"
        cart["lines"].append(second_line)
        cart["total_cents"] *= 2
        tender = cart["applied_tenders"][0]
        tender["line_allocations"] = [{"line_id": "line-sofa", "amount_cents": 5000}, {"line_id": "sofa-2", "amount_cents": 5000}]
        second_tender = copy.deepcopy(tender)
        second_tender["tender_id"] = "MOCK-GIFT-2"
        cart["applied_tenders"].append(second_tender)
        reordered = copy.deepcopy(cart)
        reordered["lines"].reverse()
        reordered["applied_tenders"].reverse()
        for t in reordered["applied_tenders"]:
            t["line_allocations"].reverse()
        self.assertEqual(digest(normalized_cart(cart)), digest(normalized_cart(reordered)))
        reordered["applied_tenders"][0]["line_allocations"][0]["amount_cents"] += 1
        reordered["applied_tenders"][0]["line_allocations"][1]["amount_cents"] -= 1
        self.assertNotEqual(digest(normalized_cart(cart)), digest(normalized_cart(reordered)))
        cart.pop("applied_tenders")
        empty = {**cart, "applied_tenders": []}
        self.assertEqual(digest(normalized_cart(cart)), digest(normalized_cart(empty)))
