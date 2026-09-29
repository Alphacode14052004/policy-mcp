"""Synthetic event-clock tests; these are not claims of live human presentation."""
import copy
import json
import unittest
from datetime import timedelta

from offerproof.models.contracts import ENVELOPE, validate
from offerproof.security.digests import instant, iso
from tests.helpers import Harness


class PresentationTimingTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)

    def status(self, response):
        return self.h.call("get_offer_journey_status", {"journey_id": response["journey_id"],
            "merchant_id": self.h.request["merchant_id"], "agent_id": self.h.request["agent_id"]})

    def assertFailure(self, response, check):
        validate(response, ENVELOPE)
        self.assertEqual(response["reason_code"], "PRESENTATION_EVIDENCE_INVALID", response)
        error = response["result"]["presentation_error"]
        self.assertEqual(error["check"], check)
        self.assertIn("not events to copy", error["timing"]["instruction"])
        self.assertNotIn("receipt", response["result"])
        return error

    def test_issuance_and_clock_are_exposed_and_persisted_once(self):
        start = self.h.start()
        self.assertEqual(start["server_time"], iso(self.h.clock()))
        self.h.clock.now += timedelta(seconds=47, microseconds=123456)
        prepared = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(start))
        issued_at = prepared["result"]["issued_at"]
        self.assertEqual(issued_at, iso(self.h.clock()))
        self.assertEqual(prepared["server_time"], issued_at)
        self.h.clock.now += timedelta(seconds=5)
        status = self.status(prepared)
        validate(status, ENVELOPE)
        self.assertEqual(status["result"]["issued_at"], issued_at)
        self.assertEqual(status["result"]["prepared"]["issued_at"], issued_at)
        self.assertEqual(status["server_time"], iso(self.h.clock()))
        timing = status["result"]["presentation_timing"]
        self.assertEqual(timing["earliest_acceptable_rendered_at"], issued_at)
        self.assertEqual(timing["latest_acceptable_rendered_at"], iso(self.h.clock()))
        with self.h.service.store.connect() as c:
            snapshot = json.loads(c.execute("SELECT body FROM disclosure_snapshots").fetchone()[0])
        self.assertEqual(snapshot["issued_at"], issued_at)
        self.assertEqual(prepared["result"]["presentation_requirements"]["maximum_age_seconds"], 900)

    def test_exact_reported_failures_explain_future_then_preissuance_retries(self):
        self.h.clock.now = instant("2026-09-29T12:01:52.389748Z")
        start = self.h.start()
        self.h.clock.now = instant("2026-09-29T12:02:38.564961Z")
        prepared = self.h.call("prepare_offer_disclosure", self.h.prepare_payload(start))
        for now, reported, check in (
            ("2026-09-29T12:02:51.389538Z", "2026-09-29T12:03:00Z", "RENDERED_AT_IN_FUTURE"),
            ("2026-09-29T12:03:14.343354Z", "2026-09-29T12:01:53Z", "RENDERED_AT_BEFORE_ISSUANCE"),
            ("2026-09-29T12:03:21.757046Z", "2026-09-29T12:01:52.388913Z", "RENDERED_AT_BEFORE_ISSUANCE"),
        ):
            with self.subTest(check=check, reported=reported):
                self.h.clock.now = instant(now)
                payload = self.h.record_payload(prepared, prepared["result"])
                payload["evidence"]["rendered_at"] = reported
                response = self.h.call("record_disclosure_outcome", payload)
                error = self.assertFailure(response, check)
                self.assertEqual(error["received_at"], reported)
                self.assertEqual(error["timing"]["issued_at"], "2026-09-29T12:02:38.564961Z")
                self.assertEqual(error["timing"]["server_time"], now)
                self.assertEqual(response["journey_state"], "DISCLOSURE_ISSUED")
                self.assertEqual(response["journey_version"], 2)
                self.assertIn("never guess", response["next_action"]["instruction"])
        status = self.status(prepared)
        self.assertIsNone(status["result"]["presentation"])
        self.assertIsNone(status["result"]["receipt"])
        self.assertIsNone(status["result"]["authorization"])
        self.assertEqual(sum(e["event_type"] == "DISCLOSURE_PRESENTATION_FAILED" for e in self.h.events()), 3)

    def test_cached_failure_retains_clock_and_status_provides_fresh_clock(self):
        p = self.h.prepared()
        payload = self.h.record_payload(p, p["result"])
        payload["evidence"]["rendered_at"] = iso(self.h.clock() + timedelta(seconds=1))
        first = self.h.call("record_disclosure_outcome", payload)
        self.assertFailure(first, "RENDERED_AT_IN_FUTURE")
        self.h.clock.now += timedelta(seconds=3)
        self.assertEqual(self.h.call("record_disclosure_outcome", payload), first)
        status = self.status(p)
        self.assertNotEqual(status["server_time"], first["server_time"])
        self.assertEqual(status["server_time"], iso(self.h.clock()))
        self.assertEqual(status["journey_state"], "DISCLOSURE_ISSUED")

    def test_precise_time_boundaries_are_not_rounded_or_relaxed(self):
        cases = [
            (0, 0, "OK"),
            (900, 0, "OK"),
            (900.000001, 0, "RENDERED_AT_TOO_OLD"),
            (0, 0.000001, "RENDERED_AT_IN_FUTURE"),
            (0, -0.000001, "RENDERED_AT_BEFORE_ISSUANCE"),
        ]
        for elapsed, event_offset, expected in cases:
            with self.subTest(elapsed=elapsed, event_offset=event_offset):
                h = Harness()
                self.addCleanup(h.close)
                p = h.prepared()
                issued = h.clock()
                h.clock.now += timedelta(seconds=elapsed)
                payload = h.record_payload(p, p["result"])
                payload["evidence"]["rendered_at"] = iso(issued + timedelta(seconds=event_offset))
                response = h.call("record_disclosure_outcome", payload)
                if expected == "OK":
                    self.assertEqual(response["reason_code"], "OK", response)
                else:
                    self.assertFailure(response, expected)

    def test_genuine_simulated_event_can_recover_without_timestamp_substitution(self):
        p = self.h.prepared()
        self.h.clock.now += timedelta(seconds=2)
        bad = self.h.record_payload(p, p["result"])
        bad["evidence"]["rendered_at"] = iso(self.h.clock() + timedelta(seconds=10))
        self.assertFailure(self.h.call("record_disclosure_outcome", bad), "RENDERED_AT_IN_FUTURE")
        # Simulate a newly captured renderer event at the controlled current time.
        self.h.clock.now += timedelta(seconds=1)
        actual = self.h.record_payload(p, p["result"])
        supplied = copy.deepcopy(actual)
        response = self.h.call("record_disclosure_outcome", actual)
        self.assertEqual(response["reason_code"], "OK", response)
        self.assertEqual(actual, supplied)
        status = self.status(response)
        self.assertEqual(status["result"]["presentation"]["rendered_at"], actual["evidence"]["rendered_at"])
        self.assertNotEqual(actual["evidence"]["rendered_at"], p["result"]["issued_at"])
        self.assertIsNone(status["result"]["receipt"])

    def test_acknowledgment_timing_errors_remain_separate_from_presentation(self):
        p = self.h.prepared()
        self.h.clock.now += timedelta(seconds=3)
        record = self.h.record_payload(p, p["result"])
        presented = self.h.call("record_disclosure_outcome", record)
        rendered_at = record["evidence"]["rendered_at"]
        self.h.clock.now += timedelta(seconds=2)
        for captured, check in ((instant(rendered_at) - timedelta(microseconds=1), "ACKNOWLEDGMENT_BEFORE_PRESENTATION"),
                                (self.h.clock() + timedelta(microseconds=1), "ACKNOWLEDGMENT_IN_FUTURE")):
            ack = {**record, **self.h.base(presented), "outcome": "ACKNOWLEDGED", "acknowledgment": {
                "actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-TIMING-ACK",
                "captured_at": iso(captured), "affirmative_action": True}}
            response = self.h.call("record_disclosure_outcome", ack)
            error = self.assertFailure(response, check)
            self.assertEqual(error["accepted_rendered_at"], rendered_at)
            self.assertEqual(response["journey_state"], "DISCLOSURE_PRESENTED")
        ack.update(self.h.base(presented))
        ack["acknowledgment"]["captured_at"] = iso(self.h.clock())
        accepted = self.h.call("record_disclosure_outcome", ack)
        self.assertEqual(accepted["reason_code"], "OK", accepted)
        self.assertEqual(accepted["result"]["receipt"]["payload"]["acknowledged_at"], ack["acknowledgment"]["captured_at"])

    def test_delayed_ack_recovery_retains_diagnostic_after_invalidation(self):
        p = self.h.prepared()
        payload = self.h.record_payload(p, p["result"])
        r = self.h.call("record_disclosure_outcome", payload)
        self.h.clock.now += timedelta(minutes=16)
        payload.update({**self.h.base(r), "outcome": "ACKNOWLEDGED", "acknowledgment": {
            "actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-LATE-ACK",
            "captured_at": iso(self.h.clock()), "affirmative_action": True}})
        response = self.h.call("record_disclosure_outcome", payload)
        self.assertFailure(response, "RENDERED_AT_TOO_OLD")
        self.assertEqual(response["journey_state"], "OFFERS_EVALUATED")
        self.assertEqual(response["next_action"]["tool"], "prepare_offer_disclosure")
        status = self.status(response)
        self.assertIsNone(status["result"]["issued_at"])
        self.assertIsNone(status["result"]["presentation_timing"])

    def test_other_evidence_failures_are_not_misreported_as_timestamp_errors(self):
        p = self.h.prepared()
        payload = self.h.record_payload(p, p["result"])
        payload["evidence"]["locale"] = "xx-XX"
        error = self.assertFailure(self.h.call("record_disclosure_outcome", payload), "PRESENTATION_CONTEXT_MISMATCH")
        self.assertEqual(error["field"], "evidence.locale")
        payload = self.h.record_payload(p, p["result"])
        payload["evidence"]["protected_text_digest"] = "0" * 64
        payload["evidence"]["scroll_visibility_attested"] = False
        error = self.assertFailure(self.h.call("record_disclosure_outcome", payload), "PRESENTATION_REQUIREMENTS_FAILED")
        self.assertEqual(set(error["failed_checks"]), {"protected_text_digest", "scroll_visibility_attested"})

    def test_legacy_issued_status_exposes_time_without_rewriting_snapshot(self):
        p = self.h.prepared()
        with self.h.service.store.connect() as c:
            journey = self.h.service.store.load(c, p["journey_id"])
            issued_at = journey["prepared"].pop("issued_at")
            self.h.service.store.save(c, journey)
            original_snapshot = c.execute("SELECT body FROM disclosure_snapshots").fetchone()[0]
        self.h.clock.now += timedelta(seconds=7)
        status = self.status(p)
        self.assertEqual(status["result"]["issued_at"], issued_at)
        self.assertEqual(status["result"]["prepared"]["issued_at"], issued_at)
        with self.h.service.store.connect() as c:
            self.assertNotIn("issued_at", self.h.service.store.load(c, p["journey_id"])["prepared"])
            self.assertEqual(c.execute("SELECT body FROM disclosure_snapshots").fetchone()[0], original_snapshot)

    def test_legacy_cached_response_without_clock_remains_schema_valid(self):
        response = self.h.start()
        response.pop("server_time")
        with self.h.service.store.connect() as c:
            c.execute("UPDATE idempotency SET response=? WHERE key=?", (json.dumps(response), self.h.request["idempotency_key"]))
        replay = self.h.start()
        self.assertEqual(replay, response)
        validate(replay, ENVELOPE)
