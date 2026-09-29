import json
import re
import uuid
from offerproof.security.digests import canonical, digest, iso


def safe_id(value):
    # Only opaque synthetic identifiers; rejected payloads never become audit text.
    if isinstance(value, str) and len(value) <= 80 and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", value):
        if not re.search(r"\d{9,}|\d{3}-\d{2}-\d{4}", value):
            return value
    return None


class AuditStore:
    def append(self, connection, *, invocation_id, tool, payload, event_type, outcome, reason, now, journey=None, offer_id=None):
        raw = payload if isinstance(payload, dict) else {}
        # For validation failures retain server correlation only, not unvalidated fields.
        request = journey["request"] if journey else {}
        prepared = journey.get("prepared", {}) if journey else {}
        event = {"event_id": "event-" + uuid.uuid4().hex, "invocation_id": invocation_id,
            "tool": tool, "event_type": event_type, "outcome": outcome, "reason_code": reason,
            "failure_stage": tool if outcome not in ("ATTEMPTED", "SUCCEEDED") else None,
            "request_id": safe_id(raw.get("request_id")), "correlation_id": safe_id(raw.get("correlation_id")),
            "idempotency_key": safe_id(raw.get("idempotency_key")), "journey_id": journey["id"] if journey else None,
            "journey_version": journey["version"] if journey else None,
            "actor": "MOCK_AGENT", **{key: request.get(key) for key in ("agent_id", "merchant_id", "channel", "renderer_id")},
            "versions": prepared.get("versions", {}), "offer_id": offer_id or prepared.get("versions", {}).get("offer_id"),
            "cart_digest": prepared.get("cart_digest") or (digest(request["cart"]) if request else None),
            "disclosure_digest": prepared.get("disclosure_digest"), "occurred_at": iso(now),
            "snapshot_reference": prepared.get("snapshot_id"),
            "evidence_reference": journey.get("receipt", {}).get("payload", {}).get("receipt_id") if journey else None}
        previous = connection.execute("SELECT event_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev_hash = previous[0] if previous else "0" * 64
        event_hash = digest({"previous_event_hash": prev_hash, "event": event})
        connection.execute("INSERT INTO audit(event_id,invocation_id,journey_id,event_type,outcome,occurred_at,payload,previous_event_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?)",
            (event["event_id"], invocation_id, event["journey_id"], event_type, outcome, event["occurred_at"], canonical(event), prev_hash, event_hash))
        return event["event_id"]

    def verify_chain(self, connection):
        previous = "0" * 64
        for row in connection.execute("SELECT payload,previous_event_hash,event_hash FROM audit ORDER BY seq"):
            if row["previous_event_hash"] != previous or digest({"previous_event_hash": previous, "event": json.loads(row["payload"])}) != row["event_hash"]:
                return False
            previous = row["event_hash"]
        return True
