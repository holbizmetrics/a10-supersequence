"""deep_n10.py — deep-run the WINNING profile from the wall map, save the best plateau word,
and auto-extract its missing-permutation signature (the culprit histogram). That signature is the
teeth of dispatch v4: "here is the exact structural deficit local search cannot fix."

Wall-map result this deepens (budget 1500/arm): winner [10,10,9,9,8,8,8,7,7,6] (ARM B gap 5,164).
This run: much larger budget on the winner (+ runner-up seed variety), saving words + signature.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import sys
import time
from collections import Counter
from math import factorial

from supersequence_family import exact_permutation_coverage
from a15_n10_graded import random_graded_word, structured_seed, profile_of

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
LENGTH = 82
REQUIRED = factorial(N)
WINNER_PROFILE = (10, 10, 9, 9, 8, 8, 8, 7, 7, 6)


def cov(word):
    return exact_permutation_coverage(word, N)


def anneal(word, budget, start_T, end_T, rng, label, log_every=2000):
    current = list(word)
    cur = cov(current)
    best, best_cov = list(current), cur
    for step in range(1, budget + 1):
        T = start_T * (end_T / start_T) ** ((step - 1) / max(1, budget - 1))
        i, j = rng.randrange(LENGTH), rng.randrange(LENGTH)
        if current[i] == current[j]:
            continue
        current[i], current[j] = current[j], current[i]
        c2 = cov(current)
        d = c2 - cur
        if d >= 0 or rng.random() < math.exp(d / T):
            cur = c2
            if cur > best_cov:
                best, best_cov = list(current), cur
        else:
            current[i], current[j] = current[j], current[i]
        if step % log_every == 0:
            print(f"  [{label} {step}] best gap {REQUIRED - best_cov}")
        if best_cov == REQUIRED:
            print(f"  *** {label}: FULL COVERAGE — CANDIDATE 82 ***")
            break
    return best, best_cov


def signature(word):
    """Enumerate ALL missing permutations of `word` + histograms (same method as the n=13/194 run)."""
    L = len(word)
    nextpos = [[L] * N for _ in range(L + 1)]
    current = [L] * N
    for p in range(L - 1, -1, -1):
        current = current.copy(); current[word[p]] = p; nextpos[p] = current
    missing = []
    def rec(mask, ptr, prefix):
        if mask == 0:
            return
        m = mask
        while m:
            bit = m & -m; s = bit.bit_length() - 1; m ^= bit
            occ = nextpos[ptr][s]
            if occ >= L:
                rest = [t for t in range(N) if (mask & (1 << t)) and t != s]
                for tail in itertools.permutations(rest):
                    missing.append(tuple(prefix) + (s,) + tail)
            else:
                rec(mask ^ bit, occ + 1, prefix + [s])
    rec((1 << N) - 1, 0, [])
    def fail_index(perm):
        ptr = 0
        for i, s in enumerate(perm):
            occ = nextpos[ptr][s]
            if occ >= L:
                return i
            ptr = occ + 1
        return -1
    depth = Counter(fail_index(p) for p in missing)
    culprit = Counter(p[fail_index(p)] for p in missing)
    return missing, dict(sorted(depth.items())), dict(culprit.most_common())


def main(budget, seeds):
    print(f"DEEP RUN — profile {WINNER_PROFILE} (wall-map winner), budget {budget}/run, {len(seeds)} seeds")
    overall_best, overall_cov = None, -1
    for seed in seeds:
        rng = random.Random(seed)
        # alternate seeding: structured for even seeds, random-graded for odd (diversity)
        word = structured_seed(WINNER_PROFILE, rng) if seed % 2 == 0 else random_graded_word(list(WINNER_PROFILE), rng)
        t0 = time.perf_counter()
        best, best_cov = anneal(word, budget, 25000.0, 15.0, rng, label=f"seed{seed}")
        print(f"[seed {seed}] final best gap {REQUIRED - best_cov}  ({time.perf_counter()-t0:.0f}s)")
        if best_cov > overall_cov:
            overall_best, overall_cov = best, best_cov
        if best_cov == REQUIRED:
            break

    gap = REQUIRED - overall_cov
    print(f"\n=== DEEP RESULT: best gap {gap} ===")
    result = {"profile": list(WINNER_PROFILE), "gap": gap, "word": overall_best}
    if gap == 0:
        print("*** CANDIDATE 82 — clean re-verify:", cov(overall_best) == REQUIRED, "***")
        print("word =", overall_best)
    else:
        miss_count_expected = gap
        missing, depth, culprit = signature(overall_best)
        print(f"signature: {len(missing)} missing perms (matches gap: {len(missing) == miss_count_expected})")
        print("fail-depth histogram:", depth)
        print("culprit histogram:", culprit)
        result["fail_depth"] = depth
        result["culprit"] = culprit
        result["missing_sample"] = [list(p) for p in missing[:10]]
    with open("deep_n10_result.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    print("saved -> deep_n10_result.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=20000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[2, 3])
    args = parser.parse_args()
    main(args.budget, args.seeds)
