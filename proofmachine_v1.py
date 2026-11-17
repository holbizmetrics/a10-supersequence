"""proofmachine_v1.py — the NONEXISTENCE prover, v1: canonical states + symmetry quotient.

Job: decide "NO complete word of length L over n symbols exists" (the hard half of each
A062714 cell; YES-halves come with constructive witnesses from the search tools).

v1 over v0 (= resynth.search_suffix from the empty prefix):
  CANONICAL STATES. Coverability of a pending-suffix set by a length-m word is invariant
  under ANY bijective relabeling of symbols (the suffix's symbols are free). So states are
  memoized in canonical form: relabel symbols by first-touch order over the sorted tuple
  set. Soundness: equal canon => states related by a bijection => same fate (imperfect
  canonicalization can only MISS equivalences — slower, never wrong). The symmetry quotient
  (relabel x n!) is thereby folded into the memo, and sibling branches with identical child
  canons are deduped at the node (kills the n-fold first-move symmetry and all later ones).

SOUNDNESS ARGUMENT (each piece audited in the 2026-07-12 blind audit for v0, carried over):
  - advance(state, s) transition exactness; heads-only branching completeness;
  - LB admissibility (max of longest-tuple and per-symbol max-demand sum);
  - memo prune: seen[canon] holds the max depth_left that FAILED; prune if
    depth_left <= seen[canon]. States cannot recur along one path (total pending length
    strictly decreases), so every memo entry is a completed failure.

Validation ladder mandatory before any new-territory run: verdicts must MATCH v0/ground truth
at n=3 (no-6), n=4 (no-11), n=5 (no-18), with times recorded. New territory: n=6 (no-27),
n=7 (no-38) — both PROVEN ground truths (Newey), so even 'new territory' is calibration."""
from __future__ import annotations

import argparse
import itertools
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass


def canon(state):
    """Canonical form: relabel by first-touch over sorted tuples, then re-sort.
    Equal canon => bijectively equivalent states (sound for memo)."""
    mapping = {}
    for t in sorted(state):
        for s in t:
            if s not in mapping:
                mapping[s] = len(mapping)
    return tuple(sorted(tuple(mapping[s] for s in t) for t in state))


def _lcs(a, b):
    la, lb_ = len(a), len(b)
    dp = [[0] * (lb_ + 1) for _ in range(la + 1)]
    for i in range(la - 1, -1, -1):
        for j in range(lb_ - 1, -1, -1):
            dp[i][j] = dp[i + 1][j + 1] + 1 if a[i] == b[j] else max(dp[i + 1][j], dp[i][j + 1])
    return dp[0][0]


def lb(state, n):
    """Admissible lower bound, v1.1. Terms (each sound, take max):
      (a) longest pending tuple;
      (b) sum over symbols of max per-tuple demand (disjoint position classes);
      (c) PAIR TERM over the top-4 longest tuples: SCS(t1,t2) = |t1|+|t2|-LCS  PLUS the demand
          of symbols outside sym(t1)|sym(t2). Sound because a covering word restricted to the
          pair's symbols must contain both tuples (>= SCS), and positions holding outside
          symbols are disjoint from that restriction (>= their demand). Additive over the split."""
    longest = 0
    demand = [0] * n
    for t in state:
        if len(t) > longest:
            longest = len(t)
        cnt = [0] * n
        for x in t:
            cnt[x] += 1
        for s in range(n):
            if cnt[s] > demand[s]:
                demand[s] = cnt[s]
    best = max(longest, sum(demand))
    top = sorted(state, key=len, reverse=True)[:4]
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a, b = top[i], top[j]
            scs = len(a) + len(b) - _lcs(a, b)
            outside = sum(demand[s] for s in range(n) if s not in set(a) and s not in set(b))
            if scs + outside > best:
                best = scs + outside
    return best


def prove_no(n, length, log_every=2_000_000):
    """True  = PROVED: no complete word of length `length` over n symbols exists.
       False = a covering path was found (word exists) — verdict NO fails."""
    start = canon(frozenset(itertools.permutations(range(n))))
    seen = {}
    nodes = [0]
    t0 = time.perf_counter()

    def dfs(state, depth_left):
        nodes[0] += 1
        if nodes[0] % log_every == 0:
            print(f"  ... {nodes[0]:,} nodes, memo {len(seen):,}, {time.perf_counter()-t0:.0f}s")
        if not state:
            return False  # covered everything => a word EXISTS
        if lb(state, n) > depth_left:
            return True
        prev = seen.get(state)
        if prev is not None and depth_left <= prev:
            return True
        # branch: heads only, dedup children by canon
        heads = {}
        for t in state:
            heads.setdefault(t[0], 0)
            heads[t[0]] = max(heads[t[0]], len(t))
        children = {}
        for s in sorted(heads, key=lambda x: -heads[x]):
            child = frozenset(
                (t[1:] if (t[0] == s and len(t) > 1) else t)
                for t in state if not (t[0] == s and len(t) == 1))
            children.setdefault(canon(child), None)
        for child_c in children:
            if not dfs(child_c, depth_left - 1):
                return False
        seen[state] = depth_left
        return True

    sys.setrecursionlimit(1_000_000)
    verdict = dfs(frozenset(start), length)
    dt = time.perf_counter() - t0
    print(f"[v1] n={n} L={length}: {'PROVED-NO' if verdict else 'WORD EXISTS (no-proof fails)'}"
          f"  ({nodes[0]:,} nodes, memo {len(seen):,}, {dt:.1f}s)")
    return verdict


LADDER = {3: 7, 4: 12, 5: 19, 6: 28, 7: 39, 8: 52, 9: 66}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rungs", type=int, nargs="+", default=[3, 4, 5])
    args = parser.parse_args()
    all_ok = True
    for n in args.rungs:
        a_n = LADDER[n]
        print(f"=== rung n={n}: prove no-{a_n - 1} (ground truth: a({n})={a_n}) ===")
        ok = prove_no(n, a_n - 1)
        if not ok:
            print(f"  *** RUNG FAILED: found a word shorter than a({n}) — impossible; BUG ***")
            all_ok = False
    print("LADDER:", "ALL RUNGS GREEN" if all_ok else "FAILURE — do not proceed")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
