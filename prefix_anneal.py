"""prefix_anneal.py — WARMTH-GAUGE prefix search (operator-commissioned 2026-07-12).

Coverage-fitness has bad fitness-distance correlation here (gap-3 was provably unfixable).
This arm anneals PREFIXES (length CUT) on a feasibility fitness instead:
  fitness(prefix) = deficit of a greedy tail-builder trying to satisfy the prefix's exact
  remainder-tuple demand in m = 82-CUT symbols  (0 deficit -> the greedy tail IS a candidate,
  which self-verifies on the slow oracle; near-0 prefixes get the exact IDA* as confirmer).

Remainder computation = resynth.py's cut-property machinery + a visited-set memo on (mask, ptr)
states (the greedy tree revisits states; blocks from a state are deterministic -> dedup valid).

Moves: symbol swaps + point mutations (profile-free — the objective doesn't care).
Seeds: the 83's first CUT symbols (best donor), deep-word prefixes, random graded."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from math import factorial

from resynth import expand_blocks, search_suffix
from supersequence_family import exact_permutation_coverage

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

N = 10
TOTAL = 82
REQUIRED = factorial(N)


def remainder_blocks_memo(prefix, n):
    """resynth.remainder_blocks + visited-set memo on (mask, ptr) — ~10x cheaper."""
    length = len(prefix)
    nextpos = [[length] * n for _ in range(length + 1)]
    for p in range(length - 1, -1, -1):
        row = nextpos[p + 1].copy()
        row[prefix[p]] = p
        nextpos[p] = row
    blocks = set()
    visited = set()

    def rec(mask, ptr):
        key = (mask, ptr)
        if key in visited:
            return
        visited.add(key)
        m = mask
        while m:
            bit = m & -m
            s = bit.bit_length() - 1
            m ^= bit
            occ = nextpos[ptr][s]
            if occ >= length:
                blocks.add((s, mask ^ bit))
            else:
                rec(mask ^ bit, occ + 1)

    rec((1 << n) - 1, 0)
    return blocks


def greedy_deficit(tuples, n, m):
    """Greedy tail-builder: m symbols, each step pick the symbol advancing the most weighted
    pending demand. Returns (deficit = #tuples unfinished, tail). Deficit 0 -> tail is a witness."""
    pending = {t: 0 for t in tuples}  # tuple -> progress pointer
    tail = []
    for _ in range(m):
        if not pending:
            break
        score = [0.0] * n
        for t, k in pending.items():
            need = t[k]
            score[need] += 1.0 + 0.5 * (len(t) - k)  # longer remaining = more urgent
        s = max(range(n), key=lambda x: score[x])
        if score[s] == 0.0:
            break
        tail.append(s)
        done = []
        for t, k in pending.items():
            if t[k] == s:
                if k + 1 == len(t):
                    done.append(t)
                else:
                    pending[t] = k + 1
        for t in done:
            del pending[t]
    return len(pending), tail


try:
    from fast_fitness import fitness_fast, tuples_set_from_arrays
    _FAST = True
except Exception:
    _FAST = False


def fitness(prefix, m):
    if _FAST:
        d, tail, arrs = fitness_fast(prefix, N, m)
        if arrs is None:
            return 10**9, None, None
        return d, tail, arrs  # arrs lazy; convert with tuples_set_from_arrays when needed
    blocks = remainder_blocks_memo(prefix, N)
    tuples = expand_blocks(blocks, N)
    if tuples is None:
        return 10**9, None, None   # block too big — very unfit
    deficit, tail = greedy_deficit(tuples, N, m)
    return deficit, tail, tuples


def seeds(cut, rng, from_harvest=None):
    """Structured prefixes only — random prefixes leave giant remainder blocks (smoke-tested
    unfit at 1e9) and waste the anneal budget. With from_harvest: generational ratchet —
    seed from the previous round's best prefixes (the FunSearch shape)."""
    if from_harvest:
        prev = json.load(open(from_harvest))
        return [(f"g2-{h['name']}", list(h["prefix"])) for h in
                sorted(prev, key=lambda h: h["deficit"])]
    out = []
    w83 = json.load(open("the83.json"))["word"]
    out.append(("83-prefix", list(w83[:cut])))
    g3 = json.load(open("endgame_result.json"))["word"]
    out.append(("gap3-prefix", list(g3[:cut])))
    runs = json.load(open("endgame_result.json"))["runs"]
    picked = 0
    seen = {tuple(g3)}
    for r in sorted(runs, key=lambda r: r["gap"]):
        key = tuple(r["word"])
        if key in seen:
            continue
        seen.add(key)
        out.append((f"{r['start']}r{r['restart']}-prefix", list(r["word"][:cut])))
        picked += 1
        if picked >= 2:
            break
    return out


def anneal(name, prefix, cut, budget, rng, exact_every=500, harvest=None):
    m = TOTAL - cut
    current = list(prefix)
    cur_def, cur_tail, _ = fitness(current, m)
    best, best_def, best_tail = list(current), cur_def, cur_tail
    print(f"[{name}] start deficit {cur_def} (m={m})")
    t0 = time.perf_counter()
    since_exact = 0
    for step in range(1, budget + 1):
        temp = 3.0 * (0.05 / 3.0) ** ((step - 1) / max(1, budget - 1))
        cand = list(current)
        if rng.random() < 0.5:
            i, j = rng.randrange(cut), rng.randrange(cut)
            cand[i], cand[j] = cand[j], cand[i]
        else:
            cand[rng.randrange(cut)] = rng.randrange(N)
        new_def, new_tail, new_tuples = fitness(cand, m)
        d = cur_def - new_def
        if d >= 0 or rng.random() < math.exp(d / temp):
            current, cur_def, cur_tail = cand, new_def, new_tail
            if cur_def < best_def:
                best, best_def, best_tail = list(current), cur_def, cur_tail
                rate = step / (time.perf_counter() - t0)
                print(f"  [{name} {step}] NEW BEST deficit {best_def}  ({rate:.1f} evals/s)")
                if best_def == 0:
                    word = best + best_tail + [0] * (m - len(best_tail))
                    gap = REQUIRED - exact_permutation_coverage(word, N)
                    print(f"  [{name}] GREEDY WITNESS — slow-oracle gap {gap}")
                    if gap == 0:
                        return word
                elif best_def <= 1 and new_tuples is not None and since_exact <= 0:
                    since_exact = exact_every
                    tset = tuples_set_from_arrays(new_tuples) if _FAST else new_tuples
                    suffix = search_suffix(tset, N, m)
                    if suffix is not None:
                        word = best + suffix + [0] * (m - len(suffix))
                        gap = REQUIRED - exact_permutation_coverage(word, N)
                        print(f"  [{name}] EXACT confirmer found suffix — slow-oracle gap {gap}")
                        if gap == 0:
                            return word
                    else:
                        print(f"  [{name}] exact confirmer: no suffix at deficit {best_def} (LB gap real)")
        since_exact -= 1
        if step % 500 == 0:
            rate = step / (time.perf_counter() - t0)
            print(f"  [{name} {step}] best deficit {best_def}  ({rate:.1f} evals/s)")
    if harvest is not None:
        harvest.append({"name": name, "cut": cut, "deficit": best_def, "prefix": best})
    return None


def main(cut, budget, seed):
    rng = random.Random(seed)
    m = TOTAL - cut
    print(f"PREFIX ANNEAL — cut {cut} (tail budget {m}), {budget} evals/seed")
    harvest = []
    for name, prefix in seeds(cut, rng, from_harvest=FROM_HARVEST):
        word = anneal(name, prefix, cut, budget, rng, harvest=harvest)
        json.dump(harvest, open(f"prefix_harvest_c{cut}.json", "w"))
        if word is not None:
            print("*** FULL COVERAGE AT 82 — CANDIDATE RECORD (slow-oracle confirmed) ***")
            print("word =", word)
            json.dump({"word": word, "from": f"prefix-anneal/{name}"},
                      open("candidate82.json", "w"))
            return
    print("No candidate this run.")


FROM_HARVEST = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cut", type=int, default=66)
    parser.add_argument("--budget", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--from-harvest", default=None,
                        help="JSON from a previous round; seeds generation N+1 (ratchet)")
    args = parser.parse_args()
    FROM_HARVEST = args.from_harvest
    main(args.cut, args.budget, args.seed)
