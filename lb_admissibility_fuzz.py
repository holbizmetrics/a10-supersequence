"""lb_admissibility_fuzz.py — REVIEWER FINDING (laptop 0c35d442, 2026-07-13): direct admissibility
test of proofmachine_v2's lb(), the component every rung depends on.

WHY THIS EXISTS. v2's four soundness arguments (dominance / universe non-circularity / imperfect
canon / memo semantics) all hold under review. But lb() itself — the pruning oracle — is validated
only INDIRECTLY (the ladder rungs happen to match ground truth). If ANY lb term over-estimates on
ANY reachable state, the prover prunes a live branch and reports PROVED-NO wrongly => every green
rung (including the 96M-node n=6) is void. The v3 charter demands exactly this test for EVOLVED
bounds ("admissibility mechanically verified vs brute-force, decidable, uncheatable") — it was never
retro-applied to the bounds v2 already ships.

THE TEST (decidable, no shared machinery with lb):
  truth(state) = exact minimal number of further symbols to satisfy all pending blocks,
                 computed by pure BFS over block-space using ONLY `advance` (no lb, no memo).
  ADMISSIBLE  <=>  lb(state, n) <= truth(state)   for every reachable state.
A single violation is a soundness kill. Passing is not proof of admissibility (finite sample), but
it converts "trusted by argument" into "argument + adversarially fuzzed", which is the bar the
campaign holds everything else to.
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import deque

from proofmachine_v2 import root_state, advance, heads, lb

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass


def truth_min_length(state, n, cap=40):
    """EXACT minimal further length to satisfy `state`, by BFS over block-space.
    Uses only `advance` (the bridge-tested transition) — NO lb, NO memo. Independent of the
    thing under test. Returns None if not reached within cap (should not happen at small n)."""
    if not state:
        return 0
    seen = {state}
    frontier = deque([(state, 0)])
    while frontier:
        cur, d = frontier.popleft()
        if d >= cap:
            continue
        for x in heads(cur):
            nxt = advance(cur, x)
            if not nxt:
                return d + 1
            if nxt not in seen:
                seen.add(nxt)
                frontier.append((nxt, d + 1))
    return None


def random_reachable_states(n, rng, count, max_walk):
    """Walk from the root emitting random heads; collect the states passed through."""
    out = []
    while len(out) < count:
        state = root_state(n)
        steps = rng.randrange(0, max_walk)
        for _ in range(steps):
            hs = sorted(heads(state))
            if not hs:
                break
            state = advance(state, rng.choice(hs))
            if not state:
                break
        if state:
            out.append(state)
    return out


def fuzz(n, samples, rng, cap):
    states = random_reachable_states(n, rng, samples, max_walk=2 * n + 4)
    violations = []
    checked = 0
    worst_slack = None
    for st in states:
        truth = truth_min_length(st, n, cap=cap)
        if truth is None:
            continue
        bound = lb(st, n)
        checked += 1
        slack = truth - bound
        if worst_slack is None or slack < worst_slack:
            worst_slack = slack
        if bound > truth:                      # OVER-estimate => INADMISSIBLE => prover unsound
            violations.append((sorted(st), bound, truth))
    return checked, violations, worst_slack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--samples", type=int, default=400)
    parser.add_argument("--cap", type=int, default=40)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    print("lb ADMISSIBILITY FUZZ — lb(state) must be <= exact minimal completion length (BFS truth)")
    print(f"{'n':>3} {'checked':>8} {'violations':>11} {'tightest slack':>15}")
    total_viol = 0
    for n in args.n:
        checked, violations, worst = fuzz(n, args.samples, rng, args.cap)
        total_viol += len(violations)
        print(f"{n:>3} {checked:>8} {len(violations):>11} {str(worst):>15}")
        for st, bound, truth in violations[:3]:
            print(f"    *** INADMISSIBLE: lb={bound} > truth={truth}  state={st}")
    print()
    if total_viol:
        print("VERDICT: lb is INADMISSIBLE — the prover can wrongly prune. EVERY RUNG IS VOID.")
        sys.exit(1)
    print("VERDICT: no violation found. lb is admissible on all sampled reachable states")
    print("         (tightest slack 0 = the bound is exactly tight somewhere — as it should be).")
    sys.exit(0)


if __name__ == "__main__":
    main()
