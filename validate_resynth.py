"""validate_resynth.py — the COMMITTED validation gate for resynth.py (audit remediation
2026-07-12: the original YES 5/5 + NO 3/3 ran in-session with no repo artifact, and the at-scale
witness gate was declared necessary but never satisfied before 60 at-scale NOs were banked).

Three arms:
  A. YES-path, small n: known-complete n=3/n=4 optima resynthesize to complete words (5 cuts).
  B. NO-path, small n: demand impossibly-short suffixes against PROVEN sigma(3)/sigma(4)
     optimality — must all be PROVABLY-NO.
  C. YES-path AT SCALE (n=10): cut the oracle-certified 83 and demand its OWN tail length back.
     A witness (the original tail) exists by construction, so search_suffix MUST return a suffix.
     This closes the audit's core hole: before this, every at-scale output was a NO, so a bug
     silently suppressing YES was indistinguishable from the reported results.

Exit 0 = all arms green. Run log is committed beside this script."""
import json
import sys
import time
from math import factorial

from resynth import resynthesize
from supersequence_family import is_complete, exact_permutation_coverage

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

failures = 0

print("=== ARM A: YES-path, small n ===")
w3 = [0, 1, 2, 0, 1, 2, 0]            # sigma(3)=7 optimum
w4 = [0, 1, 2, 3, 0, 1, 2, 0, 3, 1, 0, 2]  # sigma(4)=12 optimum (FINDING doc)
for (w, n, cuts) in ((w3, 3, (4, 5)), (w4, 4, (7, 8, 9))):
    assert is_complete(w, n)
    for c in cuts:
        cand = resynthesize(w, n, c, label=f"A/n{n}")
        ok = cand is not None and is_complete(cand, n)
        print(f"  A n={n} c={c}: complete resynthesis = {ok}")
        failures += 0 if ok else 1

print("=== ARM B: NO-path, small n (negative controls vs proven optimality) ===")
for (w, n, c) in ((w3, 3, 4), (w4, 4, 7), (w4, 4, 8)):
    m_short = len(w) - c - 1
    got = resynthesize(w, n, c, m=m_short, label=f"B/n{n}")
    bad = got is not None and is_complete(got, n)
    print(f"  B n={n} c={c} m={m_short}: NO as required = {not bad}")
    failures += 1 if bad else 0

print("=== ARM C: YES-path AT SCALE (n=10, witness = the 83's own tail) ===")
w83 = json.load(open("the83.json"))["word"]
assert len(w83) == 83 and exact_permutation_coverage(w83, 10) == factorial(10)
for c in (71, 69, 67):
    m = 83 - c   # the original tail length — a witness EXISTS
    t0 = time.perf_counter()
    cand = resynthesize(w83, 10, c, m=m, label=f"C/c{c}")
    dt = time.perf_counter() - t0
    ok = cand is not None and exact_permutation_coverage(cand, 10) == factorial(10)
    print(f"  C c={c} m={m}: suffix found + complete = {ok}  ({dt:.1f}s)")
    failures += 0 if ok else 1

print(f"\nVALIDATION: {'PASS' if failures == 0 else f'FAIL ({failures})'}")
sys.exit(0 if failures == 0 else 1)
