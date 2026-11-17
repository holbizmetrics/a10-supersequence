"""calibrate_n9.py — CALIBRATION HUNT at n=9 (operator-approved lean, 2026-07-12).

PRE-REGISTRATION (decision rule BEFORE the measurement):
  Question: can this lab's n=10 pipeline find a complete 66-word at n=9, where ground truth is
  KNOWN to exist (A062714 a(9)=66, Garnashevich 2025)?
  Protocol is the n=10 recipe verbatim, one level down, BLIND: profiles are lifted from the n=8
  record (the 52) exactly as the n=10 attack lifted the 66 — the known 66-word is NEVER used as
  seed, template, or profile source.
  Budget mirror (what n=10 got before the exact lane): profile wall-map (1500 steps/arm) ->
  4 x 1M-step anneal on the winner -> 2 endgame wave (culprit-weighted tail repair, 4 x 300k).
  DECISION RULE: gap 0 reached anywhere within budget -> TOOLS ADEQUATE (our n=10 walls become
  real evidence for a(10)=83). Budget exhausted, gap > 0 -> TOOL CEILING measured (n=10 failure
  is uninformative about the 82; whatever later closes the n=9 gap is the recipe for the 82).
  No third outcome; no post-hoc budget extension counts as PASS.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import Counter
from math import factorial

import numpy as np

from desktop_arm import coverage_jit
from supersequence_family import exact_permutation_coverage

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 9
LENGTH = 66
REQUIRED = factorial(N)


def cov(word):
    return int(coverage_jit(np.asarray(word, dtype=np.int64), N))


def lifted_profiles():
    """Lift the 52's profile one level, same procedure as the n=10 attack lifted the 66."""
    w52 = json.load(open("the52.json"))["word"]
    p52 = sorted(Counter(w52).values(), reverse=True)  # n=8 record profile
    print(f"the 52's profile (n=8 record): {p52} (sum {sum(p52)})")
    # lift: prepend a new densest symbol at max count 9, adjust to sum 66 with graded thinning —
    # mirror of how [10,10,10,9,8,8,7,7,7,6] was guessed from [9,9,9,8,7,7,6,6,5]
    cands = [
        (9, 9, 9, 8, 7, 7, 6, 6, 5),   # direct +1-symbol graded lift of the 52's shape
        (9, 9, 8, 8, 7, 7, 7, 6, 5),
        (9, 9, 9, 8, 8, 7, 6, 6, 4),
        (9, 8, 8, 8, 7, 7, 7, 6, 6),
        (9, 9, 9, 9, 7, 7, 6, 5, 5),
    ]
    return [c for c in cands if sum(c) == LENGTH and max(c) <= N]


def random_word(profile, rng):
    w = []
    for s, c in enumerate(profile):
        w.extend([s] * c)
    rng.shuffle(w)
    return w


def anneal(word, budget, t0_, t1_, rng, label, log_every=100000, culprit_weights=None,
           tail_window=9):
    current = list(word)
    cur = cov(current)
    best, best_cov = list(current), cur
    t0 = time.perf_counter()
    for step in range(1, budget + 1):
        temp = t0_ * (t1_ / t0_) ** ((step - 1) / max(1, budget - 1))
        i = j = 0
        if culprit_weights and rng.random() < 0.4:
            syms = list(culprit_weights)
            c = rng.choices(syms, weights=[culprit_weights[s] for s in syms], k=1)[0]
            tail_slots = [k for k in range(LENGTH - tail_window, LENGTH) if current[k] != c]
            body = [k for k in range(LENGTH - tail_window) if current[k] == c]
            if tail_slots and body:
                i, j = rng.choice(body), rng.choice(tail_slots)
        if i == j:
            i, j = rng.randrange(LENGTH), rng.randrange(LENGTH)
        if current[i] == current[j]:
            continue
        current[i], current[j] = current[j], current[i]
        c2 = cov(current)
        d = c2 - cur
        if d >= 0 or rng.random() < math.exp(d / temp):
            cur = c2
            if cur > best_cov:
                best, best_cov = list(current), cur
                if culprit_weights is not None:
                    culprit_weights.clear()
                    culprit_weights.update(miss_culprits(best))
        else:
            current[i], current[j] = current[j], current[i]
        if step % log_every == 0:
            rate = step / (time.perf_counter() - t0)
            print(f"  [{label} {step}] best gap {REQUIRED - best_cov}  ({rate:.0f} steps/s)")
        if best_cov == REQUIRED:
            print(f"  *** {label}: FULL COVERAGE at n=9 — 66-WORD FOUND ***")
            break
    return best, best_cov


def miss_culprits(word):
    """Ending-symbol histogram of missing perms (small gaps only) — generic-n signature."""
    L = len(word)
    nextpos = [[L] * N for _ in range(L + 1)]
    for p in range(L - 1, -1, -1):
        row = nextpos[p + 1].copy()
        row[word[p]] = p
        nextpos[p] = row
    culprit = Counter()

    def rec(mask, ptr, depth):
        m = mask
        while m:
            bit = m & -m
            s = bit.bit_length() - 1
            m ^= bit
            occ = nextpos[ptr][s]
            if occ >= L:
                rest = bin(mask ^ bit).count("1")
                culprit[s] += math.factorial(rest)
            else:
                rec(mask ^ bit, occ + 1, depth + 1)

    rec((1 << N) - 1, 0, 0)
    total = sum(culprit.values())
    return {s: c / total for s, c in culprit.items()} if total else {}


def main():
    rng = random.Random(999)
    profiles = lifted_profiles()
    print(f"PHASE 1 — wall map: {len(profiles)} lifted profiles, 1500 steps/arm")
    scored = []
    for prof in profiles:
        w = random_word(list(prof), rng)
        best, bc = anneal(w, 1500, 25000.0, 15.0, rng, label=f"map{prof[0]}{prof[1]}{prof[2]}",
                          log_every=10**9)
        scored.append((REQUIRED - bc, prof, best))
        print(f"  profile {prof}: gap {REQUIRED - bc}")
        if bc == REQUIRED:
            return finish(best)
    scored.sort()
    winner = scored[0][1]
    print(f"\nPHASE 2 — deep anneal on winner {winner}, 4 x 1M")
    deep_best, deep_cov = None, -1
    for seed in (9001, 9002, 9003, 9004):
        srng = random.Random(seed)
        w = random_word(list(winner), srng)
        best, bc = anneal(w, 1_000_000, 25000.0, 5.0, srng, label=f"deep{seed}")
        if bc > deep_cov:
            deep_best, deep_cov = best, bc
        if bc == REQUIRED:
            return finish(best)
    print(f"\nPHASE 3 — endgame kernel from gap {REQUIRED - deep_cov}, 2 waves x 4 x 300k")
    word = deep_best
    for wave in range(2):
        for r in range(4):
            srng = random.Random(7000 + wave * 100 + r)
            weights = miss_culprits(word)
            best, bc = anneal(word, 300_000, 30.0, 0.2, srng, label=f"end{wave}.{r}",
                              culprit_weights=dict(weights))
            if bc > deep_cov:
                deep_best, deep_cov = best, bc
                word = best
            if bc == REQUIRED:
                return finish(best)
    gap = REQUIRED - deep_cov
    print(f"\n=== CALIBRATION VERDICT: FAIL (tool ceiling) — best gap {gap} at full budget ===")
    print("Per pre-registration: n=10 negative results are UNINFORMATIVE about the 82;")
    print("the n=9 gap is now the tool-development target (closing it = recipe for the 82).")
    json.dump({"verdict": "TOOL-CEILING", "best_gap": gap, "word": deep_best},
              open("calibrate_n9_result.json", "w"))


def finish(word):
    slow = exact_permutation_coverage(word, N)
    ok = slow == REQUIRED
    print(f"\n=== CALIBRATION VERDICT: {'PASS (tools adequate)' if ok else 'INSTRUMENT BUG'} ===")
    print(f"slow-oracle re-verify: {REQUIRED - slow} missing")
    if ok:
        w66_known = json.load(open("the66.json"))["word"]
        print("word  =", word)
        print("same as Garnashevich's?", word == w66_known,
              "(different word is equally valid — any complete 66 passes)")
        print("Per pre-registration: the n=10 walls now count as REAL evidence toward a(10)=83.")
    json.dump({"verdict": "PASS" if ok else "BUG", "word": word},
              open("calibrate_n9_result.json", "w"))


if __name__ == "__main__":
    main()
