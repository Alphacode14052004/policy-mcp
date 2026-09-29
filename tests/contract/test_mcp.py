import asyncio
import json
import unittest
from importlib.util import find_spec
from offerproof.models.contracts import ENVELOPE, SCHEMAS
from tests.helpers import Harness

SDK = find_spec("mcp") is not None


@unittest.skipUnless(SDK, "Official MCP SDK unavailable; run with scripts/run_tests.py --sdk-dir <built vendor>")
class MCPTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)

    def test_02_discovery_has_self_describing_cold_start_contracts(self):
        from mcp import Client
        from offerproof.server import OfferProofServer
        async def exercise():
            async with Client(OfferProofServer(self.h.service)) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual({t.name for t in tools}, set(SCHEMAS))
                for tool in tools:
                    self.assertIn("For a new cart, call start_offer_journey", tool.description)
                    self.assertEqual(tool.input_schema, SCHEMAS[tool.name])
                    self.assertEqual(tool.output_schema, ENVELOPE)
                resources = (await client.list_resources()).resources
                self.assertEqual(len(resources), 3)
                self.assertEqual(len((await client.list_resource_templates()).resource_templates), 3)
                self.assertEqual(len((await client.list_prompts()).prompts), 4)
                resource = await client.read_resource("offerproof://workflow/v1")
                self.assertIn("next_action", resource.contents[0].text)
                start_tool = next(t for t in tools if t.name == "start_offer_journey")
                self.assertIn("MOCK-SKU-SOFA", start_tool.description)
                self.assertIn("cart.applied_tenders", start_tool.description)
                self.assertIn("Before asking the consumer to choose", start_tool.description)
                self.assertIn("disclosure_preview.canonical_text verbatim", start_tool.description)
                self.assertIn("Never guess timestamps", start_tool.description)
                catalog = json.loads((await client.read_resource("offerproof://catalog/current")).contents[0].text)
                self.assertIn({"sku": "MOCK-SKU-SOFA", "category": "SOFA", "item_type": "GOODS"}, catalog["products"])
        asyncio.run(exercise())

    def test_mcp_valid_and_malformed_inputs_return_audited_schema_envelopes(self):
        from mcp import Client
        from offerproof.server import OfferProofServer
        from jsonschema import Draft202012Validator
        async def exercise():
            async with Client(OfferProofServer(self.h.service)) as client:
                for tool in SCHEMAS:
                    r = await client.call_tool(tool, {"unknown": "field"})
                    Draft202012Validator(ENVELOPE).validate(r.structured_content)
                    self.assertEqual(r.structured_content["reason_code"], "SCHEMA_VALIDATION_FAILED")
                r = await client.call_tool("start_offer_journey", self.h.request)
                Draft202012Validator(ENVELOPE).validate(r.structured_content)
                self.assertEqual(r.structured_content["reason_code"], "OK")
        asyncio.run(exercise())
        self.assertEqual(sum(e["outcome"] == "ATTEMPTED" for e in self.h.events()), 6)

    def test_mcp_happy_path(self):
        self.exercise_happy_path()

    def test_mcp_sofa_with_existing_gift_payment(self):
        from tests.scenarios.test_sofa_tender import sofa_request
        self.h.request = sofa_request()
        self.exercise_happy_path()

    def exercise_happy_path(self):
        from mcp import Client
        from offerproof.server import OfferProofServer
        from offerproof.security.digests import iso
        from jsonschema import Draft202012Validator
        async def exercise():
            async with Client(OfferProofServer(self.h.service)) as client:
                async def call(tool, payload):
                    r = (await client.call_tool(tool, payload)).structured_content
                    Draft202012Validator(ENVELOPE).validate(r)
                    self.assertEqual(r["reason_code"], "OK", r)
                    return r
                r = await call("start_offer_journey", self.h.request)
                from offerproof.config import APP_VERSION
                self.assertEqual(r["result"]["server_version"], APP_VERSION)
                for offer in r["result"]["offers"]:
                    if offer["eligible"]:
                        preview = offer["disclosure_preview"]
                        self.assertTrue(preview["canonical_text"])
                        self.assertFalse(preview["selection_is_acceptance"])
                        self.assertFalse(preview["is_final_disclosure"])
                p = await call("prepare_offer_disclosure", self.h.prepare_payload(r))
                self.assertIn("server_time", p)
                self.assertIn("issued_at", p["result"])
                record = self.h.record_payload(p, p["result"])
                r = await call("record_disclosure_outcome", record)
                r = await call("record_disclosure_outcome", {**record, **self.h.base(r), "outcome": "ACKNOWLEDGED",
                    "acknowledgment": {"actor": "CONSUMER", "action": "ACKNOWLEDGE", "event_id": "MOCK-EVENT-001",
                        "captured_at": iso(self.h.clock()), "affirmative_action": True}})
                r = await call("authorize_promotional_checkout", self.h.auth_payload(r))
                self.assertEqual(r["journey_state"], "AUTHORIZED")
        asyncio.run(exercise())

    def test_mcp_exposes_timing_failure_and_fresh_status_for_existing_journey(self):
        from datetime import timedelta
        from mcp import Client
        from offerproof.server import OfferProofServer
        from offerproof.security.digests import iso
        from jsonschema import Draft202012Validator
        async def exercise():
            p = self.h.prepared()
            payload = self.h.record_payload(p, p["result"])
            payload["evidence"]["rendered_at"] = iso(self.h.clock() + timedelta(seconds=1))
            async with Client(OfferProofServer(self.h.service)) as client:
                blocked = await client.call_tool("record_disclosure_outcome", payload)
                self.assertTrue(blocked.is_error)
                r = blocked.structured_content
                Draft202012Validator(ENVELOPE).validate(r)
                self.assertEqual(r["result"]["presentation_error"]["check"], "RENDERED_AT_IN_FUTURE")
                self.h.clock.now += timedelta(seconds=3)
                status = (await client.call_tool("get_offer_journey_status", {"journey_id": p["journey_id"],
                    "merchant_id": self.h.request["merchant_id"], "agent_id": self.h.request["agent_id"]})).structured_content
                self.assertEqual(status["result"]["issued_at"], p["result"]["issued_at"])
                self.assertEqual(status["server_time"], iso(self.h.clock()))
                self.assertEqual(status["journey_state"], "DISCLOSURE_ISSUED")
        asyncio.run(exercise())
