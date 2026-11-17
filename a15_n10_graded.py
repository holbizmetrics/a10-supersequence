"""a15_n10_graded.py — LOCAL probe of the n=10 length-82 graded-profile space (the 82-attack).

Question: the 66 (n=9 record) wins via a sparsity GRADIENT [9,9,9,8,7,7,6,6,5] on a dense-trio
scaffold. Does that mechanism compose one level up — is there an 82 = graded profile at n=10?

Two arms, so the substrate's value is measurable (A15 discipline):
  ARM A (profile-only): fix the multiset to a graded profile summing to 82; anneal with
        profile-preserving SWAP moves only. (Grok's suggestion, as baseline.)
  ARM B (profile + structure): additionally SEED with the 66's architecture lifted one level —
        scaffold the dense trio at regular gaps, graded symbols thinning, tail = clean permutation
        bookended by the trio — then anneal with swaps that PROTECT the tail permutation.

Honest framing: the gap-1 wall was measured on UNCONSTRAINED moves; whether it recurs inside the
graded subspace is exactly what this measures. Expected outcome is a wall-map (how close each
profile/arm gets), which itself sharpens dispatch v4. A hit (coverage == 10!) would be a candidate
82 -> clean re-verify + cold-check by linux before any claim.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import time
from collections import Counter
from math import factorial

from supersequence_family import exact_permutation_coverage

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
LENGTH = 82
REQUIRED = factorial(N)

# candidate graded profiles summing to 82 (descending, max 10 per symbol), the lifted-66 first
PROFILES = [
    (10, 10, 10, 9, 8, 8, 7, 7, 7, 6),
    (10, 10, 9, 9, 8, 8, 8, 7, 7, 6),
    (10, 10, 10, 9, 9, 8, 7, 7, 6, 6),
    (10, 9, 9, 9, 8, 8, 8, 8, 7, 6),
    (10, 10, 10, 10, 8, 8, 7, 7, 6, 6),
]


def cov(word):
    return exact_permutation_coverage(word, N)


def profile_of(word):
    c = Counter(word)
    return tuple(sorted(c.values(), reverse=True))


def random_graded_word(profile, rng):
    word = []
    for symbol, count in enumerate(profile):
        word.extend([symbol] * count)
    rng.shuffle(word)
    return word


def structured_seed(profile, rng):
    """ARM B seed: lift the 66's architecture. Dense trio 0,1,2 scaffolds at regular spacing;
    graded symbols fill between; tail forced to a permutation bookended by the trio."""
    counts = list(profile)  # counts[s] = target multiplicity of symbol s
    # reserve the final 10 slots for a clean permutation ending ...0,1,2 (trio bookend)
    tail_perm = [3, 4, 5, 6, 7, 8, 9, 0, 1, 2]
    remaining = counts.copy()
    for s in tail_perm:
        remaining[s] -= 1
    # body: interleave — scaffold symbols 0,1,2 at regular gaps, others cycled by remaining count
    body_len = LENGTH - len(tail_perm)
    body = []
    pool = []
    for s in range(N):
        pool.extend([s] * remaining[s])
    # order the pool: repeatedly emit (densest-remaining non-recent symbol), approximating the 66's
    # even spread of dense symbols
    rem = remaining.copy()
    recent = []
    for _ in range(body_len):
        candidates = sorted(range(N), key=lambda s: -rem[s])
        pick = next((s for s in candidates if rem[s] > 0 and s not in recent[-2:]), None)
        if pick is None:
            pick = next(s for s in candidates if rem[s] > 0)
        body.append(pick)
        rem[pick] -= 1
        recent.append(pick)
    word = body + tail_perm
    assert profile_of(word) == tuple(sorted(profile, reverse=True)), "seed broke the profile"
    return word


def anneal(word, budget, start_T, end_T, rng, protect_tail=False, log_every=400, label=""):
    current = list(word)
    cur = cov(current)
    best, best_cov = list(current), cur
    lo = 0
    hi = LENGTH - (10 if protect_tail else 0)   # protected tail: swaps only in the body
    for step in range(1, budget + 1):
        T = start_T * (end_T / start_T) ** ((step - 1) / max(1, budget - 1))
        i, j = rng.randrange(lo, hi), rng.randrange(lo, hi)
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
            current[i], current[j] = current[j], current[i]  # revert
        if step % log_every == 0:
            print(f"    [{label} step {step}] best gap {REQUIRED - best_cov}")
        if best_cov == REQUIRED:
            print(f"    *** {label}: FULL COVERAGE at step {step} ***")
            break
    return best, best_cov


def main(budget, seed):
    rng = random.Random(seed)
    print(f"n={N} length={LENGTH} target={REQUIRED}  (82-attack local probe)")
    results = []
    for profile in PROFILES:
        print(f"\nPROFILE {profile} (sum {sum(profile)})")
        # ARM A: profile-only
        wA = random_graded_word(profile, rng)
        bA, cA = anneal(wA, budget, 30000.0, 20.0, rng, protect_tail=False, label="A")
        print(f"  ARM A (profile-only):      best gap {REQUIRED - cA}")
        # ARM B: structured seed + protected tail
        wB = structured_seed(profile, rng)
        seed_cov = cov(wB)
        bB, cB = anneal(wB, budget, 15000.0, 20.0, rng, protect_tail=True, label="B")
        print(f"  ARM B (66-template seed):  seed gap {REQUIRED - seed_cov} -> best gap {REQUIRED - cB}")
        results.append((profile, REQUIRED - cA, REQUIRED - cB))
        if cA == REQUIRED or cB == REQUIRED:
            winner = bA if cA == REQUIRED else bB
            print("\n*** CANDIDATE 82 FOUND — clean re-verify:", cov(winner) == REQUIRED, "***")
            print("word =", winner)
            return
    print("\n=== WALL MAP (gap remaining per profile) ===")
    print(f"{'profile':<36} {'ARM A':>8} {'ARM B':>8}")
    for profile, gA, gB in results:
        print(f"{str(profile):<36} {gA:>8} {gB:>8}")
    print("\nNo 82 found at this budget. The wall map above is the v4-dispatch intel.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=1500, help="anneal steps per arm per profile")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    main(args.budget, args.seed)
