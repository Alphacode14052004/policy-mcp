"""Audited transaction boundary and transport-independent five-tool workflow."""
import copy
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from offerproof.audit.events import ATTEMPTS, SUCCESS
from offerproof.audit.store import AuditStore, safe_id
from offerproof.config import APP_VERSION, DATA, RUNTIME, SYNTHETIC
from offerproof.core import disclosures
from offerproof.core.eligibility import allocation_reconciles, cart_summary, evaluate, validate_cart
from offerproof.core.recommendation import recommend
from offerproof.core.state_machine import invalidate, transition
from offerproof.models.contracts import Block, SCHEMAS, validate_request
from offerproof.repositories.json_repository import JsonRepository
from offerproof.repositories.sqlite_repository import SQLiteRepository
from offerproof.security.digests import canonical, digest, instant, iso, utcnow
from offerproof.security.receipts import ReceiptSigner

LOG = logging.getLogger("offerproof")
TERMINAL = {"AUTHORIZED", "DECLINED", "EXPIRED", "INVALIDATED"}
COMPARISON_GUIDANCE = ("Before asking for a selection, show every eligible offer's disclosure_preview.canonical_text verbatim, "
    "payment schedule and warnings. Selection means review, not acceptance. Then ask which offer to review and confirm "
    "any applied gift-card payment and excluded balance disposition. Final disclosure, presentation and acknowledgment are separate steps.")


class OfferProof:
    def __init__(self, data_path=DATA, runtime=RUNTIME, clock=utcnow):
        self.clock = clock
        self.repo = JsonRepository(Path(data_path), clock)
        self.reasons = {r["id"]: r for r in self.repo.all("reason-codes")}
        self.store = SQLiteRepository(Path(runtime) / "offerproof.sqlite3")
        self.audit = AuditStore()
        self.signer = ReceiptSigner(Path(runtime) / "receipt.key")

    def action(self, tool, instruction="Follow the authoritative next action.", fields=None):
        return {"tool": tool, "required_inputs": fields if fields is not None else SCHEMAS.get(tool, {}).get("required", []),
                "instruction": instruction}

    def next_action(self, journey, code="OK"):
        terminal_recoveries = {"POLICY_REVIEW_REQUIRED", "PROHIBITED_SENSITIVE_DATA", "SCHEMA_VALIDATION_FAILED",
            "AUTHORITATIVE_NOTICE_FLOW_REQUIRED", "AUDIT_UNAVAILABLE", "UNSUPPORTED_CURRENCY", "UNSUPPORTED_LOCALE",
            "IDENTITY_BINDING_MISMATCH", "PRESENTATION_CAPABILITY_UNSUPPORTED", "IDEMPOTENCY_CONFLICT", "INTERNAL_ERROR",
            "PRODUCT_NOT_CONFIGURED", "TENDER_ALLOCATION_INVALID", "TENDER_POLICY_UNSUPPORTED"}
        if code in terminal_recoveries:
            return self.action(self.reasons[code]["recovery"], self.reasons[code]["message"])
        if code in {"CART_DIGEST_MISMATCH", "OFFER_VERSION_CHANGED", "OFFER_EXPIRED"}:
            return self.action("start_offer_journey", "Reevaluate the current cart with a new idempotency key; old evidence is invalid.")
        if not journey:
            return self.action("start_offer_journey", "For a new cart, start here. Supply only synthetic cart/context data.")
        state = journey["state"]
        if state == "OFFERS_EVALUATED":
            if not any(item["eligible"] for item in journey["evaluations"]):
                return self.action("END_NO_PROMOTION", "No configured offer can finance this cart. Explain standard terms through the authoritative separate checkout flow.")
            if any(item["eligible"] and "disclosure_preview" not in item for item in journey["evaluations"]):
                return self.action("start_offer_journey", "This saved comparison predates disclosure previews. Start a new journey with a fresh idempotency key to show the disclosures before offer selection.")
            return self.action("prepare_offer_disclosure", COMPARISON_GUIDANCE)
        if state == "DISCLOSURE_ISSUED":
            return self.action("record_disclosure_outcome", "Display canonical_text exactly FIRST. Capture the actual renderer event, then submit PRESENTED with a fresh idempotency key. Read issued_at, server_time and any result.presentation_error for diagnosis; never guess or copy those times as evidence. If the host cannot capture presentation, report that limitation and stop before acknowledgment.")
        if state == "DISCLOSURE_PRESENTED":
            if journey["prepared"]["presentation_requirements"]["acknowledgment_required"]:
                return self.action("record_disclosure_outcome", "Ask for affirmative acknowledgment after displaying the final disclosure. Submit ACKNOWLEDGED with the same accepted presentation evidence and the actual consumer event timestamp. Do not invent or copy server timestamps. On a block, inspect result.presentation_error and use a fresh idempotency key for corrected event evidence.")
            return self.action("authorize_promotional_checkout", "Submit unchanged cart/context and the signed presentation receipt.")
        if state == "ACKNOWLEDGED":
            return self.action("authorize_promotional_checkout", "Submit unchanged cart/context and the signed acknowledgment receipt. This is a mock authorization, not payment.")
        if state == "AUTHORIZED":
            return self.action("END_AUTHORIZED", "Mock authorization is complete. Do not replay it under another idempotency key.")
        if state == "DECLINED":
            return self.action("END_DECLINED", "Respect the consumer's decline. This journey is closed.")
        return self.action("start_offer_journey", "Start a new journey; this journey cannot advance.")

    def envelope(self, payload, journey=None, *, code="OK", result=None, recovery=None):
        reason = self.reasons.get(code, self.reasons["INTERNAL_ERROR"])
        status = "COMPLETED" if code in {"OK", "DECLINED", "EXPIRED"} else "BLOCKED"
        if code in {"ALLOCATION_CONFIRMATION_REQUIRED", "APPLIED_TENDER_CONFIRMATION_REQUIRED", "ACKNOWLEDGMENT_REQUIRED", "NO_ELIGIBLE_PROMOTION"}:
            status = "INPUT_REQUIRED"
        raw = payload if isinstance(payload, dict) else {}
        request_id = safe_id(raw.get("request_id")) or "request-" + uuid.uuid4().hex
        return {"status": status, "journey_id": journey["id"] if journey else None,
            "server_time": iso(self.clock()),
            "journey_state": journey["state"] if journey else "NONE", "journey_version": journey["version"] if journey else 0,
            "reason_code": code, "message": reason["message"], "result": result or {},
            "next_action": self.action(recovery, reason["message"]) if recovery else self.next_action(journey, code),
            "request_id": request_id, "correlation_id": safe_id(raw.get("correlation_id")) or request_id,
            "warning": SYNTHETIC, "code": "offerproof." + code.lower(), "trackingId": request_id,
            "transient": code == "AUDIT_UNAVAILABLE"}

    def invoke(self, tool, payload):
        invocation = "invocation-" + uuid.uuid4().hex
        raw = payload if isinstance(payload, dict) else {}
        audit_payload = {"request_id": safe_id(raw.get("request_id")) or invocation,
            "correlation_id": safe_id(raw.get("correlation_id")) or invocation,
            "idempotency_key": safe_id(raw.get("idempotency_key"))}
        logged_tool = tool if tool in SCHEMAS else "UNKNOWN_TOOL"
        journey, original, cacheable, cached = None, None, False, False
        extra_events = []
        try:
            with self.store.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                self.audit.append(connection, invocation_id=invocation, tool=logged_tool, payload=audit_payload,
                    event_type=ATTEMPTS.get(tool, "UNKNOWN_TOOL_ATTEMPTED"), outcome="ATTEMPTED", reason="OK", now=self.clock())
                connection.commit()
            with self.store.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    if tool not in SCHEMAS:
                        raise Block("SCHEMA_VALIDATION_FAILED")
                    validate_request(tool, payload)
                    if tool != "start_offer_journey":
                        journey = self.store.load(connection, payload["journey_id"])
                        if journey is None:
                            raise Block("INVALID_STATE_TRANSITION")
                        if any(payload[key] != journey["request"][key] for key in ("merchant_id", "agent_id")):
                            journey = None
                            raise Block("IDENTITY_BINDING_MISMATCH")
                        original = copy.deepcopy(journey)
                    mutating = tool != "get_offer_journey_status"
                    if mutating:
                        request_digest = digest({"tool": tool, "payload": {k: v for k, v in payload.items() if k not in ("request_id", "correlation_id")}})
                        previous = connection.execute("SELECT payload_digest,response FROM idempotency WHERE merchant=? AND agent=? AND key=?",
                            (payload["merchant_id"], payload["agent_id"], payload["idempotency_key"])).fetchone()
                        if previous:
                            if previous["payload_digest"] != request_digest:
                                raise Block("IDEMPOTENCY_CONFLICT")
                            response, cached = json.loads(previous["response"]), True
                            if journey is None and response["journey_id"]:
                                journey = self.store.load(connection, response["journey_id"])
                        else:
                            cacheable = True
                    if not cached:
                        if journey and mutating and payload["expected_version"] != journey["version"]:
                            raise Block("STALE_JOURNEY_VERSION")
                        if tool != "get_offer_journey_status":
                            try:
                                self.repo.reload()
                            except Block:
                                if journey and journey["state"] not in TERMINAL:
                                    invalidate(journey, "POLICY_REVIEW_REQUIRED", restart=True)
                                    self.mark(journey, "POLICY_REVIEW_REQUIRED")
                                raise
                        journey, result, code, extra_events = self.dispatch(tool, payload, journey)
                        response = self.envelope(payload, journey, code=code, result=result)
                except Block as failure:
                    response = self.envelope(payload, journey, code=failure.code, recovery=failure.recovery, result=failure.result)
                except Exception:
                    # Roll back any partial in-memory transition; never expose exception text.
                    journey = original
                    response = self.envelope(payload, journey, code="INTERNAL_ERROR")
                    LOG.error("offerproof.internal_error invocation=%s", invocation)
                if not cached:
                    response.update(request_id=audit_payload["request_id"], correlation_id=audit_payload["correlation_id"], trackingId=audit_payload["request_id"])
                if journey and not cached:
                    self.store.save(connection, journey)
                    if tool == "prepare_offer_disclosure" and response["status"] == "COMPLETED":
                        prepared = journey["prepared"]
                        connection.execute("INSERT INTO disclosure_snapshots(snapshot_id,journey_id,disclosure_digest,body) VALUES(?,?,?,?)",
                            (prepared["snapshot_id"], journey["id"], prepared["disclosure_digest"], canonical(prepared)))
                if cacheable:
                    connection.execute("INSERT INTO idempotency(merchant,agent,key,payload_digest,response) VALUES(?,?,?,?,?)",
                        (payload["merchant_id"], payload["agent_id"], payload["idempotency_key"], request_digest, canonical(response)))
                code = response["reason_code"]
                for event_type in extra_events:
                    offer_id = None
                    if isinstance(event_type, dict):
                        offer_id, event_type = event_type["offer_id"], event_type["event_type"]
                    self.audit.append(connection, invocation_id=invocation, tool=logged_tool, payload=audit_payload,
                        event_type=event_type, outcome="SUCCEEDED", reason=code, now=self.clock(), journey=journey, offer_id=offer_id)
                outcome = "SUCCEEDED" if response["status"] == "COMPLETED" else "BLOCKED"
                if code in ("DECLINED", "EXPIRED"):
                    outcome = code
                if code == "INTERNAL_ERROR":
                    outcome = "FAILED"
                event = "IDEMPOTENT_RETRY_RETURNED" if cached else SUCCESS.get(tool, "SYSTEM_ERROR")
                if response["status"] != "COMPLETED":
                    event = "DISCLOSURE_PRESENTATION_FAILED" if tool == "record_disclosure_outcome" else "PROMOTION_BLOCKED"
                self.audit.append(connection, invocation_id=invocation, tool=logged_tool, payload=audit_payload,
                    event_type=event, outcome=outcome, reason=code, now=self.clock(), journey=journey)
                connection.commit()
                return response
        except (sqlite3.Error, OSError):
            LOG.error("offerproof.audit_unavailable invocation=%s", invocation)
            return self.envelope({}, code="AUDIT_UNAVAILABLE")

    def dispatch(self, tool, payload, journey):
        if tool == "start_offer_journey":
            return self.start(payload)
        if tool == "get_offer_journey_status":
            return journey, self.summary(journey), "OK", []
        if tool == "prepare_offer_disclosure":
            return self.prepare(payload, journey)
        if tool == "record_disclosure_outcome":
            return self.record(payload, journey)
        return self.authorize(payload, journey)

    def start(self, payload):
        request = {k: copy.deepcopy(v) for k, v in payload.items() if k not in ("idempotency_key", "request_id", "correlation_id")}
        request["cart"] = validate_cart(request["cart"], self.repo)
        terms, policy, _ = disclosures.resolve_context(request, self.repo)
        evaluated = self.compare(request, terms, policy)
        journey = {"id": "journey-" + uuid.uuid4().hex, "version": 0, "state": "STARTED", "request": request,
            "created_at": iso(self.clock()), "evaluations": evaluated, "timeline": []}
        transition(journey, "OFFERS_EVALUATED")
        self.mark(journey, "ELIGIBILITY_EVALUATED", digest(request["cart"]))
        any_promo = any(r["eligible"] and r["plan_type"] != "STANDARD_REVOLVING" for r in evaluated)
        result = {"server_version": APP_VERSION, **cart_summary(request["cart"]), "offers": evaluated,
            "recommendation": recommend(evaluated, request.get("preferences"), self.repo),
            "policy": {k: v for k, v in policy.items() if k not in ("bundle", "profile")},
            "standard_fallback": next(r for r in evaluated if r["plan_type"] == "STANDARD_REVOLVING"),
            "allocation_note": "Gift cards being purchased are excluded products. Existing gift cards used as payment belong in applied_tenders. Mock thresholds use eligible balance AFTER applied tender; this is not a real merchant rule. Confirm both any applied payment and any excluded balance disposition. No actual gift-card redemption occurs.",
            "presentation_guidance": COMPARISON_GUIDANCE + " Also show threshold failures, including EPP-12-0APR. A recommendation does not prove an offer is safer or cheaper.",
            "comparison_only": True, "selection_is_acceptance": False}
        events = ["JOURNEY_STARTED"] + [{"event_type": "OFFER_ELIGIBLE" if r["eligible"] else "OFFER_INELIGIBLE", "offer_id": r["offer_id"]} for r in evaluated]
        events += [{"event_type": "DISCLOSURE_PREVIEW_GENERATED", "offer_id": r["offer_id"]} for r in evaluated if r["eligible"]]
        return journey, result, "OK" if any_promo else "NO_ELIGIBLE_PROMOTION", events

    def compare(self, request, terms, policy):
        evaluated = evaluate(request["cart"], request, terms, policy, self.repo)
        for item in evaluated:
            if item["eligible"]:
                offer = self.repo.active(self.repo.get("offers", item["offer_id"]), "OFFER_EXPIRED")
                item["disclosure_preview"] = disclosures.preview(request, item, offer, self.repo)
        return evaluated

    def prepare(self, payload, journey):
        if journey["state"] != "OFFERS_EVALUATED":
            raise Block("INVALID_STATE_TRANSITION")
        if any(item["eligible"] and "disclosure_preview" not in item for item in journey["evaluations"]):
            raise Block("INVALID_STATE_TRANSITION", recovery="start_offer_journey")
        request = journey["request"]
        validate_cart(request["cart"], self.repo)
        terms, policy, _ = disclosures.resolve_context(request, self.repo)
        evaluated = self.compare(request, terms, policy)
        selected = next((r for r in evaluated if r["offer_id"] == payload["offer_id"]), None)
        if selected is None:
            raise Block("SCHEMA_VALIDATION_FAILED")
        if not selected["eligible"]:
            raise Block(selected["reason_codes"][0])
        allocation = copy.deepcopy(selected["allocation"])
        if allocation["applied_tender_confirmation_required"]:
            confirmation = payload.get("applied_tender_confirmation")
            if not confirmation or not confirmation["confirmed"] or confirmation["applied_tender_cents"] != allocation["applied_tender_cents"]:
                raise Block("APPLIED_TENDER_CONFIRMATION_REQUIRED")
            allocation["applied_tender_confirmation_required"] = False
            allocation["applied_tender_confirmed_by"] = "CONSUMER"
        elif payload.get("applied_tender_confirmation"):
            raise Block("TENDER_ALLOCATION_INVALID")
        if allocation["confirmation_required"]:
            confirmation = payload.get("allocation_confirmation")
            if not confirmation or not confirmation["confirmed"]:
                raise Block("ALLOCATION_CONFIRMATION_REQUIRED")
            # This demo supports separate tender only. Standard revolving would
            # require a second accepted terms/evidence path, deliberately absent.
            if confirmation["excluded_disposition"] != "SEPARATE_TENDER":
                raise Block("ALLOCATION_CONFIRMATION_REQUIRED", recovery="CONFIRM_SEPARATE_TENDER")
            allocation["excluded_disposition"] = "SEPARATE_TENDER"
            allocation["confirmation_required"] = False
            allocation["confirmed_by"] = "CONSUMER"
        if not allocation_reconciles(allocation, request["cart"]):
            raise Block("SCHEMA_VALIDATION_FAILED")
        offer = self.repo.active(self.repo.get("offers", payload["offer_id"]), "OFFER_EXPIRED")
        prepared = disclosures.prepare(request, selected, offer, allocation, self.repo)
        prepared["snapshot_id"] = "snapshot-" + uuid.uuid4().hex
        issued_at = iso(self.clock())
        prepared["issued_at"] = issued_at
        journey.update({"prepared": prepared, "issued_at": issued_at, "evaluations": evaluated})
        journey.pop("block_reason", None)
        transition(journey, "DISCLOSURE_ISSUED")
        self.mark(journey, "DISCLOSURE_ISSUED", prepared["disclosure_digest"])
        return journey, prepared, "OK", []

    def stale(self, journey, code, restart=False, *, result=None):
        if journey["state"] not in TERMINAL:
            invalidate(journey, code, restart=restart)
            self.mark(journey, code)
        raise Block(code, result=result)

    def fresh(self, journey):
        if "prepared" not in journey:
            raise Block("INVALID_STATE_TRANSITION")
        old, request = journey["prepared"], journey["request"]
        offer = self.repo.get("offers", old["versions"]["offer_id"])
        try:
            self.repo.active(offer, "OFFER_EXPIRED")
        except Block:
            self.stale(journey, "OFFER_EXPIRED", True)
        terms, policy, renderer = disclosures.resolve_context(request, self.repo)
        disclosure = self.repo.active(self.repo.get("disclosures", offer["disclosure_id"]))
        current = disclosures.versions(request, offer, terms, policy, disclosure, renderer, self.repo)
        for component, code in [("terms", "TERMS_VERSION_CHANGED"), ("policy", "POLICY_VERSION_CHANGED"),
                ("profile", "POLICY_VERSION_CHANGED"), ("disclosure", "DISCLOSURE_DIGEST_MISMATCH"),
                ("renderer", "DISCLOSURE_DIGEST_MISMATCH"), ("offer", "OFFER_VERSION_CHANGED"),
                ("merchant", "OFFER_VERSION_CHANGED"), ("products", "OFFER_VERSION_CHANGED")]:
            if current[component] != old["record_digests"][component]:
                self.stale(journey, code, code == "OFFER_VERSION_CHANGED")
        validate_cart(request["cart"], self.repo)
        evaluated = evaluate(request["cart"], request, terms, policy, self.repo)
        if not next(r for r in evaluated if r["offer_id"] == offer["id"])["eligible"]:
            self.stale(journey, "OFFER_VERSION_CHANGED", True)

    def record(self, payload, journey):
        if journey["state"] not in {"DISCLOSURE_ISSUED", "DISCLOSURE_PRESENTED", "ACKNOWLEDGED"}:
            raise Block("INVALID_STATE_TRANSITION")
        self.fresh(journey)
        prepared = journey["prepared"]
        if payload["renderer_id"] != journey["request"]["renderer_id"]:
            raise Block("IDENTITY_BINDING_MISMATCH")
        if payload["cart_digest"] != prepared["cart_digest"]:
            raise Block("CART_DIGEST_MISMATCH")
        if payload["disclosure_digest"] != prepared["disclosure_digest"]:
            raise Block("DISCLOSURE_DIGEST_MISMATCH")
        outcome, now = payload["outcome"], self.clock()
        if outcome == "PRESENTATION_FAILED":
            disclosures.presentation_failure("RENDERER_REPORTED_FAILURE", "outcome",
                "The caller reported that presentation failed. Do not acknowledge; use a renderer that can display and capture the required evidence.",
                journey["issued_at"], now)
        if outcome in ("DECLINED", "EXPIRED"):
            transition(journey, outcome)
            journey.pop("receipt", None)
            self.mark(journey, outcome)
            return journey, {"outcome": outcome}, outcome, [outcome]
        if journey.get("presentation") and (now - instant(journey["presentation"]["rendered_at"])).total_seconds() > disclosures.MAX_PRESENTATION_AGE_SECONDS:
            try:
                disclosures.verify_presentation(journey["presentation"], prepared, journey["issued_at"], now)
            except Block as failure:
                self.stale(journey, failure.code, result=failure.result)
        disclosures.verify_presentation(payload["evidence"], prepared, journey["issued_at"], now)
        if outcome == "PRESENTED":
            if journey["state"] != "DISCLOSURE_ISSUED":
                raise Block("INVALID_STATE_TRANSITION")
            journey["presentation"] = copy.deepcopy(payload["evidence"])
            transition(journey, "DISCLOSURE_PRESENTED")
            self.mark(journey, "PRESENTATION_VERIFIED", prepared["disclosure_digest"])
            if not prepared["presentation_requirements"]["acknowledgment_required"]:
                journey["receipt"] = self.signer.issue(journey, now)
            return journey, {"evidence_label": "MOCK_RENDERER_ATTESTATION", "receipt": journey.get("receipt")}, "OK", []
        if journey["state"] != "DISCLOSURE_PRESENTED":
            raise Block("DISCLOSURE_NOT_PRESENTED")
        if payload["evidence"] != journey["presentation"]:
            disclosures.presentation_failure("ACCEPTED_PRESENTATION_CHANGED", "evidence",
                "Acknowledgment must reference the exact previously accepted renderer event, including its timestamp.",
                journey["issued_at"], now)
        acknowledgment = payload.get("acknowledgment")
        if not acknowledgment or not acknowledgment["affirmative_action"]:
            raise Block("ACKNOWLEDGMENT_REQUIRED")
        disclosures.verify_acknowledgment_timing(acknowledgment, journey["presentation"], journey["issued_at"], now)
        journey["acknowledged_at"] = acknowledgment["captured_at"]
        journey["acknowledgment"] = copy.deepcopy(acknowledgment)
        transition(journey, "ACKNOWLEDGED")
        journey["receipt"] = self.signer.issue(journey, now)
        self.mark(journey, "ACKNOWLEDGMENT_RECEIVED", journey["receipt"]["payload"]["receipt_id"])
        return journey, {"receipt": journey["receipt"], "evidence_label": "MOCK_RENDERER_ATTESTATION"}, "OK", ["ACKNOWLEDGMENT_RECEIVED"]

    def authorize(self, payload, journey):
        cart = validate_cart(payload["cart"], self.repo)
        if digest(cart) != digest(journey["request"]["cart"]):
            self.stale(journey, "CART_DIGEST_MISMATCH", True)
        if payload["jurisdiction"] != journey["request"]["jurisdiction"]:
            self.stale(journey, "POLICY_REVIEW_REQUIRED", True)
        if journey["state"] in TERMINAL:
            raise Block("INVALID_STATE_TRANSITION")
        if journey["state"] == "OFFERS_EVALUATED":
            raise Block("INVALID_STATE_TRANSITION")
        self.fresh(journey)
        if payload["offer_id"] != journey["prepared"]["versions"]["offer_id"]:
            raise Block("RECEIPT_INVALID")
        if journey["state"] == "DISCLOSURE_ISSUED":
            raise Block("DISCLOSURE_NOT_PRESENTED")
        if journey["state"] == "DISCLOSURE_PRESENTED" and journey["prepared"]["presentation_requirements"]["acknowledgment_required"]:
            raise Block("ACKNOWLEDGMENT_REQUIRED")
        if "receipt" not in payload:
            raise Block("RECEIPT_INVALID")
        try:
            self.signer.verify(payload["receipt"], journey, self.clock())
        except Block as error:
            if error.code == "RECEIPT_EXPIRED":
                self.stale(journey, error.code)
            raise
        disclosures.verify_presentation(journey["presentation"], journey["prepared"], journey["issued_at"], self.clock())
        allocation = journey["prepared"]["allocation"]
        if allocation["confirmation_required"] or not allocation_reconciles(allocation, cart):
            raise Block("ALLOCATION_CONFIRMATION_REQUIRED")
        transition(journey, "AUTHORIZED")
        journey["authorization"] = {"authorization_id": "authorization-" + uuid.uuid4().hex,
            "authorized_at": iso(self.clock()), "decision": "MOCK_PROMOTIONAL_AUTHORIZATION", "payment_processed": False}
        self.mark(journey, "PROMOTION_AUTHORIZED", journey["authorization"]["authorization_id"])
        return journey, {**journey["authorization"], "receipt": journey["receipt"], "offer_trust_passport": self.passport(journey)}, "OK", []

    def mark(self, journey, event, reference=None):
        journey["timeline"].append({"event": event, "at": iso(self.clock()), "version": journey["version"], "reference": reference})

    def passport(self, journey):
        return {"title": "Synthetic Offer Trust Passport", "journey_id": journey["id"], "timeline": journey["timeline"],
            "versions": journey.get("prepared", {}).get("versions", {}),
            "cart_digest": digest(journey["request"]["cart"]),
            "disclosure_digest": journey.get("prepared", {}).get("disclosure_digest"),
            "receipt_id": journey.get("receipt", {}).get("payload", {}).get("receipt_id"),
            "evidence_limit": "Mock renderer attestation; no authenticated human proof or blockchain claim."}

    def summary(self, journey):
        prepared = copy.deepcopy(journey.get("prepared"))
        issued_at = journey.get("issued_at")
        if prepared is not None and issued_at:
            # Expose older issued journeys without rewriting their immutable snapshots.
            prepared["issued_at"] = issued_at
        return {"server_version": APP_VERSION, **cart_summary(journey["request"]["cart"]), "offers": journey["evaluations"],
            "issued_at": issued_at,
            "presentation_timing": disclosures.presentation_timing(issued_at, self.clock()) if issued_at else None,
            "presentation_guidance": self.next_action(journey)["instruction"],
            "comparison_only": journey["state"] == "OFFERS_EVALUATED", "selection_is_acceptance": False,
            "block_reason": journey.get("block_reason"), "prepared": prepared,
            "presentation": journey.get("presentation"), "receipt": journey.get("receipt"),
            "authorization": journey.get("authorization"), "offer_trust_passport": self.passport(journey)}
