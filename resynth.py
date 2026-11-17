"""resynth.py — SUFFIX RESYNTHESIS: exact tail reconstruction (design msg 5c0ba5a1).

Cut-property (proof sketch, one paragraph): leftmost-greedy embedding of a permutation p into a
word w reaches, after matching k symbols, the minimal possible pointer among ALL embeddings of
p[:k] into w. Hence if p embeds via any split u.v (u in w[:c], v in w[c:]), greedy-in-prefix
matches k* >= |u| symbols, and p[k*:] is a suffix of v, so p[k*:] embeds in w[c:] too. Converse
is trivial. Therefore: p embeds in w  IFF  its greedy REMAINDER after w[:c] embeds in w[c:].
Coverage is exactly "every remainder tuple embeds in the suffix" — the suffix can be resynthesized
independently of how the prefix was found.

Pipeline per cut c:
  1. REMAINDERS: walk the greedy-embedding tree of the prefix; collect the DISTINCT set R of
     remainder tuples over all n! permutations (dedup structural: a failure with j symbols left
     contributes s.(every ordering of rest) — recorded as (s, frozenset(rest)) blocks and expanded
     lazily into the search's trie-free suffix representation).
  2. EXACT SEARCH: IDA* over suffix symbols. State = frozenset of pending remainder suffixes
     (duplicates collapse). Lower bound = max(longest pending tuple, sum over symbols of the max
     per-tuple demand). Depth budget = target suffix length m.
     Verdict: SUFFIX FOUND (candidate word, slow-oracle verified) or PROVABLY-NO-SUFFIX at (c, m).

Validation gate (run FIRST, --validate): the known-complete 66 (n=9) is cut and resynthesized;
the search MUST find a suffix at the original length (the original tail is a witness). A method
that fails its witness is broken; do not trust n=10 output until this gate is green.

Block explosion honesty: a failure at mask-size j contributes j-symbol-first blocks whose
expansions are (j-1)! orderings. We do NOT expand: a block (s, rest) embeds in suffix S iff
s matches at some position and THEN every ordering of rest embeds after it — equivalently the
sub-block (rest as a full set) must embed as ALL orderings, which is itself "suffix of S after s
must contain all perms of rest". We handle blocks EXACTLY via the recursive requirement
all_perms_embed(S', rest_set) — checkable by the same coverage DP on the smaller alphabet subset.
For the search we conservatively expand blocks with |rest| <= EXPAND_MAX into explicit tuples and
BAIL if any bigger block survives at that cut (cut deeper -> blocks shrink)."""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from functools import lru_cache
from math import factorial

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

EXPAND_MAX = 4          # expand blocks with up to this many trailing symbols ((k-1)! tuples each)
TUPLE_CAP = 300_000     # bail if the distinct-tuple set exceeds this


def build_nextpos(word, n):
    length = len(word)
    nextpos = [[length] * n for _ in range(length + 1)]
    for p in range(length - 1, -1, -1):
        row = nextpos[p + 1].copy()
        row[word[p]] = p
        nextpos[p] = row
    return nextpos


def remainder_blocks(word, n, cut):
    """Distinct remainder structure after greedy-embedding all n! perms against word[:cut].
    Returns set of blocks (first_sym, rest_mask); the full remainder set is
    { (first,) + sigma : sigma a permutation of rest }. Empty set <=> all perms complete
    in the prefix. Requires cut <= len(word)."""
    assert cut <= len(word), "cut beyond word length"
    nextpos = build_nextpos(word[:cut], n)
    length = cut
    blocks = set()

    def rec(mask, ptr):
        m = mask
        while m:
            bit = m & -m
            s = bit.bit_length() - 1
            m ^= bit
            occ = nextpos[ptr][s]
            if occ >= length:
                rest = mask ^ bit
                blocks.add((s, rest))
            else:
                rec(mask ^ bit, occ + 1)

    rec((1 << n) - 1, 0)
    return blocks


def expand_blocks(blocks, n):
    """Blocks -> explicit distinct remainder tuples. None if a block is too big to expand."""
    tuples = set()
    for s, rest_mask in blocks:
        rest = [t for t in range(n) if rest_mask & (1 << t)]
        if len(rest) > EXPAND_MAX:
            return None
        for sigma in itertools.permutations(rest):
            tuples.add((s,) + sigma)
            if len(tuples) > TUPLE_CAP:
                return None
    return tuples


def search_suffix(tuples, n, m):
    """Fixed-budget DFS with transposition table (audit note: not iterative deepening):
    find a length-<=m word over 0..n-1 containing every tuple as a subsequence, or prove
    none exists. State = frozenset of pending suffixes. Soundness of the memo prune and
    completeness of the heads-only branching: audited 2026-07-12 (blind correctness lens,
    1080 brute-force trials; see audit_bruteforce_crosscheck.py for the execution lens)."""
    if not tuples:
        return []

    def lb(state):
        longest = max((len(t) for t in state), default=0)
        demand = [0] * n
        for t in state:
            cnt = [0] * n
            for x in t:
                cnt[x] += 1
            for s in range(n):
                if cnt[s] > demand[s]:
                    demand[s] = cnt[s]
        return max(longest, sum(demand))

    seen = {}

    def dfs(state, depth_left, path):
        if not state:
            return path
        if lb(state) > depth_left:
            return None
        prev = seen.get(state)
        if prev is not None and prev >= depth_left:
            return None
        seen[state] = depth_left
        # candidate symbols: only those that advance at least one pending tuple, prefer
        # symbols that head the longest tuples (they're on the critical path)
        heads = {}
        for t in state:
            heads.setdefault(t[0], 0)
            heads[t[0]] = max(heads[t[0]], len(t))
        for s in sorted(heads, key=lambda x: -heads[x]):
            new_state = frozenset(
                (t[1:] if (t[0] == s and len(t) > 1) else t)
                for t in state if not (t[0] == s and len(t) == 1))
            got = dfs(new_state, depth_left - 1, path + [s])
            if got is not None:
                return got
        return None

    return dfs(frozenset(tuples), m, [])


def resynthesize(word, n, cut, m=None, label=""):
    """Try to rebuild a suffix of length m (default: len(word)-cut) after word[:cut].

    RETURN CONTRACT (audit finding 2026-07-12 — two meanings of None): returns the candidate
    word on SUFFIX FOUND; returns None BOTH when PROVABLY-NO-SUFFIX (a genuine nonexistence
    proof at this (cut, m)) AND when the run BAILs (block too big / tuple cap — NOTHING proved).
    The printed line distinguishes them; a caller needing the distinction must not infer
    'None => proved no suffix'. Callers in this repo treat None only as 'no candidate here'."""
    if m is None:
        m = len(word) - cut
    t0 = time.perf_counter()
    blocks = remainder_blocks(word, n, cut)
    max_block = max((bin(r).count("1") for _, r in blocks), default=0)
    tuples = expand_blocks(blocks, n)
    if tuples is None:
        print(f"[{label} c={cut}] BAIL: block too big (max rest {max_block} > {EXPAND_MAX}) "
              f"or tuple cap — cut deeper")
        return None
    print(f"[{label} c={cut}] {len(blocks)} blocks -> {len(tuples)} distinct tuples "
          f"(max block rest {max_block}) in {time.perf_counter()-t0:.1f}s; searching m={m}...")
    t0 = time.perf_counter()
    suffix = search_suffix(tuples, n, m)
    dt = time.perf_counter() - t0
    if suffix is None:
        print(f"[{label} c={cut}] PROVABLY-NO-SUFFIX at m={m}  ({dt:.1f}s exact)")
        return None
    # pad free slots arbitrarily (any symbol works if all tuples already embedded)
    suffix = suffix + [0] * (m - len(suffix))
    candidate = list(word[:cut]) + suffix
    print(f"[{label} c={cut}] SUFFIX FOUND ({dt:.1f}s): {suffix}")
    return candidate


def validate_on_66():
    """Gate: cut the known-complete 66 (n=9, A136094-verified in FINDING UPDATE 2) and
    resynthesize at the original length. Must succeed."""
    from supersequence_family import exact_permutation_coverage, is_complete
    with open("the66.json", encoding="utf-8") as handle:
        w66 = json.load(handle)["word"]
    n = 9
    assert is_complete(w66, n), "the 66 on disk is not complete?!"
    ok_all = True
    for cut in (58, 56, 54):
        cand = resynthesize(w66, n, cut, label="validate66")
        if cand is None:
            ok_all = False
            print(f"  validate66 c={cut}: FAILED to refind a suffix — method or budget broken")
            continue
        good = is_complete(cand, n)
        print(f"  validate66 c={cut}: resynthesized word complete = {good}")
        ok_all &= good
    print("VALIDATION:", "PASS" if ok_all else "FAIL")
    return ok_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--cuts", type=int, nargs="+", default=[74, 72, 70, 68])
    parser.add_argument("--source", default="endgame_result.json")
    args = parser.parse_args()

    if args.validate:
        if not validate_on_66():
            sys.exit(1)
        return

    from supersequence_family import exact_permutation_coverage
    n = 10
    required = factorial(n)
    word = json.load(open(args.source, encoding="utf-8"))["word"]
    print(f"RESYNTH target: gap-{required - exact_permutation_coverage(word, n)} word, cuts {args.cuts}")
    for cut in args.cuts:
        cand = resynthesize(word, n, cut, label="gap3")
        if cand is not None:
            gap = required - exact_permutation_coverage(cand, n)
            print(f"  candidate slow-oracle gap: {gap}")
            if gap == 0:
                print("*** FULL COVERAGE — CANDIDATE 82 (slow-oracle confirmed) ***")
                print("word =", cand)
                json.dump({"word": cand, "cut": cut}, open("candidate82.json", "w"))
                return
    print("No candidate at these cuts.")


if __name__ == "__main__":
    main()
