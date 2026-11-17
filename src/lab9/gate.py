"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from lab9.graders import GRADERS
from lab9.eval import aggregate
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    def finite(value):
        return isinstance(value, (int, float)) and math.isfinite(value)

    def inspect_report(rep, label):
        manifest, rows = rep.get("manifest", {}), rep.get("rows", [])
        seeds, items = manifest.get("seeds", []), manifest.get("items")
        pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
        try:
            counts = Counter(pairs)
            seed_set = set(seeds)
            item_ids = {i for i, _ in pairs}
            expected = {(i, seed) for i in item_ids for seed in seeds}
        except TypeError:
            problems.append(f"{label}: invalid item or seed identifiers")
            return set(), {}
        if not rows or not seeds or len(seed_set) != len(seeds) or not isinstance(items, int) or items < 1:
            problems.append(f"{label}: invalid/empty manifest or rows")
        if len(rows) != (items or 0) * len(seeds) or len(item_ids) != items:
            problems.append(f"{label}: rows do not match manifest item x seed count")
        if any(n != 1 for n in counts.values()) or set(pairs) != expected:
            problems.append(f"{label}: duplicated or incomplete item/seed grid")
        if any(not isinstance(i, str) or not isinstance(seed, int) or isinstance(seed, bool)
               for i, seed in pairs):
            problems.append(f"{label}: invalid item/seed types")
        if rep.get("evaluator_failures"):
            problems.append(f"{label}: evaluator_failures is nonempty")
        for mid, value in rep.get("metrics", {}).items():
            if not finite(value):
                problems.append(f"{label}: metric {mid} is missing or nonfinite")
        graded = [m for m in spec.get("metrics", []) if m["id"] in GRADERS]
        slices = {}
        for row in rows:
            tags = row.get("slices", [])
            if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags) or len(set(tags)) != len(tags):
                problems.append(f"{label}: invalid slice tags")
                tags = []
            tags = frozenset(tags)
            item = row.get("item_id")
            if item in slices and slices[item] != tags:
                problems.append(f"{label}: inconsistent slice tags across seeds")
            slices[item] = tags
            for m in graded:
                value = row.get(m["id"])
                if not finite(value) or value not in (0, 1):
                    problems.append(f"{label}: invalid/missing row value {m['id']}")
            if any(m["id"] == "cost_per_success" for m in spec.get("metrics", [])) and "cost" not in row:
                problems.append(f"{label}: missing row cost")
            if "cost" in row and (not finite(row["cost"]) or row["cost"] < 0):
                problems.append(f"{label}: invalid row cost")
        for m in spec.get("metrics", []):
            mid = m["id"]
            value = rep.get("metrics", {}).get(mid)
            if not finite(value):
                problems.append(f"{label}: required metric {mid} is missing/nonfinite")
            if mid in GRADERS and rows and all(finite(r.get(mid)) for r in rows):
                expected_value = sum(r[mid] for r in rows)
                if m.get("kind") != "safety":
                    expected_value = round(expected_value / len(rows), 4)
                if finite(value) and abs(value - expected_value) > 1e-8:
                    problems.append(f"{label}: aggregate {mid} contradicts rows")
        # Recompute derived reliability/cost metrics when their source evidence exists.
        if rows and all(finite(r.get("pass_rate")) and r.get("pass_rate") in (0, 1) for r in rows):
            # Reliability must still be checked if an attacker drops every cost field.
            derived = aggregate([{**r, "cost": r.get("cost", 0.0) if finite(r.get("cost", 0.0)) else 0.0}
                                 for r in rows], [], k_values=spec.get("pass_k", []))
            for mid, value in derived.items():
                if mid in rep.get("metrics", {}) and (not finite(value) or
                        not finite(rep["metrics"][mid]) or abs(value - rep["metrics"][mid]) > 1e-8):
                    problems.append(f"{label}: derived metric {mid} contradicts rows")
        return set(pairs), slices

    pr_pairs, pr_tags = inspect_report(pr, "PR")
    base_pairs, base_tags = inspect_report(base, "baseline")
    if pr_pairs != base_pairs:
        problems.append("PR and baseline have different item/seed sets")
    if pr_tags != base_tags:
        problems.append("PR changed item slice membership")
    if pr.get("manifest", {}).get("eval_set_sha") != base.get("manifest", {}).get("eval_set_sha"):
        problems.append("eval set checksum differs")
    if spec.get("seeds") and set(pr.get("manifest", {}).get("seeds", [])) != set(spec["seeds"]):
        problems.append("manifest seeds differ from spec")

    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        def ratchet(old, new, name, direct=False):
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"ratchet: {name} stopped blocking")
            ot, nt = (old, new) if direct else (old.get("threshold", {}), new.get("threshold", {}))
            for key, value in ot.items():
                if key in ("min", "max", "max_increase"):
                    nv = nt.get(key)
                    if not finite(nv) or (nv < value if key == "min" else nv > value):
                        problems.append(f"ratchet: {name} loosened {key}")
                elif key == "no_significant_drop" and value and not nt.get(key):
                    problems.append(f"ratchet: {name} dropped no_significant_drop")
        current = {m["id"]: m for m in spec.get("metrics", [])}
        for old in base_spec.get("metrics", []):
            mid = old["id"]
            if mid not in current:
                problems.append(f"ratchet: metric {mid} removed")
            else:
                ratchet(old, current[mid], mid)
                for field in ("kind", "grader", "level"):
                    if old.get(field) != current[mid].get(field):
                        problems.append(f"ratchet: metric {mid} changed {field}")
        current_slices = {(x["name"], x["metric"]): x for x in spec.get("slices", [])}
        for old in base_spec.get("slices", []):
            key = (old["name"], old["metric"])
            if key not in current_slices:
                problems.append(f"ratchet: slice {key} removed")
            else:
                ratchet(old, current_slices[key], f"slice:{key}", direct=True)
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        mid = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        failed, note = False, ""
        if not a or set(a) != set(b):
            failed, value, note = True, None, "missing or unmatched slice items"
        else:
            keys = sorted(a)
            value = sum(a.values()) / len(a)
            failed = "min" in entry and value < entry["min"]
            if entry.get("no_significant_drop"):
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95))
                failed = failed or hi < 0
                note = f"delta {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
        if failed and entry.get("blocking"):
            blocked.append(mid)
        verdict = "BLOCK" if failed and entry.get("blocking") else "warn" if failed else "ok"
        lines.append(f"  {mid:<35} {value!s:<8} {note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
