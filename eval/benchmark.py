"""Measured deterministic core workload. Does not call an LLM or measure business savings."""
import argparse
import copy
import json
import math
import platform
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from offerproof.models.contracts import ENVELOPE, validate
from scripts.demo import run
from tests.helpers import Harness


def measure(calls, repetitions):
    h = Harness()
    latencies, counts = [], {}
    try:
        for index in range(calls):
            request = copy.deepcopy(h.request)
            request["idempotency_key"] = f"adversarial-{index}"
            choice = index % 10
            tool = "start_offer_journey"
            if choice == 0:
                request["cart"]["lines"][0]["quantity"] = -index - 1
            elif choice == 1:
                request["unknown_field"] = "not permitted"
            elif choice == 2:
                request["cart"]["total_cents"] += index + 1
            elif choice == 3:
                request["cart"]["currency"] = "EUR"
            elif choice == 4:
                request["locale"] = "es-US"
            elif choice == 5:
                request["jurisdiction"]["billing_state"] = "MOCK-UNKNOWN"
            elif choice == 6:
                request["credit_score"] = "SYNTHETIC-PROHIBITED-FIELD"
            elif choice == 7:
                request["cart"]["lines"][1]["item_type"] = "GOODS"
            elif choice == 8:
                request["cart"]["lines"][0]["description"] = "a" * (2001 + index)
            else:
                tool = "authorize_promotional_checkout"
            started = time.perf_counter_ns()
            response = h.call(tool, request)
            latencies.append((time.perf_counter_ns() - started) / 1000000)
            validate(response, ENVELOPE)
            assert response["status"] == "BLOCKED" and response["journey_state"] != "AUTHORIZED", response
            counts[response["reason_code"]] = counts.get(response["reason_code"], 0) + 1
        successful = []
        for _ in range(repetitions):
            result = run(h.service, h.clock)
            successful.append(result["steps"][-1]["response"]["result"])
        with h.service.store.connect() as connection:
            audits_valid = h.service.audit.verify_chain(connection)
        assert audits_valid and all(row["receipt"]["signature"] for row in successful)
        return {"python": platform.python_version(), "platform": platform.platform(),
            "workload": "Deterministic direct-core calls: ten malformed/adversarial families with varied payloads; not a live LLM evaluation.",
            "adversarial_calls": calls, "blocked_calls": sum(counts.values()), "reason_counts": counts,
            "adversarial_call_p95_ms": sorted(latencies)[math.ceil(len(latencies) * .95) - 1],
            "latency_scope": "Direct core, includes JSON validation, SQLite attempt/final commits; excludes MCP transport, LLM and human time.",
            "automated_fixture_repetitions": repetitions, "successful_authorizations_with_receipts": len(successful),
            "changed_cart_replays_blocked": repetitions, "audit_chain_valid": audits_valid,
            "live_copilot_rehearsals": 0, "natural_language_prompts_executed": 0, "business_savings_measured": False}
    finally:
        h.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--calls", type=int, default=1000)
    parser.add_argument("--fixture-repetitions", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("eval/results/benchmark.json"))
    args = parser.parse_args()
    result = measure(args.calls, args.fixture_repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
