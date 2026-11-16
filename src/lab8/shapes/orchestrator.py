"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("orchestrator", claim_id, seed))

    def conclude(status: str, proposal: int = 0, reason: str | None = None) -> RunResult:
        # MockLLM only drafts wording from the code's decision, never money or tools.
        # Neither the ticket nor model output is written to the trace.
        complete(budget, seed=seed, purpose="draft", prompt=f"status={status}; proposal={proposal}")
        trace.add("decision", {"status": status, "proposal_amount": proposal, "reason": reason})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add("claim", {"claim_id": claim_id, "found": claim["found"]})
    if not claim["found"]:
        return conclude("failed", reason="unknown_claim")
    if not claim.get("order_id"):
        return conclude("needs_info", reason="missing_order_id")

    # The delegation is fixed in code. Free-form ticket text cannot grant tools
    # or change the principal; the runtime enforces ownership on order lookup.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", handoff)
    investigated = run_readonly_investigators(
        conn, budget, handoff, principal_id=claim["principal_id"]
    )
    tools = investigated["tools"]
    order_view = tools.get("lookup_order", {})
    # Log only the scope decision, not the full claim, ticket or order payload.
    trace.add("investigator", {
        "visible": bool(order_view.get("visible")),
        "reason": order_view.get("reason"),
        "policy_count": len((tools.get("lookup_policy") or {}).get("policies") or []),
    })
    if not order_view.get("visible"):
        return conclude("escalated", reason=order_view.get("reason"))

    quote = tools["compute_compensation"]
    proposal = int(quote["amount_vnd"])
    trace.add("quote", quote)
    if proposal <= 0:
        return conclude("denied", reason=quote.get("reason"))

    # Pass the FULL entitlement. Approval caps and earlier refunds belong to
    # the host transaction; subtracting them here would subtract them twice.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        # Flush evidence, then propagate the crash so the harness can resume.
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("host", {
        "ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"],
    })
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return conclude(status, proposal, outcome["reason"])
    return conclude("resolved", proposal)
