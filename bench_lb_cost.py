"""bench_lb_cost.py — the R1 owed diagnosis: is the n=6 throughput collapse ALGORITHMIC
(lb3 per-call cost) or ENVIRONMENTAL (overnight sleep/throttle)?

Times v2.lb vs v3.lb3 per-call on the SAME reachable n=6 states, and compares bound values.
Pre-registered decision rule lives in CAMPAIGN-a10.md § Rung log 2026-07-21 (sealed before run).
"""
from __future__ import annotations

import random
import statistics
import sys
import time

import proofmachine_v2 as v2
import proofmachine_v3 as v3

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 6
TARGET_STATES = 300
REPS = 50


def sample_states(rng):
    """Distinct reachable n=6 states via random advance-walks from root, mixed depths."""
    states = set()
    tries = 0
    while len(states) < TARGET_STATES and tries < 20_000:
        tries += 1
        st = v2.root_state(N)
        for _ in range(rng.randrange(1, 4 * N)):
            hs = sorted(v2.heads(st))
            if not hs or not st:
                break
            st = v2.advance(st, rng.choice(hs))
        if st:
            states.add(st)
    return sorted(states, key=lambda s: (len(s), sorted(s)))


def time_fn(fn, st):
    best = float("inf")
    for _ in range(REPS):
        t0 = time.perf_counter()
        fn(st, N)
        dt = time.perf_counter() - t0
        if dt < best:
            best = dt
    return best


def main():
    rng = random.Random(62714)
    states = sample_states(rng)
    print(f"[bench] {len(states)} distinct reachable n={N} states (seed 62714)")
    t_lb, t_lb3, gt, eq, lt = [], [], 0, 0, 0
    for st in states:
        t_lb.append(time_fn(v2.lb, st))
        t_lb3.append(time_fn(v3.lb3, st))
        a, b = v2.lb(st, N), v3.lb3(st, N)
        gt += b > a
        eq += b == a
        lt += b < a
    med_lb = statistics.median(t_lb) * 1e6
    med_lb3 = statistics.median(t_lb3) * 1e6
    ratio = med_lb3 / med_lb if med_lb > 0 else float("inf")
    print(f"  v2.lb  median {med_lb:9.1f} us/call   mean {statistics.mean(t_lb)*1e6:9.1f}")
    print(f"  v3.lb3 median {med_lb3:9.1f} us/call   mean {statistics.mean(t_lb3)*1e6:9.1f}")
    print(f"  RATIO lb3/lb (median): {ratio:.2f}x")
    print(f"  strength on same states: lb3>lb {gt} / equal {eq} / lb3<lb {lt}")
    # pre-registered adjudication (CAMPAIGN-a10.md 2026-07-21)
    if ratio <= 5 and med_lb3 < 500:
        verdict = "ENVIRONMENTAL — file H2 (awake/desktop re-run) before evolution machinery"
    elif ratio >= 20 or med_lb3 >= 2000:
        verdict = "ALGORITHMIC — evolution fitness = wall-clock; first target = cheaper lb3"
    else:
        verdict = "MIXED — both lanes named, operator picks"
    print(f"  VERDICT (pre-registered rule): {verdict}")


if __name__ == "__main__":
    main()
