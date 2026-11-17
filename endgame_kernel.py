"""endgame_kernel.py — the last-symbol repair phase (desktop lane, follows batch 2).

Standing invariant across ALL deep words (linux-confirmed, 4/4): every missing permutation
fails at its LAST symbol — the prefix embeds, but no occurrence of the final symbol remains.
Culprits are word-local (6/3/9/2 across words), so the kernel targets the *invariant*, not a
fixed symbol: warm-start from the deepest words and bias proposals toward placing the
CURRENT word's culprit symbols into the tail window.

Move mix (acceptance stays coverage-only, as in batch 2):
  TARGETED (p=0.4): pick culprit symbol c weighted by the LIVE miss histogram, pick a tail
    slot j (last TAIL_WINDOW positions) with word[j] != c, pick a non-tail occurrence i of c,
    propose swap(i, j) — directly adds a late occurrence of c.
  UNIFORM  (p=0.6): plain swap anywhere.
Culprit histogram recomputed from the exact signature whenever best improves (gaps are tiny,
enumeration is cheap). Low-temperature schedule: this is plateau-walking + repair, not
exploration.
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

from supersequence_family import exact_permutation_coverage
from deep_n10 import signature
from desktop_arm import coverage_jit

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
LENGTH = 82
REQUIRED = factorial(N)
TAIL_WINDOW = 10
TARGET_P = 0.4


def cov_fast(word_list) -> int:
    return int(coverage_jit(np.asarray(word_list, dtype=np.int64), N))


def culprit_weights(word):
    _, _, culprit = signature(word)
    total = sum(culprit.values())
    return {int(s): c / total for s, c in culprit.items()} if total else {}


def targeted_move(word, weights, rng):
    if not weights:
        return None
    symbols = list(weights.keys())
    probs = [weights[s] for s in symbols]
    c = rng.choices(symbols, weights=probs, k=1)[0]
    tail_slots = [j for j in range(LENGTH - TAIL_WINDOW, LENGTH) if word[j] != c]
    body_occs = [i for i in range(LENGTH - TAIL_WINDOW) if word[i] == c]
    if not tail_slots or not body_occs:
        return None
    return rng.choice(body_occs), rng.choice(tail_slots)


def repair(word, budget, start_t, end_t, rng, label, log_every=25000):
    current = list(word)
    cur = cov_fast(current)
    best, best_cov = list(current), cur
    weights = culprit_weights(best)
    t0 = time.perf_counter()
    for step in range(1, budget + 1):
        temp = start_t * (end_t / start_t) ** ((step - 1) / max(1, budget - 1))
        move = targeted_move(current, weights, rng) if rng.random() < TARGET_P else None
        if move is None:
            move = rng.randrange(LENGTH), rng.randrange(LENGTH)
        i, j = move
        if current[i] == current[j]:
            continue
        current[i], current[j] = current[j], current[i]
        c2 = cov_fast(current)
        d = c2 - cur
        if d >= 0 or rng.random() < math.exp(d / temp):
            cur = c2
            if cur > best_cov:
                best, best_cov = list(current), cur
                weights = culprit_weights(best)  # re-aim at the new miss set
        else:
            current[i], current[j] = current[j], current[i]
        if step % log_every == 0:
            rate = step / (time.perf_counter() - t0)
            print(f"  [{label} {step}] best gap {REQUIRED - best_cov}  ({rate:.0f} steps/s)")
        if best_cov == REQUIRED:
            print(f"  *** {label}: FULL COVERAGE — CANDIDATE 82 ***")
            break
    return best, best_cov


def load_start_words():
    words = []
    with open("desktop_arm_result.json", encoding="utf-8") as handle:
        d = json.load(handle)
        words.append(("W23-lifted66", d["word"]))
    with open("batch2_result.json", encoding="utf-8") as handle:
        for r in json.load(handle):
            if r["arm"] == "CONTROL":
                words.append((f"W{r['gap']}-winner", r["word"]))
    return words


def main(budget, restarts):
    starts = load_start_words()
    print(f"ENDGAME KERNEL — {len(starts)} start words, {restarts} restarts x {budget} steps each, "
          f"tail window {TAIL_WINDOW}, targeted p={TARGET_P}")
    overall_best, overall_cov, overall_label = None, -1, ""
    results = []
    for name, word in starts:
        start_gap = REQUIRED - cov_fast(word)
        print(f"\nSTART {name}: gap {start_gap}")
        for r in range(restarts):
            rng = random.Random(9000 + r * 100 + start_gap)
            label = f"{name}/r{r}"
            best, best_cov = repair(word, budget, 30.0, 0.2, rng, label)
            gap = REQUIRED - best_cov
            print(f"[{label}] final gap {gap}")
            results.append({"start": name, "restart": r, "gap": gap, "word": best})
            if best_cov > overall_cov:
                overall_best, overall_cov, overall_label = best, best_cov, label
            if best_cov == REQUIRED:
                break
        if overall_cov == REQUIRED:
            break

    gap = REQUIRED - overall_cov
    slow = REQUIRED - exact_permutation_coverage(overall_best, N)
    print(f"\n=== ENDGAME RESULT: best gap {gap} from {overall_label} (slow re-verify {slow}) ===")
    out = {"best_gap": gap, "slow_gap": slow, "from": overall_label,
           "word": overall_best, "runs": results}
    if 0 < gap:
        _, depth, culprit = signature(overall_best)
        out["fail_depth"] = depth
        out["culprit"] = culprit
        print("fail-depth:", depth, " culprit:", culprit)
    with open("endgame_result.json", "w", encoding="utf-8") as handle:
        json.dump(out, handle)
    print("saved -> endgame_result.json")
    if gap == 0:
        print("word =", overall_best)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=200_000)
    parser.add_argument("--restarts", type=int, default=3)
    args = parser.parse_args()
    main(args.budget, args.restarts)
