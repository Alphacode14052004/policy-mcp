from offerproof.models.contracts import Block

TRANSITIONS = {
    "STARTED": {"OFFERS_EVALUATED"}, "OFFERS_EVALUATED": {"DISCLOSURE_ISSUED"},
    "DISCLOSURE_ISSUED": {"DISCLOSURE_PRESENTED", "DECLINED", "EXPIRED"},
    "DISCLOSURE_PRESENTED": {"ACKNOWLEDGED", "AUTHORIZED", "DECLINED", "EXPIRED"},
    "ACKNOWLEDGED": {"AUTHORIZED", "DECLINED", "EXPIRED"},
    "AUTHORIZED": set(), "DECLINED": set(), "EXPIRED": set(), "INVALIDATED": set(),
}


def transition(journey, target):
    if target not in TRANSITIONS[journey["state"]]:
        raise Block("INVALID_STATE_TRANSITION")
    journey["state"] = target
    journey["version"] += 1


def invalidate(journey, reason, *, restart=False):
    journey["state"] = "INVALIDATED" if restart else "OFFERS_EVALUATED"
    journey["version"] += 1
    journey["block_reason"] = reason
    for key in ("prepared", "presentation", "receipt", "acknowledgment", "acknowledged_at", "issued_at", "authorization"):
        journey.pop(key, None)
