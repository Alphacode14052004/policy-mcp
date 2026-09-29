import copy
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from offerproof.config import DATA
from offerproof.core.orchestration import OfferProof
from offerproof.security.digests import digest, iso
from scripts.demo import common, evidence, fixture


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


class Harness:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="offerproof-test-")
        self.root = Path(self.temporary.name)
        self.data = self.root / "mock-data"
        shutil.copytree(DATA, self.data)
        self.clock = Clock()
        self.service = OfferProof(self.data, self.root / "runtime", self.clock)
        self.request = fixture()
        self.counter = 0

    def close(self):
        self.temporary.cleanup()

    def call(self, tool, payload):
        return self.service.invoke(tool, payload)

    def base(self, response):
        self.counter += 1
        return common(self.request, response, f"test-{self.counter}")

    def start(self, request=None):
        return self.call("start_offer_journey", request or self.request)

    def prepare_payload(self, response, offer="DI-6M"):
        payload = {**self.base(response), "offer_id": offer,
            "allocation_confirmation": {"confirmed": True, "excluded_disposition": "SEPARATE_TENDER", "confirmed_by": "CONSUMER"}}
        applied = sum(t["amount_cents"] for t in self.request["cart"].get("applied_tenders", []))
        if applied:
            payload["applied_tender_confirmation"] = {"confirmed": True, "applied_tender_cents": applied, "confirmed_by": "CONSUMER"}
        return payload

    def prepared(self):
        result = self.call("prepare_offer_disclosure", self.prepare_payload(self.start()))
        assert result["reason_code"] == "OK", result
        return result

    def record_payload(self, response, prepared, outcome="PRESENTED"):
        return {**self.base(response), "renderer_id": self.request["renderer_id"], "cart_digest": prepared["cart_digest"],
            "disclosure_digest": prepared["disclosure_digest"], "outcome": outcome, "evidence": evidence(prepared, self.clock())}

    def acknowledged(self):
        p = self.prepared()
        present = self.record_payload(p, p["result"])
        r = self.call("record_disclosure_outcome", present)
        assert r["reason_code"] == "OK", r
        ack = {**present, **self.base(r), "outcome": "ACKNOWLEDGED", "acknowledgment": {
            "actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-ACK-001", "captured_at": iso(self.clock()), "affirmative_action": True}}
        r = self.call("record_disclosure_outcome", ack)
        assert r["reason_code"] == "OK", r
        return r, ack

    def auth_payload(self, response):
        return {**self.base(response), "cart": copy.deepcopy(self.request["cart"]),
            "jurisdiction": copy.deepcopy(self.request["jurisdiction"]), "offer_id": "DI-6M", "receipt": response["result"]["receipt"]}

    def edit(self, filename, ident, change):
        path = self.data / f"{filename}.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        record = next(r for r in document["records"] if r["id"] == ident)
        change(record)
        if "checksum" in record:
            record["checksum"] = digest({k: v for k, v in record.items() if k != "checksum"})
        path.write_text(json.dumps(document), encoding="utf-8")

    def events(self):
        with self.service.store.connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM audit ORDER BY seq")]
