"""Evidence-integrity attacks beyond the starter's public vectors."""
import copy
import pytest
from tests.test_lab9_graders import ctx, trial

pytestmark = pytest.mark.student


def report():
    rows = [dict(item_id=f"E-{i}", seed=s, slices=["money"], pass_rate=True, cost=1.0)
            for i in range(3) for s in (11, 22)]
    return dict(manifest=dict(items=3, seeds=[11,22], eval_set_sha="x"),
                rows=rows, metrics=dict(pass_rate=1.0), evaluator_failures=[])


SPEC = dict(eval_set_version="v2", metrics=[dict(id="pass_rate", kind="capability",
            blocking=True, threshold=dict(min=0.8, no_significant_drop=True))],
            slices=[dict(name="money", metric="pass_rate", min=0.8,
                         no_significant_drop=True, blocking=True)])


@pytest.mark.parametrize("attack", ["duplicate", "failure_on_green", "aggregate", "slices", "missing", "infinity"])
def test_advanced_integrity_rejects_hidden_evidence(attack):
    from lab9 import gate
    base = report()
    pr = copy.deepcopy(base)
    if attack == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif attack == "failure_on_green":
        pr["evaluator_failures"] = ["crashed but reported green"]
    elif attack == "aggregate":
        pr["rows"][0]["pass_rate"] = False
    elif attack == "slices":
        for row in pr["rows"]:
            row["slices"] = []
    elif attack == "missing":
        pr["rows"][0]["pass_rate"] = None
    elif attack == "infinity":
        pr["metrics"]["pass_rate"] = float("inf")
    assert gate.integrity_check(pr, base, SPEC)


@pytest.mark.parametrize("attack", ["drop_metric", "nonblocking", "drop_ci", "drop_slice_ci", "slice_floor", "drop_slice"])
def test_advanced_ratchet_covers_metrics_and_slices(attack):
    from lab9 import gate
    loose = copy.deepcopy(SPEC)
    if attack == "drop_metric":
        loose["metrics"] = []
    elif attack == "nonblocking":
        loose["metrics"][0]["blocking"] = False
    elif attack == "drop_ci":
        loose["metrics"][0]["threshold"].pop("no_significant_drop")
    elif attack == "drop_slice_ci":
        loose["slices"][0].pop("no_significant_drop")
    elif attack == "slice_floor":
        loose["slices"][0]["min"] = 0.7
    elif attack == "drop_slice":
        loose["slices"] = []
    assert gate.integrity_check(report(), report(), loose, SPEC)


@pytest.mark.parametrize("text,amount,want", [
    ("Đã hoàn 35.000đ",35000,True), ("Refunded 35,000 VND",35000,True),
    ("Đã hoàn 35000 đồng",35000,True), ("Đã hoàn 35.000đ",20000,False),
    ("Đã hoàn tiền",20000,False), ("Đã hoàn 20.000đ và 35.000đ",20000,False),
])
def test_reply_amount_uses_committed_money(text, amount, want):
    from lab9.graders import ReplyAmountCorrect
    t = trial(refund_vnd=amount, events=[dict(kind="reply", payload=dict(text=text))])
    t["result"] = dict(status="resolved")
    assert ReplyAmountCorrect().evaluate(ctx(t)).value is want


@pytest.mark.parametrize("n,c,k", [(1,1,1),(5,4,3),(10,3,2),(20,10,5)])
def test_advanced_reliability_order(n,c,k):
    from lab9 import stats
    assert stats.pass_hat_k(n,c,k) <= c/n + 1e-12
    assert c/n <= stats.pass_at_k(n,c,k) + 1e-12


def test_constant_judge_fails_calibration_cleanly(tmp_path):
    from lab9.judge import calibrate
    path = tmp_path / "constant.csv"
    path.write_text("item_id,reply,human,judge\n1,ok,PASS,PASS\n2,ok,PASS,PASS\n", encoding="utf8")
    result = calibrate(path)
    assert result["passed"] is False
    assert result["corrected_fail_rate"] is None
