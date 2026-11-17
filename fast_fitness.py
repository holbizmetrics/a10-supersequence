"""fast_fitness.py — numba port of the warmth-gauge fitness (operator-confirmed 2026-07-12).

Two jitted kernels replacing the pure-Python hot path of prefix_anneal.fitness:
  1. remainder_blocks_jit: iterative DFS over greedy (mask, ptr) states with a visited table;
     block dedup via an (n, 2^n) seen-matrix. Replaces the ~50ms Python walk.
  2. greedy_deficit_jit: the greedy tail-builder over tuples packed as a fixed-width int array.
Tuple expansion (blocks -> distinct tuples) stays in Python (cheap, itertools).

CONTRACT: outputs must agree EXACTLY with resynth.remainder_blocks and
prefix_anneal.greedy_deficit — enforced by instrument_check() below, which is run and logged
before any fast-fitness verdict is banked (same discipline as desktop_arm's coverage_jit)."""
from __future__ import annotations

import itertools
import sys

import numpy as np
from numba import njit

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass


@njit(cache=True)
def remainder_blocks_jit(prefix: np.ndarray, n: int):
    """Return (K, sym[K], rest[K]) — the distinct greedy-remainder blocks of `prefix`."""
    length = prefix.shape[0]
    full = (1 << n) - 1
    nextpos = np.full((length + 1, n), length, dtype=np.int64)
    for p in range(length - 1, -1, -1):
        for s in range(n):
            nextpos[p, s] = nextpos[p + 1, s]
        nextpos[p, prefix[p]] = p

    visited = np.zeros((full + 1, length + 2), dtype=np.bool_)
    seen_block = np.zeros((n, full + 1), dtype=np.bool_)
    out_sym = np.empty(n * (full + 1), dtype=np.int64)
    out_rest = np.empty(n * (full + 1), dtype=np.int64)
    n_blocks = 0

    # explicit DFS stack of (mask, ptr) packed as mask*(length+2)+ptr
    stack = np.empty((full + 1) * (length + 2), dtype=np.int64)
    top = 0
    stack[top] = full * (length + 2) + 0
    top += 1
    visited[full, 0] = True
    while top > 0:
        top -= 1
        code = stack[top]
        mask = code // (length + 2)
        ptr = code % (length + 2)
        m = mask
        while m:
            bit = m & (-m)
            s = 0
            b = bit
            while b > 1:
                b >>= 1
                s += 1
            m ^= bit
            occ = nextpos[ptr, s]
            if occ >= length:
                rest = mask ^ bit
                if not seen_block[s, rest]:
                    seen_block[s, rest] = True
                    out_sym[n_blocks] = s
                    out_rest[n_blocks] = rest
                    n_blocks += 1
            else:
                nmask = mask ^ bit
                nptr = occ + 1
                if not visited[nmask, nptr]:
                    visited[nmask, nptr] = True
                    stack[top] = nmask * (length + 2) + nptr
                    top += 1
    return n_blocks, out_sym[:n_blocks], out_rest[:n_blocks]


@njit(cache=True)
def greedy_deficit_jit(tup: np.ndarray, tlen: np.ndarray, n: int, m: int):
    """Greedy tail-builder. tup: (T, W) symbol array; tlen: lengths. Returns (deficit, tail, tail_len).
    Mirrors prefix_anneal.greedy_deficit exactly: score[s] = sum over pending tuples heading s of
    (1 + 0.5 * remaining_length); pick argmax (ties -> smallest s, matching Python max());
    stop when no pending or no positive score."""
    T = tup.shape[0]
    ptr = np.zeros(T, dtype=np.int64)
    done = np.zeros(T, dtype=np.bool_)
    pending = T
    tail = np.empty(m, dtype=np.int64)
    tail_len = 0
    for _ in range(m):
        if pending == 0:
            break
        score = np.zeros(n, dtype=np.float64)
        for t in range(T):
            if not done[t]:
                need = tup[t, ptr[t]]
                score[need] += 1.0 + 0.5 * (tlen[t] - ptr[t])
        best_s = 0
        best_v = score[0]
        for s in range(1, n):
            if score[s] > best_v:
                best_v = score[s]
                best_s = s
        if best_v == 0.0:
            break
        tail[tail_len] = best_s
        tail_len += 1
        for t in range(T):
            if not done[t] and tup[t, ptr[t]] == best_s:
                ptr[t] += 1
                if ptr[t] == tlen[t]:
                    done[t] = True
                    pending -= 1
    return pending, tail, tail_len


EXPAND_MAX = 4
TUPLE_CAP = 300_000


def blocks_to_tuple_arrays(n_blocks, sym, rest, n):
    """Expand blocks to distinct tuples, packed as (T, W) array + lengths. None on bail."""
    tuples = set()
    for i in range(n_blocks):
        s = int(sym[i])
        rest_syms = [t for t in range(n) if rest[i] & (1 << t)]
        if len(rest_syms) > EXPAND_MAX:
            return None, None
        for sigma in itertools.permutations(rest_syms):
            tuples.add((s,) + sigma)
            if len(tuples) > TUPLE_CAP:
                return None, None
    if not tuples:
        return np.zeros((0, 1), dtype=np.int64), np.zeros(0, dtype=np.int64)
    W = max(len(t) for t in tuples)
    T = len(tuples)
    arr = np.zeros((T, W), dtype=np.int64)
    lens = np.zeros(T, dtype=np.int64)
    for k, t in enumerate(sorted(tuples)):
        lens[k] = len(t)
        for j, x in enumerate(t):
            arr[k, j] = x
    return arr, lens


def fitness_fast(prefix, n, m):
    """Drop-in for prefix_anneal.fitness, LAZY tuples: returns (deficit, tail_list, arrs) where
    arrs = (tup, lens) numpy pair (convert via tuples_set_from_arrays ONLY when the exact
    confirmer needs a set — building the Python set per-eval was 4x the whole jit pipeline)."""
    arr_prefix = np.asarray(prefix, dtype=np.int64)
    n_blocks, sym, rest = remainder_blocks_jit(arr_prefix, n)
    tup, lens = blocks_to_tuple_arrays(n_blocks, sym, rest, n)
    if tup is None:
        return 10**9, None, None
    if tup.shape[0] == 0:
        return 0, [], (tup, lens)
    deficit, tail, tail_len = greedy_deficit_jit(tup, lens, n, m)
    return int(deficit), [int(tail[i]) for i in range(int(tail_len))], (tup, lens)


def tuples_set_from_arrays(arrs):
    tup, lens = arrs
    return {tuple(int(tup[k, j]) for j in range(int(lens[k]))) for k in range(tup.shape[0])}


def instrument_check(rng):
    """Fast fitness must agree EXACTLY with the Python path on blocks AND deficit."""
    from resynth import remainder_blocks as rb_python
    from prefix_anneal import greedy_deficit as gd_python
    from a15_n10_graded import random_graded_word
    import random

    checks = 0
    # small-n randoms + n=10 structured, multiple cuts
    for trial in range(30):
        n = (3, 4, 5)[trial % 3]
        L = rng.randrange(2 * n, 4 * n)
        w = [rng.randrange(n) for _ in range(L)]
        cut = rng.randrange(1, L)
        py_blocks = rb_python(w + [0], n, cut)
        k, sym, rest = remainder_blocks_jit(np.asarray(w[:cut], dtype=np.int64), n)
        jit_blocks = {(int(sym[i]), int(rest[i])) for i in range(k)}
        assert jit_blocks == py_blocks, (n, w, cut)
        checks += 1
    from resynth import expand_blocks as eb_python
    import json
    # n=10: structured prefixes (harvest) — expandable; random graded — may bail: assert PARITY
    harvest = json.load(open("prefix_harvest_c66_g1.json"))
    n10_cases = [(h["prefix"], 66) for h in harvest]
    for k in range(3):
        w = random_graded_word([10, 10, 9, 9, 8, 8, 8, 7, 7, 6], random.Random(900 + k))
        n10_cases.append((w[:66], 66))
        n10_cases.append((w[:62], 62))
    for prefix, cut in n10_cases:
        m = 82 - cut
        py_blocks = rb_python(list(prefix) + [0], 10, cut)
        kk, sym, rest = remainder_blocks_jit(np.asarray(prefix[:cut], dtype=np.int64), 10)
        assert {(int(sym[i]), int(rest[i])) for i in range(kk)} == py_blocks
        py_tuples = eb_python(py_blocks, 10)
        tup, lens = blocks_to_tuple_arrays(kk, sym, rest, 10)
        if py_tuples is None or tup is None:
            assert (py_tuples is None) == (tup is None), "bail parity broken"
            checks += 1
            continue
        d_py, _ = gd_python(py_tuples, 10, m)
        d_jit, _, _ = greedy_deficit_jit(tup, lens, 10, m)
        assert d_py == int(d_jit), (cut, d_py, int(d_jit))
        checks += 1
    print(f"[fast-fitness instrument] jit == python on {checks}/{checks} cross-checks — PASSES")


if __name__ == "__main__":
    import random
    instrument_check(random.Random(7))
