"""exhaustive_lb_check.py — EXHAUSTIVE admissibility check of BOTH deployed bounds (v2.lb, v3.lb3)
over every reachable canon class at n, with exact truth from a memoized completion DP.

Supersedes the sampled lb_admissibility_fuzz at the n it completes: coverage is every reachable
canon class, not 400 samples. Soundness of the class-level check: canon-equal states are related
by a symbol bijection (audit: equal canon => genuine equivalence), and truth/lb/lb3 are all
relabel-invariant, so one representative per class decides the class.

truth(state) = 1 + min over heads of truth(advance(state, x)); heads-only is WLOG (a non-head
emission changes nothing). Uses ONLY advance/heads — no lb, no prover memo. The DP's root value
is a BUILT-IN NULL CONTROL: it must equal the proven a(n) (7/12/19) or the instrument is broken
and no verdict counts. Re-checking v2.lb reproduces the 2026-07-13 audit's exhaustive zero-
violation verdict — a second control.

Budget discipline (2026-07-21): wall budget enforced IN-PROCESS (time.time), the R1 lesson.
Exit 0 clean / 1 VIOLATION (soundness kill) / 2 null-control failure / 3 budget exceeded.
"""
from __future__ import annotations

import argparse
import sys
import time

from proofmachine_v2 import root_state, advance, heads, canon, lb
from proofmachine_v3 import lb3

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

A_TRUE = {3: 7, 4: 12, 5: 19}


def check(n, wall_budget=None, progress_every=100_000):
    w0 = time.time()
    truth_memo = {}          # canon key -> exact completion length
    stats = {"classes": 0, "viol_lb": [], "viol_lb3": [], "worst_lb": None, "worst_lb3": None}

    sys.setrecursionlimit(200_000)

    def truth(state):
        if not state:
            return 0
        key = canon(state, n)
        hit = truth_memo.get(key)
        if hit is not None:
            return hit
        if wall_budget is not None and time.time() - w0 > wall_budget:
            raise TimeoutError
        best = None
        for x in sorted(heads(state)):
            t = 1 + truth(advance(state, x))
            if best is None or t < best:
                best = t
        truth_memo[key] = best
        stats["classes"] += 1
        if stats["classes"] % progress_every == 0:
            print(f"  ... {stats['classes']:,} classes, {time.time()-w0:.0f}s")
        # admissibility of BOTH deployed bounds on this representative
        b2, b3 = lb(state, n), lb3(state, n)
        if b2 > best:
            stats["viol_lb"].append((sorted(state), b2, best))
        if b3 > best:
            stats["viol_lb3"].append((sorted(state), b3, best))
        s2, s3 = best - b2, best - b3
        if stats["worst_lb"] is None or s2 < stats["worst_lb"]:
            stats["worst_lb"] = s2
        if stats["worst_lb3"] is None or s3 < stats["worst_lb3"]:
            stats["worst_lb3"] = s3
        return best

    try:
        root_truth = truth(root_state(n))
    except TimeoutError:
        rate = stats["classes"] / max(time.time() - w0, 1e-9)
        print(f"[n={n}] BUDGET EXCEEDED at {stats['classes']:,} classes "
              f"({time.time()-w0:.0f}s, {rate:,.0f} classes/s) — no verdict.")
        return 3
    dt = time.time() - w0
    ok_null = root_truth == A_TRUE[n]
    print(f"[n={n}] classes={stats['classes']:,}  root-truth={root_truth} "
          f"(NULL CONTROL {'PASS' if ok_null else '*** FAIL — expected ' + str(A_TRUE[n])})  {dt:.1f}s")
    print(f"       lb : {len(stats['viol_lb'])} violations, tightest slack {stats['worst_lb']}")
    print(f"       lb3: {len(stats['viol_lb3'])} violations, tightest slack {stats['worst_lb3']}")
    for tag in ("viol_lb", "viol_lb3"):
        for st, b, t in stats[tag][:3]:
            print(f"    *** INADMISSIBLE {tag}: bound={b} > truth={t}  state={st}")
    if not ok_null:
        return 2
    if stats["viol_lb"] or stats["viol_lb3"]:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--wall-budget", type=float, default=None,
                        help="in-process seconds cap PER n (exit 3 on breach, no verdict)")
    args = parser.parse_args()
    worst = 0
    for n in args.n:
        worst = max(worst, check(n, wall_budget=args.wall_budget))
    if worst == 0:
        print("VERDICT: lb AND lb3 admissible on EVERY reachable canon class at all completed n.")
    sys.exit(worst)


if __name__ == "__main__":
    main()
