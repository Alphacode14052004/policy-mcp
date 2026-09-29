import hashlib
import hmac
import os
import secrets
import uuid
from datetime import timedelta
from offerproof.models.contracts import Block
from offerproof.security.digests import canonical, digest, instant, iso


class ReceiptSigner:
    def __init__(self, key_path):
        key_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(secrets.token_bytes(32))
                stream.flush()
                os.fsync(stream.fileno())
        self._key = key_path.read_bytes()
        if len(self._key) != 32:
            raise ValueError("Invalid demo signing key")

    def signature(self, payload):
        return hmac.new(self._key, canonical(payload).encode("utf-8"), hashlib.sha256).hexdigest()

    def bindings(self, journey):
        request, prepared = journey["request"], journey["prepared"]
        fields = ("offer_id", "offer_version", "terms_id", "terms_version", "policy_id", "policy_version",
            "disclosure_id", "disclosure_version", "presentation_policy_id", "presentation_policy_version")
        return {"journey_id": journey["id"], "merchant_id": request["merchant_id"], "agent_id": request["agent_id"],
            **{key: prepared["versions"][key] for key in fields}, "cart_digest": prepared["cart_digest"],
            "disclosure_digest": prepared["disclosure_digest"], "allocation_digest": digest(prepared["allocation"]),
            "context_digest": digest(request["jurisdiction"]), "versions_digest": digest(prepared["record_digests"]),
            "presented_at": journey["presentation"]["rendered_at"], "acknowledged_at": journey.get("acknowledged_at"),
            "locale": request["locale"], "channel": request["channel"], "renderer_id": request["renderer_id"],
            "renderer_version": prepared["presentation_requirements"]["renderer_version"]}

    def issue(self, journey, now):
        expires = min(now + timedelta(minutes=15), instant(journey["prepared"]["valid_until"]))
        payload = {**self.bindings(journey), "receipt_id": "receipt-" + uuid.uuid4().hex, "expires_at": iso(expires)}
        return {"payload": payload, "signature": self.signature(payload)}

    def verify(self, receipt, journey, now):
        payload = receipt["payload"]
        if not hmac.compare_digest(self.signature(payload), receipt["signature"]):
            raise Block("RECEIPT_INVALID")
        if instant(payload["expires_at"]) <= now:
            raise Block("RECEIPT_EXPIRED")
        if any(payload.get(key) != value for key, value in self.bindings(journey).items()):
            raise Block("RECEIPT_INVALID")
        if journey.get("receipt") != receipt:
            raise Block("RECEIPT_INVALID")
