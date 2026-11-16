"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json
from typing import Any

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Choose the next read action using trusted facts, not ticket instructions."""
    claim = observation["claim"]
    if not claim["found"]:
        return {"final": {"status": "failed", "error_reason": "unknown_claim"}}
    if not claim.get("order_id"):
        return {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}

    last_tool = observation.get("last_tool")
    if last_tool is None:
        return {
            "tool": "lookup_order",
            "args": {"order_id": claim["order_id"], "principal_id": claim["principal_id"]},
        }

    result = observation["last_result"]
    if last_tool == "lookup_order":
        if not result["visible"]:
            return {"final": {"status": "escalated", "error_reason": result["reason"]}}
        return {"tool": "compute_compensation", "args": {"order": result["order"]}}
    if last_tool == "compute_compensation":
        # The shape takes the amount from the tool observation, not this final action.
        return {"final": {"status": "quote_ready"}}
    return {"final": {"status": "failed", "error_reason": "unexpected_observation"}}


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))
    try:
        budget.add_tool(tool_cost())
        view = get_claim_view(conn, claim_id)
        claim = {
            key: view[key]
            for key in ("found", "claim_id", "order_id", "principal_id")
            if key in view
        }

        def counted_decide(observation: dict[str, Any]) -> dict[str, Any]:
            # MockLLM simulates usage; the deterministic decide adapter selects tools.
            complete(
                budget,
                seed=seed,
                purpose="decide",
                prompt=json.dumps(observation, ensure_ascii=False, sort_keys=True),
            )
            action = decide(observation)
            trace.add("react", {"tool": action.get("tool"), "final": "final" in action})
            return action

        loop = run_react(
            conn,
            budget,
            observation={"claim": claim},
            decide=counted_decide,
            max_steps=8,
            worker=True,
        )
        trace.add("loop", {"stopped": loop["stopped"]})
        status = loop["final"]["status"]
        reason = loop["final"].get("error_reason")
        proposal = 0
        if status == "quote_ready":
            observation = loop["observation"]
            if observation.get("last_tool") != "compute_compensation":
                status, reason = "failed", "missing_quote"
            else:
                quote = observation["last_result"]
                proposal = int(quote["amount_vnd"])
                trace.add("quote", quote)
                if proposal <= 0:
                    status, reason = "denied", quote.get("reason")
                else:
                    # Full entitlement: the host handles approval and earlier refunds.
                    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
                    if outcome["ok"]:
                        status, reason = "resolved", None
                    else:
                        status = "failed" if outcome["conflict"] else "denied"
                        reason = outcome["reason"]

        trace.add("decision", {"status": status, "proposal_amount": proposal, "reason": reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
    finally:
        # Also closes on InjectedCrash, which deliberately propagates to the caller.
        conn.close()
