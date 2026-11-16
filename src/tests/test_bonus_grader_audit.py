"""B7 findings: strict xfail documents intentional supplied-grader defects.

Use --runxfail to expose the raw failing assertions. Unexpected fixes are XPASS
and fail the normal suite, so these marks do not silently accept changed graders.
"""

import importlib

import pytest

from bonus.grader_audit import GRADERS, RELATIONS, build_report, evaluate
from grader_audit.grader_b import summarize as reference

KNOWN_DEFECTS = {
    ("grader_a", "duplication"): "Extra cost per claim and shared duplicate pass_5 bug",
    ("grader_b", "duplication"): "Shared base counts rows instead of distinct seeds for pass_5",
    ("grader_c", "duplication"): "Shared base counts rows instead of distinct seeds for pass_5",
    ("grader_a", "order_invariance"): "Extra claim cost depends on the first seed encountered",
    ("grader_c", "infra_exclusion"): "Counts infrastructure failures as wrong decisions",
}


@pytest.mark.parametrize(
    "grader,relation",
    [pytest.param(g, r, id=f"{g}-{r}", marks=pytest.mark.xfail(
        strict=True, reason=KNOWN_DEFECTS[(g, r)]
    ) if (g, r) in KNOWN_DEFECTS else []) for g in GRADERS for r in RELATIONS],
)
def test_grader_metamorphic_relation(grader, relation):
    summarize = importlib.import_module(f"grader_audit.{grader}").summarize
    result = evaluate(summarize, relation)
    assert result["holds"], result["violations"]


def test_new_relation_detects_bug_missed_by_original_relations():
    def order_sensitive(rows):
        stats = reference(rows)
        if rows and rows[0]["seed"] == 22:
            for values in stats.values():
                values["total_simulated_cost_vnd"] += 1
                values["cost_per_success_vnd"] = values["total_simulated_cost_vnd"] / values["successes"]
        return stats

    # The existing shared pass_5 defect remains: this new bug adds no signal
    # to any original relation, but is detected by the new relation.
    for relation in RELATIONS[:3]:
        assert evaluate(order_sensitive, relation) == evaluate(reference, relation)
    assert evaluate(reference, "order_invariance")["holds"]
    assert not evaluate(order_sensitive, "order_invariance")["holds"]


def test_audit_report_is_reproducible_and_records_all_violations():
    report = build_report()
    assert report == build_report()
    violations = {(g, r) for g, results in report["results"].items()
                  for r, finding in results.items() if not finding["holds"]}
    assert violations == set(KNOWN_DEFECTS)


@pytest.mark.parametrize(
    "grader,relation,fields",
    [
        ("grader_a", "duplication", {"workflow.cost_per_success_vnd", "workflow.pass_5",
                                     "workflow.total_simulated_cost_vnd"}),
        ("grader_a", "order_invariance", {"workflow.cost_per_success_vnd",
                                          "workflow.total_simulated_cost_vnd"}),
        ("grader_b", "duplication", {"workflow.pass_5"}),
        ("grader_c", "duplication", {"workflow.pass_5"}),
        ("grader_c", "infra_exclusion", {"workflow.pass_rate", "workflow.graded_trials",
                                         "workflow.seed_pass_rates", "workflow.pass_5"}),
    ],
)
def test_expected_failures_do_not_hide_additional_bad_metrics(grader, relation, fields):
    summarize = importlib.import_module(f"grader_audit.{grader}").summarize
    finding = evaluate(summarize, relation)
    assert {item["field"] for item in finding["violations"]} == fields


@pytest.mark.parametrize("relation", ["infra_exclusion", "duplication", "order_invariance"])
def test_audit_rejects_grader_that_drops_every_shape(relation):
    finding = evaluate(lambda rows: {}, relation)
    assert not finding["holds"]
    assert {item["field"] for item in finding["violations"]} == {"a.shapes", "b.shapes"}
