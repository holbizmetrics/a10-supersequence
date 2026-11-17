"""two_swap_clearance.py — EXHAUSTIVE 2-swap clearance (laptop design 1877b247, STEP 1).

Decidable question: is a given word within ONE or TWO position-swaps of full coverage (gap 0)?
Enumerates ALL single swaps (i<j), then ALL ordered pairs of swaps (second loop unrestricted, so
both orders of overlapping/non-commuting pairs are covered; disjoint pairs get evaluated twice —
redundant but exhaustive-by-construction, which is the point of a clearance).

Fully jitted with prange parallelism. Collects every word reaching gap <= NEAR_KEEP (near-hits
inform the next kernel design). Verdict per word: CLEARED-NO (definitively not within 2 swaps),
or HIT (word(s) at gap 0, slow-oracle re-verified Python-side before any claim).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from math import factorial

import numpy as np
from numba import njit, prange

from supersequence_family import exact_permutation_coverage
from desktop_arm import coverage_jit

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
REQUIRED = factorial(N)
NEAR_KEEP = 5  # collect (first-swap, second-swap) pairs reaching gap <= this


@njit(cache=True)
def _coverage(word, n):
    return coverage_jit(word, n)


@njit(cache=True)
def single_swaps(word, n):
    """Return (best_cov, best_i, best_j, covs) over all single swaps i<j."""
    length = word.shape[0]
    best_cov = -1
    best_i = -1
    best_j = -1
    for i in range(length - 1):
        for j in range(i + 1, length):
            if word[i] == word[j]:
                continue
            word[i], word[j] = word[j], word[i]
            c = _coverage(word, n)
            word[i], word[j] = word[j], word[i]
            if c > best_cov:
                best_cov, best_i, best_j = c, i, j
    return best_cov, best_i, best_j


@njit(parallel=True, cache=True)
def pair_swaps(word, n, required, pair_table):
    """For every first swap (row of pair_table, i<j -> prange) apply it, then try EVERY second
    swap (k<l). Returns per-first-swap best coverage + the (k,l) achieving it, so Python can
    reconstruct all near-hits and any exact hit. Ordered coverage of overlapping pairs comes
    from the outer loop visiting both members of each overlapping pair as 'first'."""
    length = word.shape[0]
    n_first = pair_table.shape[0]
    best_cov = np.full(n_first, -1, dtype=np.int64)
    best_kl = np.full((n_first, 2), -1, dtype=np.int64)
    for idx in prange(n_first):
        i = pair_table[idx, 0]
        j = pair_table[idx, 1]
        if word[i] == word[j]:
            continue
        w = word.copy()
        w[i], w[j] = w[j], w[i]
        loc_best = _coverage(w, n)  # pair may degenerate to the single swap (k,l no-op skipped)
        loc_k, loc_l = -1, -1
        for k in range(length - 1):
            for l in range(k + 1, length):
                if w[k] == w[l]:
                    continue
                w[k], w[l] = w[l], w[k]
                c = _coverage(w, n)
                w[k], w[l] = w[l], w[k]
                if c > loc_best:
                    loc_best, loc_k, loc_l = c, k, l
                    if c == required:
                        break
            if loc_best == required:
                break
        best_cov[idx] = loc_best
        best_kl[idx, 0] = loc_k
        best_kl[idx, 1] = loc_l
    return best_cov, best_kl


def make_pair_table(length):
    return np.array([(i, j) for i in range(length - 1) for j in range(i + 1, length)],
                    dtype=np.int64)


def clear_word(name, word):
    word = np.asarray(word, dtype=np.int64)
    length = len(word)
    base_gap = REQUIRED - int(coverage_jit(word, N))
    print(f"\n=== {name}: base gap {base_gap} ===")

    t0 = time.perf_counter()
    s_cov, s_i, s_j = single_swaps(word.copy(), N)
    print(f"[singles] best gap {REQUIRED - s_cov} via swap({s_i},{s_j})  "
          f"({time.perf_counter() - t0:.1f}s for {length*(length-1)//2} swaps)")
    if s_cov == REQUIRED:
        return finish_hit(name, word, [(int(s_i), int(s_j))])

    t0 = time.perf_counter()
    pair_table = make_pair_table(length)
    p_cov, p_kl = pair_swaps(word.copy(), N, REQUIRED, pair_table)
    dt = time.perf_counter() - t0
    best_idx = int(np.argmax(p_cov))
    best = int(p_cov[best_idx])
    print(f"[pairs] best gap {REQUIRED - best}  ({dt:.0f}s exhaustive)")

    near = []
    for idx in np.nonzero(p_cov >= REQUIRED - NEAR_KEEP)[0]:
        i, j = int(pair_table[idx, 0]), int(pair_table[idx, 1])
        k, l = int(p_kl[idx, 0]), int(p_kl[idx, 1])
        near.append({"swap1": [i, j], "swap2": [k, l], "gap": REQUIRED - int(p_cov[idx])})
    near.sort(key=lambda r: r["gap"])
    print(f"[pairs] near-hits (gap<={NEAR_KEEP}): {len(near)}")
    for r in near[:10]:
        print("   ", r)

    if best == REQUIRED:
        idx = best_idx
        i, j = int(pair_table[idx, 0]), int(pair_table[idx, 1])
        k, l = int(p_kl[idx, 0]), int(p_kl[idx, 1])
        return finish_hit(name, word, [(i, j), (k, l)])

    verdict = {"name": name, "base_gap": base_gap, "verdict": "CLEARED-NO",
               "best_single_gap": REQUIRED - int(s_cov),
               "best_pair_gap": REQUIRED - best, "near_hits": near}
    print(f"VERDICT {name}: CLEARED-NO — not within 2 swaps of 0 (best pair gap {REQUIRED - best})")
    return verdict


def finish_hit(name, word, swaps):
    w = list(int(x) for x in word)
    for i, j in swaps:
        w[i], w[j] = w[j], w[i]
    slow = exact_permutation_coverage(w, N)
    ok = slow == REQUIRED
    print(f"*** {name}: HIT at swaps {swaps} — slow-oracle re-verify: "
          f"{'CONFIRMED gap 0' if ok else f'FAILED ({REQUIRED - slow} short) — INSTRUMENT BUG'} ***")
    if ok:
        print("word =", w)
    return {"name": name, "verdict": "HIT" if ok else "HIT-UNCONFIRMED",
            "swaps": [list(s) for s in swaps], "word": w, "slow_gap": REQUIRED - slow}


def main(targets):
    with open("batch2_result.json", encoding="utf-8") as handle:
        batch2 = {f"W{r['gap']}": r["word"] for r in json.load(handle) if r["arm"] == "CONTROL"}
    with open("desktop_arm_result.json", encoding="utf-8") as handle:
        batch2["W23"] = json.load(handle)["word"]
    out = []
    for name in targets:
        if name not in batch2:
            print(f"skip {name}: not found (have {sorted(batch2)})")
            continue
        out.append(clear_word(name, batch2[name]))
        with open("two_swap_clearance.json", "w", encoding="utf-8") as handle:
            json.dump(out, handle)
    print("\nsaved -> two_swap_clearance.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["W17", "W19", "W23"])
    args = parser.parse_args()
    main(args.targets)
