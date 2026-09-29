"""JSON Schemas shared by domain validation, SDK discovery and documentation.

Validation is deliberately performed inside the audited application boundary.
"""
import re
from offerproof.config import MAX_PAYLOAD_BYTES
from offerproof.security.digests import canonical, instant


class Block(Exception):
    def __init__(self, code, *, recovery=None, result=None):
        super().__init__(code)
        self.code, self.recovery = code, recovery
        self.result = result


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def string(maximum=100, pattern=None, enum=None):
    value = {"type": "string", "minLength": 1, "maxLength": maximum}
    if pattern:
        value["pattern"] = pattern
    if enum is not None:
        value["enum"] = enum
    return value


def integer(minimum=0, maximum=100000000):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


def array(items, maximum=50, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


ID = string(80, r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
MOCK_ID = string(80, r"^MOCK-[A-Z0-9-]+$")
HASH = string(64, r"^[a-f0-9]{64}$")
TIME = {**string(40), "format": "date-time"}
BOOL = {"type": "boolean"}
LINE = obj({"line_id": ID, "sku": MOCK_ID, "category": ID, "item_type": ID,
            "unit_price_cents": integer(1), "quantity": integer(1, 100),
            "title": string(200), "description": string(2000)},
           ["line_id", "sku", "category", "item_type", "unit_price_cents", "quantity"])
APPLIED_TENDER = obj({"tender_id": MOCK_ID, "tender_type": string(enum=["GIFT_CARD"]),
    "amount_cents": integer(1), "line_allocations": array(obj({"line_id": ID, "amount_cents": integer(1)}), 50, 1)})
CART = obj({"cart_id": MOCK_ID, "currency": string(3), "lines": array(LINE, 50, 1),
            "tax_cents": integer(), "shipping_cents": integer(), "total_cents": integer(1),
            "applied_tenders": array(APPLIED_TENDER, 10)},
           ["cart_id", "currency", "lines", "tax_cents", "shipping_cents", "total_cents"])
CART["properties"]["lines"]["description"] = "Products being purchased. A gift card being redeemed is NOT a product line."
CART["properties"]["total_cents"]["description"] = "Gross purchase total BEFORE payment tenders; must equal lines plus tax and shipping."
CART["properties"]["applied_tenders"]["description"] = "Optional existing mock gift cards used as payment, with exact line allocations. No real card numbers or balance verification."
JURISDICTION = obj({
    "profile_id": ID, "issuer_charter": ID, "issuer_location": ID,
    "product_legal_type": ID, "account_program": MOCK_ID, "origination_channel": ID,
    "merchant_location": ID, "consumer_residence_state": ID, "billing_state": ID,
    "servicemember_status_source": MOCK_ID, "servicemember_status_result": ID,
    "transaction_at": TIME,
})
PREFERENCES = obj({"avoid_surprise_interest": BOOL, "target_monthly_cents": integer(1),
                   "payoff_horizon_months": integer(1, 120), "reward_preference": BOOL}, [])
IDENTITY = {"merchant_id": MOCK_ID, "agent_id": MOCK_ID}
REQUEST = {"request_id": ID, "correlation_id": ID}
MUTATION = {**IDENTITY, **REQUEST, "journey_id": ID,
            "expected_version": integer(1), "idempotency_key": ID}
EVIDENCE = obj({
    "attestation_type": string(enum=["MOCK_RENDERER_ATTESTATION"]),
    "rendered_at": TIME, "locale": ID, "channel": ID,
    "renderer_version": ID, "viewport": string(enum=["DESKTOP", "MOBILE", "CHAT"]),
    "required_sections_shown": array(ID, 10, 1), "protected_text_digest": HASH,
    "placement_order": array(ID, 10, 1), "prominence_checks": array(ID, 10, 1),
    "a11y_checks": array(ID, 10, 1), "visible_duration_ms": integer(1, 3600000),
    "scroll_visibility_attested": BOOL,
})
EVIDENCE["properties"]["rendered_at"] = {**TIME, "description":
    "Actual UTC time captured by the renderer after displaying the issued final disclosure. Must be at or after issued_at, not in the future, and no more than 900 seconds old at validation. Never guess or copy server_time, journey creation time, preview time or issued_at as evidence."}
ACK = obj({"actor": string(enum=["CONSUMER"]), "action": string(enum=["ACKNOWLEDGE"]),
           "event_id": ID, "captured_at": TIME, "affirmative_action": BOOL})
ACK["properties"]["captured_at"] = {**TIME, "description":
    "Actual UTC time captured with the consumer's affirmative acknowledgment, after the accepted presentation and no later than server validation. Do not substitute a server-clock value for a consumer event."}
RECEIPT_PAYLOAD = obj({
    "receipt_id": ID, "journey_id": ID, **IDENTITY, "offer_id": ID,
    "terms_id": ID, "terms_version": ID, "policy_id": ID, "policy_version": ID,
    "disclosure_id": ID, "disclosure_version": ID, "offer_version": ID,
    "presentation_policy_id": ID, "presentation_policy_version": ID,
    "cart_digest": HASH, "disclosure_digest": HASH, "allocation_digest": HASH,
    "context_digest": HASH, "versions_digest": HASH, "presented_at": TIME,
    "acknowledged_at": {"anyOf": [TIME, {"type": "null"}]}, "locale": ID,
    "channel": ID, "renderer_id": ID, "renderer_version": ID, "expires_at": TIME,
})
RECEIPT = obj({"payload": RECEIPT_PAYLOAD, "signature": HASH})
SCHEMAS = {
    "start_offer_journey": obj({**IDENTITY, **REQUEST, "idempotency_key": ID,
        "cart": CART, "program_id": MOCK_ID, "channel": ID, "renderer_id": MOCK_ID,
        "locale": ID, "account_terms_id": MOCK_ID, "jurisdiction": JURISDICTION,
        "preferences": PREFERENCES},
        [*IDENTITY, *REQUEST, "idempotency_key", "cart", "program_id", "channel",
         "renderer_id", "locale", "account_terms_id", "jurisdiction"]),
    "prepare_offer_disclosure": obj({**MUTATION, "offer_id": ID,
        "allocation_confirmation": obj({"confirmed": BOOL, "excluded_disposition": string(enum=[
            "SEPARATE_TENDER", "STANDARD_REVOLVING"]), "confirmed_by": string(enum=["CONSUMER"])}),
        "applied_tender_confirmation": obj({"confirmed": BOOL, "applied_tender_cents": integer(1),
            "confirmed_by": string(enum=["CONSUMER"])})},
        [*MUTATION, "offer_id"]),
    "record_disclosure_outcome": obj({**MUTATION, "renderer_id": MOCK_ID,
        "cart_digest": HASH, "disclosure_digest": HASH,
        "outcome": string(enum=["PRESENTED", "PRESENTATION_FAILED", "DECLINED", "ACKNOWLEDGED", "EXPIRED"]),
        "evidence": EVIDENCE, "acknowledgment": ACK},
        [*MUTATION, "renderer_id", "cart_digest", "disclosure_digest", "outcome", "evidence"]),
    "authorize_promotional_checkout": obj({**MUTATION, "cart": CART, "jurisdiction": JURISDICTION,
        "offer_id": ID, "receipt": RECEIPT}, [*MUTATION, "cart", "jurisdiction", "offer_id"]),
    "get_offer_journey_status": obj({"journey_id": ID, **IDENTITY, **REQUEST},
        ["journey_id", *IDENTITY]),
}
ENVELOPE = obj({
    "status": string(enum=["COMPLETED", "BLOCKED", "INPUT_REQUIRED"]),
    "journey_id": {"anyOf": [ID, {"type": "null"}]},
    "journey_state": string(enum=["NONE", "STARTED", "OFFERS_EVALUATED", "DISCLOSURE_ISSUED",
        "DISCLOSURE_PRESENTED", "ACKNOWLEDGED", "AUTHORIZED", "DECLINED", "EXPIRED", "INVALIDATED"]),
    "journey_version": integer(), "reason_code": ID, "message": string(500),
    "result": {"type": "object"},
    "next_action": obj({"tool": ID, "required_inputs": array(ID, 30), "instruction": string(500)}),
    **REQUEST, "warning": string(500), "code": ID, "trackingId": ID, "transient": BOOL,
})
# Optional for compatibility with immutable idempotency responses saved before
# 1.3.0. Every newly constructed response includes the clock reading.
ENVELOPE["properties"]["server_time"] = {**TIME, "description":
    "UTC when this response was constructed. An idempotent replay retains its original timestamp; get_offer_journey_status returns a fresh clock reading. This is diagnostic information, never presentation or acknowledgment evidence."}

SENSITIVE_KEYS = {"ssn", "socialsecuritynumber", "creditscore", "consumerreport", "consumerreportdata",
                  "accountnumber", "pan", "cvv", "dob", "dateofbirth", "income", "password",
                  "token", "authorization", "secret", "email", "phone", "fullname"}


def screen(value, depth=0):
    if depth > 15:
        raise Block("SCHEMA_VALIDATION_FAILED")
    if isinstance(value, dict):
        for key, item in value.items():
            if re.sub(r"[^a-z]", "", str(key).lower()) in SENSITIVE_KEYS:
                raise Block("PROHIBITED_SENSITIVE_DATA")
            if re.sub(r"[^a-z]", "", str(key).lower()) in {"adverseaction", "adverseactionnotice"}:
                raise Block("AUTHORITATIVE_NOTICE_FLOW_REQUIRED")
            screen(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            screen(item, depth + 1)
    elif isinstance(value, str):
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{13,19}\b|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", value):
            raise Block("PROHIBITED_SENSITIVE_DATA")


def validate(value, schema):
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate(value, alternative)
                return
            except (Block, ValueError):
                pass
        raise Block("SCHEMA_VALIDATION_FAILED")
    kind = schema["type"]
    okay = {"object": isinstance(value, dict), "array": isinstance(value, list),
            "integer": type(value) is int, "boolean": type(value) is bool,
            "string": isinstance(value, str), "null": value is None}[kind]
    if not okay:
        raise Block("SCHEMA_VALIDATION_FAILED")
    if kind == "object":
        props = schema.get("properties", {})
        if not set(schema.get("required", [])).issubset(value):
            raise Block("SCHEMA_VALIDATION_FAILED")
        if schema.get("additionalProperties") is False and set(value) - set(props):
            raise Block("SCHEMA_VALIDATION_FAILED")
        for key in value.keys() & props.keys():
            validate(value[key], props[key])
    elif kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100):
            raise Block("SCHEMA_VALIDATION_FAILED")
        for item in value:
            validate(item, schema["items"])
    elif kind == "integer":
        if not schema.get("minimum", value) <= value <= schema.get("maximum", value):
            raise Block("SCHEMA_VALIDATION_FAILED")
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 10000):
            raise Block("SCHEMA_VALIDATION_FAILED")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise Block("SCHEMA_VALIDATION_FAILED")
        if schema.get("format") == "date-time":
            try:
                instant(value)
            except (ValueError, OverflowError):
                raise Block("SCHEMA_VALIDATION_FAILED") from None
    if "enum" in schema and value not in schema["enum"]:
        raise Block("SCHEMA_VALIDATION_FAILED")


def validate_request(tool, value):
    screen(value)
    try:
        if len(canonical(value).encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise Block("SCHEMA_VALIDATION_FAILED")
        validate(value, SCHEMAS[tool])
    except (ValueError, TypeError, KeyError, RecursionError):
        raise Block("SCHEMA_VALIDATION_FAILED") from None
