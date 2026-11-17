"""audit_bruteforce_crosscheck.py — blind adversarial brute-force cross-validation of resynth.py.

Independent of resynth's logic: ground truth is full enumeration of ALL n^m suffixes,
each checked with a naive two-pointer subsequence scan per permutation over the FULL
candidate word (no greedy-remainder shortcut, no nextpos table, no reuse of the oracle
under test).

Verdict mapping for resynth (driven via the underlying functions, NOT the wrapper,
because resynthesize() returns None for BOTH the BAIL path and the PROVABLY-NO path):
    BAIL   = expand_blocks returned None (no verdict claimed)
    NO     = search_suffix returned None (claimed PROVABLY-NO-SUFFIX at (c, m))
    FOUND  = search_suffix returned a suffix (claimed complete candidate)

Disagreement classes (each is CRITICAL):
    A. resynth NO  but brute force finds a working suffix
    B. resynth FOUND but its candidate is NOT complete per the naive checker
    C. resynth FOUND but brute force finds NO working suffix (impossible if B clean,
       still checked)
Plus a consistency check that resynthesize()'s printed branch matches the direct path.
"""
from __future__ import annotations

import io
import itertools
import random
import sys
import time
from contextlib import redirect_stdout

sys.path.insert(0, r"D:\FromGitHubEtc\Prometheus-Crystal-Lab-Auto\.prometheus\explore\pcla-funsearch-loop")
import resynth  # noqa: E402


# ---------------- independent naive machinery ----------------

def contains_perm(word, p):
    """Two-pointer scan: is p a subsequence of word?"""
    i = 0
    lp = len(p)
    for x in word:
        if i < lp and x == p[i]:
            i += 1
    return i == lp


def contains_all_perms(word, n):
    return all(contains_perm(word, p) for p in itertools.permutations(range(n)))


def brute_force_suffix(prefix, n, m):
    """Enumerate ALL n^m suffixes; return first suffix making prefix+suffix complete, else None."""
    perms = list(itertools.permutations(range(n)))
    # trivial monotonicity fact (independent of resynth): a perm already in the prefix is
    # in every extension — skip it per-suffix, but ALWAYS scan the FULL candidate word
    # for the rest (no pointer/remainder caching).
    missing = [p for p in perms if not contains_perm(prefix, p)]
    if not missing:
        return []
    for suf in itertools.product(range(n), repeat=m):
        cand = prefix + list(suf)
        if all(contains_perm(cand, p) for p in missing):
            return list(suf)
    return None


# ---------------- resynth drivers ----------------

def resynth_verdict(word, n, c, m):
    blocks = resynth.remainder_blocks(word, n, c)
    tuples = resynth.expand_blocks(blocks, n)
    if tuples is None:
        return ("BAIL", None)
    suf = resynth.search_suffix(tuples, n, m)
    if suf is None:
        return ("NO", None)
    suf = suf + [0] * (m - len(suf))
    return ("FOUND", list(word[:c]) + suf)


def resynthesize_wrapper_branch(word, n, c, m):
    """Run the real resynthesize(); classify which branch it printed."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = resynth.resynthesize(word, n, c, m, label="audit")
    text = buf.getvalue()
    if "BAIL" in text:
        branch = "BAIL"
    elif "PROVABLY-NO-SUFFIX" in text:
        branch = "NO"
    elif "SUFFIX FOUND" in text:
        branch = "FOUND"
    else:
        branch = "???"
    return branch, out


# ---------------- test loop ----------------

def run_case(word, n, c, m, stats, disagreements):
    verdict, candidate = resynth_verdict(word, n, c, m)
    branch, wrapper_out = resynthesize_wrapper_branch(word, n, c, m)
    stats["cases"] += 1
    stats[verdict] += 1
    repro = dict(word=word, n=n, c=c, m=m)

    # wrapper-vs-direct consistency
    if branch != verdict or ((wrapper_out is None) != (candidate is None)):
        disagreements.append(("WRAPPER-MISMATCH", repro,
                              f"direct={verdict} wrapper_branch={branch}"))
    if verdict == "FOUND" and wrapper_out is not None and wrapper_out != candidate:
        # different witness is fine only if both complete; check wrapper's too
        if not contains_all_perms(wrapper_out, n):
            disagreements.append(("B-WRAPPER-BAD-WITNESS", repro, f"wrapper cand={wrapper_out}"))

    prefix = list(word[:c])
    bf = brute_force_suffix(prefix, n, m)

    if verdict == "FOUND":
        if not contains_all_perms(candidate, n):
            disagreements.append(("B-BAD-WITNESS", repro, f"cand={candidate}"))
        elif bf is None:
            disagreements.append(("C-FOUND-BUT-BRUTE-NO", repro, f"cand={candidate}"))
        else:
            stats["agree"] += 1
    elif verdict == "NO":
        if bf is not None:
            disagreements.append(("A-NO-BUT-SUFFIX-EXISTS", repro, f"brute suffix={bf}"))
        else:
            stats["agree"] += 1
    else:  # BAIL — no verdict claimed; record only, never counts as agreement or disagreement
        stats["bail_detail"].append((repro, "exists" if bf is not None else "none"))


def main():
    rng = random.Random(20260712)
    stats = {"cases": 0, "agree": 0, "FOUND": 0, "NO": 0, "BAIL": 0, "bail_detail": []}
    disagreements = []
    t0 = time.perf_counter()

    # --- n=3: 100 words, len 6..9, random cut, m in {len-c, len-c-1} ---
    for _ in range(100):
        L = rng.randint(6, 9)
        word = [rng.randrange(3) for _ in range(L)]
        c = rng.randint(2, L - 2)
        for m in (L - c, L - c - 1):
            if m < 1:
                continue
            run_case(word, 3, c, m, stats, disagreements)

    # --- n=4: 100 words, len 10..14, cut chosen so m = len-c <= 6 (brute-force budget) ---
    for _ in range(100):
        L = rng.randint(10, 14)
        word = [rng.randrange(4) for _ in range(L)]
        c = rng.randint(max(2, L - 6), L - 2)
        for m in (L - c, L - c - 1):
            if m < 1:
                continue
            run_case(word, 4, c, m, stats, disagreements)

    # --- stress: very short prefixes (c=2,3) => large remainder blocks ---
    # n=3 with len 8..9 and n=4 with len 9 (m<=7 keeps brute force tractable)
    for _ in range(4):
        L = rng.randint(8, 9)
        word = [rng.randrange(3) for _ in range(L)]
        for c in (2, 3):
            run_case(word, 3, c, L - c, stats, disagreements)
    for _ in range(4):
        L = 9
        word = [rng.randrange(4) for _ in range(L)]
        for c in (2, 3):
            run_case(word, 4, c, L - c, stats, disagreements)

    # --- explicit bail-path probe: force EXPAND_MAX down so blocks refuse to expand ---
    bail_probe = []
    old = resynth.EXPAND_MAX
    try:
        resynth.EXPAND_MAX = 1
        for _ in range(6):
            L = 9
            word = [rng.randrange(4) for _ in range(L)]
            c = 2
            m = L - c
            blocks = resynth.remainder_blocks(word, 4, c)
            maxrest = max((bin(r).count("1") for _, r in blocks), default=0)
            tuples = resynth.expand_blocks(blocks, 4)
            branch, wrapper_out = resynthesize_wrapper_branch(word, 4, c, m)
            bail_probe.append(dict(word=word, maxrest=maxrest,
                                   expand_none=(tuples is None), branch=branch,
                                   wrapper_ret_none=(wrapper_out is None)))
            if maxrest > 1:
                if tuples is not None:
                    disagreements.append(("BAIL-NOT-TAKEN", dict(word=word, c=c, m=m),
                                          f"maxrest={maxrest} but expand_blocks expanded"))
                if branch != "BAIL":
                    disagreements.append(("BAIL-MISLABELED", dict(word=word, c=c, m=m),
                                          f"wrapper printed branch={branch}, expected BAIL"))
    finally:
        resynth.EXPAND_MAX = old

    dt = time.perf_counter() - t0

    print("=" * 70)
    print(f"TOTAL CASES RUN : {stats['cases']}")
    print(f"  FOUND verdicts: {stats['FOUND']}")
    print(f"  NO verdicts   : {stats['NO']}")
    print(f"  BAIL (no verdict claimed): {stats['BAIL']}")
    print(f"AGREEMENTS      : {stats['agree']} (of {stats['FOUND'] + stats['NO']} verdict-bearing cases)")
    print(f"DISAGREEMENTS   : {len(disagreements)}")
    for tag, repro, detail in disagreements:
        print(f"  [{tag}] {repro}  {detail}")
    print(f"BAIL-PROBE (EXPAND_MAX=1, 6 words, c=2): "
          f"{sum(1 for b in bail_probe if b['branch'] == 'BAIL')} / {len(bail_probe)} took BAIL branch; "
          f"all wrapper returns None: {all(b['wrapper_ret_none'] for b in bail_probe)}")
    for b in bail_probe:
        print(f"    maxrest={b['maxrest']} expand_none={b['expand_none']} branch={b['branch']}")
    print(f"RUNTIME         : {dt:.1f}s")
    print("VERDICT         :", "CLEAN" if not disagreements else "CRITICAL FINDINGS ABOVE")
    return 0 if not disagreements else 1


if __name__ == "__main__":
    sys.exit(main())
