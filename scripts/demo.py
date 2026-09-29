"""Deterministic fixture driver. Not a natural-language or human-consent test."""
import argparse
import copy
import json
import sys
import tempfile
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from offerproof.config import ROOT
from offerproof.core.orchestration import OfferProof
from offerproof.security.digests import iso, utcnow


def fixture():
    return json.loads((ROOT / "demo-data" / "mixed-cart.json").read_text(encoding="utf-8"))


def common(start, response, suffix):
    return {"merchant_id": start["merchant_id"], "agent_id": start["agent_id"],
        "request_id": "request-" + suffix, "correlation_id": start["correlation_id"],
        "journey_id": response["journey_id"], "expected_version": response["journey_version"],
        "idempotency_key": "key-" + suffix}


def evidence(prepared, now):
    req = prepared["presentation_requirements"]
    return {"attestation_type": "MOCK_RENDERER_ATTESTATION", "rendered_at": iso(now),
        "locale": req["locale"], "channel": req["channel"], "renderer_version": req["renderer_version"],
        "viewport": "CHAT", "required_sections_shown": req["required_sections"],
        "protected_text_digest": prepared["disclosure_digest"], "placement_order": req["placement_order"],
        "prominence_checks": req["prominence_checks"], "a11y_checks": req["a11y_checks"],
        "visible_duration_ms": req["minimum_visible_ms"], "scroll_visibility_attested": True}


def run(service, clock=utcnow, start_request=None):
    start = copy.deepcopy(start_request) if start_request is not None else fixture()
    nonce = uuid.uuid4().hex
    start["idempotency_key"] += "-" + nonce
    responses = []
    def invoke(tool, data):
        result = service.invoke(tool, data)
        responses.append({"tool": tool, "response": result})
        if result["reason_code"] != "OK":
            raise RuntimeError("Demo step blocked: " + result["reason_code"])
        return result
    r = invoke("start_offer_journey", start)
    preparation = {**common(start, r, nonce + "prepare"), "offer_id": "DI-6M",
        "allocation_confirmation": {"confirmed": True, "excluded_disposition": "SEPARATE_TENDER", "confirmed_by": "CONSUMER"}}
    if r["result"]["applied_tender_cents"]:
        preparation["applied_tender_confirmation"] = {"confirmed": True,
            "applied_tender_cents": r["result"]["applied_tender_cents"], "confirmed_by": "CONSUMER"}
    r = invoke("prepare_offer_disclosure", preparation)
    prepared = r["result"]
    attestation = evidence(prepared, clock())
    record = {"renderer_id": start["renderer_id"], "cart_digest": prepared["cart_digest"],
        "disclosure_digest": prepared["disclosure_digest"], "evidence": attestation}
    r = invoke("record_disclosure_outcome", {**common(start, r, nonce + "present"), **record, "outcome": "PRESENTED"})
    r = invoke("record_disclosure_outcome", {**common(start, r, nonce + "ack"), **record, "outcome": "ACKNOWLEDGED",
        "acknowledgment": {"actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-EVENT-ACK",
                           "captured_at": iso(clock()), "affirmative_action": True}})
    auth = {**common(start, r, nonce + "auth"), "cart": start["cart"], "jurisdiction": start["jurisdiction"],
        "offer_id": "DI-6M", "receipt": r["result"]["receipt"]}
    r = invoke("authorize_promotional_checkout", auth)
    changed = copy.deepcopy(auth)
    changed.update(common(start, r, nonce + "changed"))
    changed["cart"]["lines"][0]["unit_price_cents"] += 100
    changed["cart"]["total_cents"] += 100
    blocked = service.invoke("authorize_promotional_checkout", changed)
    assert blocked["reason_code"] == "CART_DIGEST_MISMATCH"
    return {"label": "AUTOMATED SYNTHETIC FIXTURE; NO HUMAN CONSENT OR LIVE LLM REHEARSAL", "steps": responses,
            "changed_cart_replay": blocked, "success": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--scenario", choices=["mixed-cart", "sofa-gift-card-redemption"], default="mixed-cart")
    parser.add_argument("--preview-only", action="store_true", help="Evaluate and return all disclosure previews, without selecting an offer or simulating consent.")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="offerproof-demo-") as temporary:
        start = json.loads((ROOT / "demo-data" / f"{args.scenario}.json").read_text(encoding="utf-8"))
        service = OfferProof(runtime=args.runtime or Path(temporary))
        if args.preview_only:
            start["idempotency_key"] += "-" + uuid.uuid4().hex
            response = service.invoke("start_offer_journey", start)
            result = {"label": "AUTOMATED SYNTHETIC COMPARISON; NO SELECTION, CONSENT OR AUTHORIZATION",
                "steps": [{"tool": "start_offer_journey", "response": response}], "comparison_only": True,
                "success": response["reason_code"] in {"OK", "NO_ELIGIBLE_PROMOTION"}}
        else:
            result = run(service, start_request=start)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.preview_only:
        print(json.dumps({"success": result["success"], "comparison_only": True,
            "journey_state": response["journey_state"], "server_version": response["result"].get("server_version"),
            "disclosure_previews": sum("disclosure_preview" in o for o in response["result"].get("offers", []))}))
        if not result["success"]:
            raise SystemExit(1)
    else:
        print(json.dumps({"success": result["success"], "authorization": result["steps"][-1]["response"]["result"]["decision"],
                          "changed_cart_replay": result["changed_cart_replay"]["reason_code"]}))
