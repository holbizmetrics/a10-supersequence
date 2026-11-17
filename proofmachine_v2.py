"""proofmachine_v2.py — the NONEXISTENCE prover, v2: BLOCK-STATE algebra.

THE STRUCTURAL FACT (bridge-tested below before anything counts): every state reachable from
the empty prefix is exactly a set of BLOCKS (s, R) = "all orderings of R, prefixed by s, must
still embed" — the root is {(s, U\\{s}) : s in U}, and emission is closed in block space:
  emit x:  block (s,R), s != x  ->  unchanged
           block (x,{})         ->  satisfied, dropped
           block (x,R), R != {} ->  {(r, R\\{r}) : r in R}
DOMINANCE: (s,R) is implied by (s,R') when R subset R' (any ordering of R extends to one of R');
states are kept as antichains (drop dominated) — sound, exact.

LOWER BOUND (each term admissible; max):
  (a) 1 + max |R|  (longest pending tuple);
  (b) #distinct referenced symbols (per-symbol demand is 0/1 in block space);
  (c) pair term: two blocks, shared rest-symbols ordered OPPOSITELY -> concrete tuple pair,
      exact SCS via DP, + count of referenced symbols outside the pair (disjoint positions);
  (d) UNIVERSE term: if for universe u (= {s} | R, popcount k < n) ALL k blocks (s, u\\{s})
      are present, the suffix must be COMPLETE over u  =>  >= A_PROVEN[k], + referenced symbols
      outside u. A_PROVEN uses only literature-PROVEN values (Newey k<=7, proven per
      Radomirovic 2012 intro) — never the value being decided (k < n strictly), no circularity.

MEMO: canonical form = relabel by first-touch over blocks sorted by label-independent keys
first (imperfect canon = missed hits only, never wrong; equal canon => bijective equivalence).
Memo maps canon -> max depth_left that FAILED; bounded by MEMO_CAP (full memo stops inserting
when full — sound, only slower).

VALIDATION CONTRACT (run before any new-territory rung):
  1. bridge test — block-advance == tuple-advance on randomized states x emissions;
  2. ladder n=3/4/5 verdicts must equal v1.1's (decorrelated implementations agreeing);
  3. only then n=6 (no-27; ground truth Newey a(6)=28)."""
from __future__ import annotations

import argparse
import itertools
import random
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

A_PROVEN = {1: 1, 2: 3, 3: 7, 4: 12, 5: 19, 6: 28, 7: 39}  # Newey, proven range only
MEMO_CAP = 40_000_000
MASK_BYTES = 2   # v2.3: rest-mask needs 2 bytes for n>=9 (one byte overflowed => prover COULD NOT RUN at n=10)

# v2.3 (audit 2026-07-13): CODE FINGERPRINT for memo provenance. Any memo entry is a CONCLUSION
# derived under a specific (lb, canon, advance, A_PROVEN). Reusing entries written by different code
# is how an exhaustive prover publishes a FALSE THEOREM without any bug in its mathematics — a lens-4
# finding, reproduced live: one forged entry turned prove_no(4,12) from "WORD EXISTS" into
# "PROVED-NO" in a single node. Memos are now signed and REFUSED (hard exit) on mismatch.
def code_fingerprint():
    import hashlib, inspect
    src = "".join(inspect.getsource(fn) for fn in (advance, prune_dominated, lb, canon, _scs_pair))
    src += repr(sorted(A_PROVEN.items())) + f"|MASK_BYTES={MASK_BYTES}"
    return hashlib.sha256(src.encode()).hexdigest()


def root_state(n):
    full = (1 << n) - 1
    return frozenset((s, full ^ (1 << s)) for s in range(n))


def prune_dominated(blocks):
    """Antichain per head: drop (s,R) if some (s,R') with R subset R' (proper or equal dup)."""
    by_head = {}
    for s, r in blocks:
        by_head.setdefault(s, []).append(r)
    out = set()
    for s, rests in by_head.items():
        rests.sort(key=lambda r: -bin(r).count("1"))
        kept = []
        for r in rests:
            if not any((r & k) == r for k in kept):
                kept.append(r)
        for r in kept:
            out.add((s, r))
    return out


def advance(blocks, x):
    """Emit symbol x. Returns new frozenset of blocks (dominance-pruned)."""
    out = set()
    for s, r in blocks:
        if s != x:
            out.add((s, r))
        elif r:
            m = r
            while m:
                bit = m & -m
                m ^= bit
                out.add((bit.bit_length() - 1, r ^ bit))
        # (x, {}) satisfied -> dropped
    return frozenset(prune_dominated(out))


def heads(blocks):
    return {s for s, _ in blocks}


def referenced_mask(blocks):
    m = 0
    for s, r in blocks:
        m |= (1 << s) | r
    return m


def _scs_pair(t1, t2):
    l1, l2 = len(t1), len(t2)
    dp = [[0] * (l2 + 1) for _ in range(l1 + 1)]
    for i in range(l1 - 1, -1, -1):
        for j in range(l2 - 1, -1, -1):
            dp[i][j] = dp[i + 1][j + 1] + 1 if t1[i] == t2[j] else max(dp[i + 1][j], dp[i][j + 1])
    return l1 + l2 - dp[0][0]


def lb(blocks, n):
    if not blocks:
        return 0
    ref = referenced_mask(blocks)
    n_ref = bin(ref).count("1")
    longest = 1 + max(bin(r).count("1") for _, r in blocks)
    best = max(longest, n_ref)
    # pair term on the two largest blocks (opposite shared-order tuples, exact SCS)
    big = sorted(blocks, key=lambda b: -bin(b[1]).count("1"))[:3]
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            (s1, r1), (s2, r2) = big[i], big[j]
            shared = r1 & r2
            sh = [t for t in range(n) if shared & (1 << t)]
            o1 = [t for t in range(n) if (r1 & ~shared) & (1 << t)]
            o2 = [t for t in range(n) if (r2 & ~shared) & (1 << t)]
            t1 = (s1,) + tuple(sh) + tuple(o1)
            t2 = (s2,) + tuple(reversed(sh)) + tuple(o2)
            pair_mask = (1 << s1) | (1 << s2) | r1 | r2
            outside = bin(ref & ~pair_mask).count("1")
            v = _scs_pair(t1, t2) + outside
            if v > best:
                best = v
    # universe term: complete-over-u requirement
    by_universe = {}
    for s, r in blocks:
        u = (1 << s) | r
        by_universe.setdefault(u, set()).add(s)
    for u, ss in by_universe.items():
        k = bin(u).count("1")
        if k < n and k in A_PROVEN and len(ss) == k:
            v = A_PROVEN[k] + bin(ref & ~u).count("1")
            if v > best:
                best = v
    return best


def canon(blocks, n):
    """Relabel by first-touch over blocks sorted by label-independent keys first.
    Imperfect (label-dependent tiebreaks) but sound: equal canon => bijective equivalence."""
    def label_free_key(b):
        s, r = b
        return (bin(r).count("1"),)
    order = sorted(blocks, key=lambda b: (label_free_key(b), b))
    mapping = {}
    def lab(s):
        if s not in mapping:
            mapping[s] = len(mapping)
        return mapping[s]
    out = []
    for s, r in order:
        ns = lab(s)
        rest = sorted(lab(t) for t in range(n) if r & (1 << t))
        nr = 0
        for t in rest:
            nr |= 1 << t
        out.append((ns, nr))
    # PACKED key (v2.1, after the 38M-node OOM-suspect kill): fixed-width per block —
    # ~10-20x smaller memo keys than nested tuples. Bijective encoding => memo semantics unchanged.
    #
    # v2.3 FIX (audit 2026-07-13, lens-4 finding, reproduced): the old encoding emitted ONE byte for
    # the mask, so at n>=9 the mask exceeds 255 and bytes() raised ValueError — i.e. THE PROVER COULD
    # NOT RUN AT ITS OWN TARGET (n=10). Now: 1 byte head + MASK_BYTES bytes mask (big-endian),
    # fixed-width => still injective (no aliasing), and valid for every n we will ever run.
    return b"".join(bytes((s_,)) + m_.to_bytes(MASK_BYTES, "big") for s_, m_ in sorted(out))


def prove_no(n, length, log_every=2_000_000, persist_every=5_000_000):
    """True = PROVED no complete word of length `length` over n symbols; False = word exists.
    MEMO PERSISTENCE (v2.2, after two silent kills at ~36-40M nodes): the memo is snapshotted
    to memo_n{n}_L{length}.pkl every persist_every nodes (atomic tmp+rename) and loaded on
    start — a killed run's successor fast-forwards through the memoized region instead of
    re-searching it. Sound: the memo only ever prunes completed failures."""
    import pickle, os
    memo_path = f"memo_n{n}_L{length}.pkl"
    fingerprint = code_fingerprint()
    seen = {}
    if os.path.exists(memo_path):
        with open(memo_path, "rb") as fh:
            payload = pickle.load(fh)
        # v2.3: REFUSE unauthenticated or foreign memos. A memo is a set of CONCLUSIONS derived under
        # a specific code version; silently reusing one written by different code = false theorem.
        if not isinstance(payload, dict) or payload.get("__fingerprint__") != fingerprint:
            print(f"  *** REFUSING MEMO {memo_path}: missing/mismatched code fingerprint.")
            print(f"  *** Its entries were derived under DIFFERENT code and may be WRONG.")
            print(f"  *** Delete it and re-run from scratch. Refusing to publish a proof on foreign bytes.")
            sys.exit(2)
        if payload.get("n") != n or payload.get("length") != length:
            print(f"  *** REFUSING MEMO {memo_path}: parameter mismatch."); sys.exit(2)
        seen = payload["entries"]
        print(f"  [resume] loaded memo: {len(seen):,} entries (fingerprint OK) from {memo_path}")
    nodes = [0]
    t0 = time.perf_counter()
    sys.setrecursionlimit(1_000_000)

    def snapshot():
        payload = {"__fingerprint__": fingerprint, "n": n, "length": length, "entries": seen}
        with open(memo_path + ".tmp", "wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
            fh.flush(); os.fsync(fh.fileno())          # v2.3: no torn snapshots
        os.replace(memo_path + ".tmp", memo_path)
        print(f"  [snapshot] memo {len(seen):,} -> {memo_path}")

    def dfs(blocks, depth_left):
        nodes[0] += 1
        if nodes[0] % log_every == 0:
            print(f"  ... {nodes[0]:,} nodes, memo {len(seen):,}, {time.perf_counter()-t0:.0f}s")
        if nodes[0] % persist_every == 0:
            snapshot()
        if not blocks:
            return False
        if lb(blocks, n) > depth_left:
            return True
        key = canon(blocks, n)
        prev = seen.get(key)
        if prev is not None and depth_left <= prev:
            return True
        children = {}
        for x in heads(blocks):
            children[advance(blocks, x)] = None
        for child in children:
            if not dfs(child, depth_left - 1):
                return False
        if len(seen) < MEMO_CAP:
            seen[key] = depth_left
        return True

    verdict = dfs(root_state(n), length)
    dt = time.perf_counter() - t0
    snapshot()
    print(f"[v2] n={n} L={length}: {'PROVED-NO' if verdict else 'WORD EXISTS (no-proof fails)'}"
          f"  ({nodes[0]:,} nodes, memo {len(seen):,}, {dt:.1f}s)")
    return verdict


# ---------- validation contract ----------

def blocks_to_tuples(blocks, n):
    out = set()
    for s, r in blocks:
        rest = [t for t in range(n) if r & (1 << t)]
        for sigma in itertools.permutations(rest):
            out.add((s,) + sigma)
    return out


def tuple_advance(tuples, x):
    return frozenset(
        (t[1:] if (t[0] == x and len(t) > 1) else t)
        for t in tuples if not (t[0] == x and len(t) == 1))


def dominance_close_tuples(tuples):
    """Tuple-space image of dominance: drop t if it is a subsequence of another pending t'
    with the same head (covering t' covers t). Mirrors block dominance for the bridge test."""
    def is_subseq(a, b):
        it = iter(b)
        return all(x in it for x in a)
    keep = set()
    ts = sorted(tuples, key=len, reverse=True)
    for t in ts:
        if not any(t2[0] == t[0] and len(t2) > len(t) and is_subseq(t, t2) for t2 in keep):
            keep.add(t)
    return frozenset(keep)


def bridge_test(rng, rounds=300):
    """block-advance == tuple-advance (modulo dominance closure) on randomized states."""
    for k in range(rounds):
        n = rng.choice((3, 4, 5))
        state = root_state(n)
        for _ in range(rng.randrange(0, 2 * n)):
            hs = sorted(heads(state))
            if not hs or not state:
                break
            x = rng.choice(hs + [rng.randrange(n)])
            t_before = blocks_to_tuples(state, n)
            state_after = advance(state, x)
            t_after_via_blocks = blocks_to_tuples(state_after, n)
            t_after_direct = dominance_close_tuples(tuple_advance(frozenset(t_before), x))
            assert t_after_via_blocks == t_after_direct, (n, x, sorted(state))
            state = state_after
    print(f"[bridge] block-advance == tuple-advance on {rounds} randomized walks — PASSES")


LADDER = {3: 7, 4: 12, 5: 19, 6: 28, 7: 39}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rungs", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--skip-bridge", action="store_true")
    args = parser.parse_args()
    if not args.skip_bridge:
        bridge_test(random.Random(2026))
    all_ok = True
    for n in args.rungs:
        a_n = LADDER[n]
        # v2.3 (audit 2026-07-13): the YES-DIRECTION, which this ladder was MISSING.
        # Two lenses found this independently and it is the deepest finding of the audit:
        # the old ladder only ran prove_no(n, a(n)-1), whose true answer is True — and an
        # OVER-PRUNING bug can ONLY turn False into True. So the ladder was structurally
        # INCAPABLE of catching an over-pruner: it was green precisely where the bug hides.
        # prove_no(n, a(n)) MUST be False (a word of length a(n) exists, by definition of a(n)).
        # This is the cheap guard against the exact failure class the whole machine risks.
        print(f"=== rung n={n}: YES-direction — prove_no({n}, {a_n}) must be False (a word EXISTS) ===")
        if prove_no(n, a_n) is not False:
            print(f"  *** OVER-PRUNING BUG: claimed no word of length a({n})={a_n} exists. ***")
            all_ok = False
        print(f"=== rung n={n}: NO-direction — prove no-{a_n - 1} (ground truth a({n})={a_n}) ===")
        ok = prove_no(n, a_n - 1)
        if not ok:
            print(f"  *** RUNG FAILED — impossible; BUG ***")
            all_ok = False
    print("LADDER:", "ALL RUNGS GREEN" if all_ok else "FAILURE — do not proceed")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
