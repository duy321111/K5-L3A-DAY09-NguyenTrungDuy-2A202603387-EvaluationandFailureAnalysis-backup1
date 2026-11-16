"""B7: offline metamorphic audit; never modify the supplied graders or fixtures."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path

from lab8.compensation import quote

FIXTURES = Path(__file__).resolve().parents[1] / "grader_audit" / "fixtures"
GRADERS = ("grader_a", "grader_b", "grader_c")
RELATIONS = ("delay_boundary", "infra_exclusion", "duplication", "order_invariance")


def fixture(name):
    return json.loads((FIXTURES / f"metamorphic_{name}.json").read_text(encoding="utf-8"))


def equal(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10)
    return left == right


def evaluate(summarize, relation):
    """Return observed values and every violated expectation, without hiding failures."""
    if relation not in RELATIONS:
        raise ValueError(f"Unknown relation: {relation}")
    checks = []

    def check(field, expected, actual):
        checks.append({"field": field, "expected": expected, "actual": actual,
                       "holds": equal(expected, actual)})

    if relation == "delay_boundary":
        data = fixture("claim_delay")
        # This relation is business logic, not a summarize comparison.
        a, b = [quote(data[key]["order"], data["policies"], as_of=data["as_of"])
                for key in ("a", "b")]
        check("delay_2.amount_vnd", 0, a.amount_vnd)
        check("delay_3.amount_vnd", data["b"]["order"]["shipping_fee_vnd"], b.amount_vnd)
        check("entitlement_flips", True, a.amount_vnd == 0 and b.amount_vnd > 0)
        observations = {"a": a.amount_vnd, "b": b.amount_vnd, "scope": "shared quote function"}
    else:
        data = fixture("infra" if relation == "infra_exclusion" else "duplicate")
        a = summarize(data["a"])
        b = summarize(list(reversed(data["a"])) if relation == "order_invariance" else data["b"])
        observations = {"a": a, "b": b}
        expected_shapes = sorted({row["shape"] for row in data["a"]})
        check("a.shapes", expected_shapes, sorted(a))
        check("b.shapes", expected_shapes, sorted(b))
        for shape, stats in a.items():
            if shape not in b:
                continue
            other = b[shape]
            if relation == "infra_exclusion":
                for key in ("pass_rate", "graded_trials", "successes", "seed_pass_rates", "pass_5"):
                    check(f"{shape}.{key}", stats[key], other[key])
            elif relation == "duplication":
                totals = {"trials", "graded_trials", "successes", "total_simulated_cost_vnd"}
                invariants = {"pass_rate", "pass_5", "seed_pass_rates", "seed_variance",
                              "seed_min", "seed_max", "cost_per_success_vnd", "mean_steps",
                              "p95_steps", "mean_model_calls", "mean_tool_calls"}
                for key in sorted(totals | invariants):
                    expected = 2 * stats[key] if key in totals else stats[key]
                    check(f"{shape}.{key}", expected, other[key])
            elif relation == "order_invariance":
                # Independent completed trial records have no chronological meaning here.
                for key in stats:
                    check(f"{shape}.{key}", stats[key], other[key])
            else:
                raise ValueError(relation)
    return {"relation": relation, "holds": all(c["holds"] for c in checks),
            "violations": [c for c in checks if not c["holds"]],
            "checks": checks, "observations": observations}


def build_report():
    results = {}
    for name in GRADERS:
        summarize = importlib.import_module(f"grader_audit.{name}").summarize
        results[name] = {relation: evaluate(summarize, relation) for relation in RELATIONS}
    inputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(FIXTURES.glob("*.json"))}
    inputs.update({name: hashlib.sha256((FIXTURES.parent / f"{name}.py").read_bytes()).hexdigest()
                   for name in GRADERS})
    inputs["bonus/grader_audit.py"] = hashlib.sha256(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    report = {
        "topic": "B7", "inputs_sha256": inputs, "results": results,
        "safety": {"refund_execution": False, "secret_leak_count": None,
                   "approval_bypass_count": None,
                   "note": "Audit uses synthetic aggregate fixtures, not shape execution; safety gates are separate."},
        "limits": "Passing finite metamorphic relations does not prove general correctness. No hidden evaluation.",
    }
    digest = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()[:12]
    report["run_id"] = f"B7-{digest}"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/bonus_grader_audit.json")
    args = parser.parse_args()
    report = build_report()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["run_id"])
    for name, results in report["results"].items():
        print(name, ", ".join(f"{r}={'PASS' if v['holds'] else 'VIOLATION'}" for r, v in results.items()))
        for relation, finding in results.items():
            for violation in finding["violations"]:
                print(f"  {relation}: {violation['field']}: "
                      f"expected={violation['expected']}, actual={violation['actual']}")
    print(path)


if __name__ == "__main__":
    main()
