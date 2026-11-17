"""supersequence_family.py — map the shortest-supersequence family across alphabet size n,
to find the WINNABLE slice (operator-requested 2026-07-10).

Problem: sigma(n) = minimal length of a word over n symbols containing all n! permutations as
(non-contiguous) subsequences.

Literature anchors (verify what we can here):
  - Exactly known for 1<=n<=7 (Newey): 1,3,7,12,19,28,39  == n^2-2n+4 for n>=3. OPTIMUM PROVEN -> dead.
  - Newey's conjecture sigma(n)=n^2-2n+4 is DISPROVEN: ceil(n^2 - 7/3 n + 19/3) is a valid upper
    bound and is STRICTLY SMALLER than n^2-2n+4 for n>=10 (first crack at n=10: 83<84).
  - Asymptotic best upper bound ~ n^2 - (5/2)n + O(...).
So: n<=7 solved(dead) · n=8,9 open-but-conjecture-likely-optimal · n>=10 open + naive-beatable(live).

This module carries a GENERAL-n exact oracle so we can verify completeness / search at any n,
and prints the family map with an oracle-cost proxy (why small n is tractable).
"""
from __future__ import annotations

import sys
from functools import lru_cache
from math import ceil, factorial
from typing import Sequence

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def exact_permutation_coverage(word: Sequence[int], n: int) -> int:
    """General-n exact count of permutations of 0..n-1 occurring as subsequences of `word`.
    Same DP as the n=13 oracle, parameterized by n. State = (position, remaining_mask)."""
    word = tuple(word)
    assert all(0 <= s < n for s in word), "symbol out of range 0..n-1 (negative ints corrupt the table silently)"
    length = len(word)
    full_mask = (1 << n) - 1
    next_position = [[length] * n for _ in range(length + 1)]
    current = [length] * n
    for position in range(length - 1, -1, -1):
        current = current.copy()
        current[word[position]] = position
        next_position[position] = current

    @lru_cache(maxsize=None)
    def count(position: int, remaining_mask: int) -> int:
        if remaining_mask == 0:
            return 1
        total = 0
        mask = remaining_mask
        while mask:
            bit = mask & -mask
            symbol = bit.bit_length() - 1
            occurrence = next_position[position][symbol]
            if occurrence < length:
                total += count(occurrence + 1, remaining_mask ^ bit)
            mask ^= bit
        return total

    result = count(0, full_mask)
    count.cache_clear()
    return result


def is_complete(word: Sequence[int], n: int) -> bool:
    return exact_permutation_coverage(word, n) == factorial(n)


def newey_length(n: int) -> int:
    """The n^2-2n+4 construction length (= exact optimum for 3<=n<=7; upper bound otherwise)."""
    return n * n - 2 * n + 4 if n >= 3 else (1 if n == 1 else 3)


def improved_upper_bound(n: int) -> int:
    """ceil(n^2 - 7/3 n + 19/3): a proven upper bound strictly below Newey for n>=10."""
    return ceil(n * n - (7 * n) / 3 + 19 / 3)


EXACT_KNOWN = {1: 1, 2: 3, 3: 7, 4: 12, 5: 19, 6: 28, 7: 39}  # Newey, optimum proven


def status(n: int) -> str:
    if n in EXACT_KNOWN:
        return "SOLVED (optimum proven) -> DEAD target"
    if n in (8, 9):
        return "OPEN, but conjecture value likely optimal (crack starts n=10) -> near-dead"
    # n >= 10
    return "OPEN + naive DISPROVEN (shorter known to exist) -> LIVE / winnable"


def dp_state_cost(n: int, length: int) -> int:
    """Rough per-evaluation cost proxy = (length+1) * 2^n reachable DP states."""
    return (length + 1) * (1 << n)


def print_map(max_n: int = 14) -> None:
    print(f"{'n':>3} {'n!':>13} {'newey(n^2-2n+4)':>16} {'improved UB':>12} "
          f"{'exact':>7} {'DP-cost~':>12}  status")
    for n in range(1, max_n + 1):
        newey = newey_length(n)
        improved = improved_upper_bound(n)
        exact = str(EXACT_KNOWN.get(n, "open"))
        cost = dp_state_cost(n, newey)
        beatable = "  <== naive beatable" if (n >= 10 and improved < newey) else ""
        print(f"{n:>3} {factorial(n):>13,} {newey:>16} {improved:>12} {exact:>7} {cost:>12,}  "
              f"{status(n)}{beatable}")


if __name__ == "__main__":
    print_map()
    # quick self-check of the general oracle on a known tiny case
    print()
    trivial_n3 = [0, 1, 2, 0, 1, 2, 0]  # length 7 = sigma(3); should be complete
    print("oracle self-check: n=3 length-7 word complete?",
          is_complete(trivial_n3, 3), f"(coverage {exact_permutation_coverage(trivial_n3,3)}/6)")
