"""desktop_arm.py — DESKTOP search arm of the n=10/82 attack (second windows node).

Lane division (bus, 2026-07-11): laptop deep-runs profile B [10,10,9,9,8,8,8,7,7,6];
desktop (this) runs the ORTHOGONAL lifted-66 profile A [10,10,10,9,8,8,7,7,7,6];
linux cold-scores plateau words on its decorrelated reversal-DP oracle.

What's new here vs deep_n10.py: a numba-jitted ITERATIVE coverage DP (~1000x the pure-Python
lru_cache recursion), unlocking million-step anneals. The jitted evaluator is cross-checked
EXACTLY against supersequence_family.exact_permutation_coverage before any run (instrument
check — a fast oracle that disagrees with the slow oracle is a bug, not a speedup).

Seeds: 1001+ (disjoint from laptop's [2,3]) — stated on the bus before launch.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from math import factorial

import numpy as np
from numba import njit

from supersequence_family import exact_permutation_coverage
from a15_n10_graded import random_graded_word, structured_seed
from deep_n10 import signature

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
LENGTH = 82
REQUIRED = factorial(N)
DESKTOP_PROFILE = (10, 10, 10, 9, 8, 8, 7, 7, 7, 6)  # lifted-66 guess, sum 82


@njit(cache=True)
def coverage_jit(word: np.ndarray, n: int) -> np.int64:
    """Iterative version of the (position, remaining_mask) DP.
    count[mask, p] = #permutations of the symbol-set `mask` embeddable (canonically, via
    first-occurrence steps) starting at position p. Ascending mask order is a valid
    topological order because mask^bit < mask."""
    length = word.shape[0]
    full = (1 << n) - 1
    # next occurrence table: nextpos[p, s] = first index >= p with word[index]==s, else length
    nextpos = np.full((length + 1, n), length, dtype=np.int64)
    for p in range(length - 1, -1, -1):
        for s in range(n):
            nextpos[p, s] = nextpos[p + 1, s]
        nextpos[p, word[p]] = p
    count = np.zeros((full + 1, length + 2), dtype=np.int64)
    count[0, :] = 1
    for mask in range(1, full + 1):
        m = mask
        while m:
            bit = m & (-m)
            s = 0
            b = bit
            while b > 1:
                b >>= 1
                s += 1
            sub = mask ^ bit
            for p in range(length + 1):
                occ = nextpos[p, s]
                if occ < length:
                    count[mask, p] += count[sub, occ + 1]
            m ^= bit
    return count[full, 0]


def cov_fast(word_list) -> int:
    return int(coverage_jit(np.asarray(word_list, dtype=np.int64), N))


def instrument_check(rng: random.Random) -> None:
    """Jitted oracle must agree EXACTLY with the pure-Python oracle before any run."""
    # known small case
    w3 = [0, 1, 2, 0, 1, 2, 0]
    assert int(coverage_jit(np.asarray(w3, dtype=np.int64), 3)) == 6 == exact_permutation_coverage(w3, 3)
    # random n=5 words (fast on both oracles)
    for _ in range(6):
        w = [rng.randrange(5) for _ in range(rng.randrange(10, 26))]
        a = int(coverage_jit(np.asarray(w, dtype=np.int64), 5))
        b = exact_permutation_coverage(w, 5)
        assert a == b, (w, a, b)
    # random n=10 length-82 words, both seed styles
    for k in range(3):
        w = random_graded_word(list(DESKTOP_PROFILE), rng) if k % 2 else structured_seed(DESKTOP_PROFILE, rng)
        a = cov_fast(w)
        b = exact_permutation_coverage(w, N)
        assert a == b, (a, b)
    print("[instrument] jitted DP == python DP on 10/10 cross-checks — instrument PASSES")


def anneal(word, budget, start_t, end_t, rng, label, log_every=50000):
    current = list(word)
    cur = cov_fast(current)
    best, best_cov = list(current), cur
    t0 = time.perf_counter()
    for step in range(1, budget + 1):
        temp = start_t * (end_t / start_t) ** ((step - 1) / max(1, budget - 1))
        i, j = rng.randrange(LENGTH), rng.randrange(LENGTH)
        if current[i] == current[j]:
            continue
        current[i], current[j] = current[j], current[i]
        c2 = cov_fast(current)
        d = c2 - cur
        if d >= 0 or rng.random() < math.exp(d / temp):
            cur = c2
            if cur > best_cov:
                best, best_cov = list(current), cur
        else:
            current[i], current[j] = current[j], current[i]
        if step % log_every == 0:
            rate = step / (time.perf_counter() - t0)
            print(f"  [{label} {step}] best gap {REQUIRED - best_cov}  ({rate:.0f} steps/s)")
        if best_cov == REQUIRED:
            print(f"  *** {label}: FULL COVERAGE — CANDIDATE 82 ***")
            break
    return best, best_cov


def main(budget, seeds):
    rng = random.Random(12345)
    instrument_check(rng)
    print(f"DESKTOP ARM — profile {DESKTOP_PROFILE} (lifted-66), budget {budget}/seed, seeds {seeds}")
    overall_best, overall_cov = None, -1
    for seed in seeds:
        srng = random.Random(seed)
        word = structured_seed(DESKTOP_PROFILE, srng) if seed % 2 == 0 else random_graded_word(list(DESKTOP_PROFILE), srng)
        t0 = time.perf_counter()
        best, best_cov = anneal(word, budget, 25000.0, 5.0, srng, label=f"seed{seed}")
        print(f"[seed {seed}] final best gap {REQUIRED - best_cov}  ({time.perf_counter() - t0:.0f}s)")
        if best_cov > overall_cov:
            overall_best, overall_cov = best, best_cov
        if best_cov == REQUIRED:
            break

    gap = REQUIRED - overall_cov
    # decidable re-verify of the final word on the SLOW oracle (instrument-independent)
    slow = exact_permutation_coverage(overall_best, N)
    print(f"\n=== DESKTOP RESULT: best gap {gap} (slow-oracle re-verify: {REQUIRED - slow}) ===")
    result = {"arm": "desktop", "profile": list(DESKTOP_PROFILE), "gap": gap,
              "slow_oracle_gap": REQUIRED - slow, "word": overall_best,
              "budget": budget, "seeds": seeds}
    if gap > 0:
        missing, depth, culprit = signature(overall_best)
        result["fail_depth"] = depth
        result["culprit"] = culprit
        result["missing_count"] = len(missing)
        print(f"signature: {len(missing)} missing (matches gap: {len(missing) == gap})")
        print("fail-depth:", depth)
        print("culprit:", culprit)
    with open("desktop_arm_result.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    print("saved -> desktop_arm_result.json")
    print("word =", overall_best)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=1_000_000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1001, 1002])
    args = parser.parse_args()
    main(args.budget, args.seeds)
