import hashlib
import json
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utcnow():
    return datetime.now(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return result


def normalized_cart(cart):
    # Display prose never persists or influences a financial decision.
    result = {k: v for k, v in cart.items() if k != "lines"}
    result["lines"] = sorted(
        [{k: v for k, v in line.items() if k not in ("title", "description")} for line in cart["lines"]],
        key=lambda line: line["line_id"],
    )
    if cart.get("applied_tenders"):
        result["applied_tenders"] = sorted(
            [{**tender, "line_allocations": sorted(tender["line_allocations"], key=lambda a: a["line_id"])}
             for tender in cart["applied_tenders"]], key=lambda t: t["tender_id"])
    else:
        result.pop("applied_tenders", None)
    return result
