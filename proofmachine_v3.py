"""proofmachine_v3.py — evolved-bounds era, generation 0: the PROVEN candidates.

Discipline (the evolve->prove->deploy contract): a bound may enter a PROOF RUN only with a
written admissibility proof. The FunSearch loop (bounds_lab, next) may DISCOVER candidates
empirically; empirical bounds never deploy. Generation 0 = three bounds with one-line proofs,
cashed before any evolution:

  (B1) BLOCK-RECURSIVE: block (s,R) present => LB >= 1 + A[|R|] + outside(s,R).
       PROOF: every ordering of R embeds after SOME s, hence after the FIRST s (position p);
       so w[p+1:] contains every ordering of R => |w| >= (p+1) + a(|R|) >= 1 + a(|R|).
       Symbols outside {s}|R occupy positions disjoint from the {s}|R-restriction: additive.
       A[] uses literature-PROVEN values only (Newey k<=7) AND k < n strictly (no circularity:
       at rung n we only cite a(k) for k <= n-1, all proven).
  (B2) DISJOINT-GROUP ADDITIVITY: partition blocks into symbol-disjoint groups (greedy union);
       LB >= sum of per-group LBs. PROOF: groups touch disjoint symbol sets, so the positions
       serving one group are disjoint from those serving another.
       Per-group LB = max(B1-term, longest, |referenced|).
  (B3) PAIR/TRIPLE-SCS within a group (carried from v2, proof unchanged).

Machinery (advance/dominance/canon/memo/persistence) imported UNCHANGED from proofmachine_v2 —
that code has a banked proof (n=6) and a 4-argument soundness case behind it; v3 only replaces
the bound. Validation contract: ladder n=3/4/5 verdicts must match; then n=6 RE-RUN with fresh
memo (v3-suffixed) — ground truth known AND v2's 96.25M-node baseline gives the exact
strength measurement that decides n=7 feasibility."""
from __future__ import annotations

import argparse
import sys
import time

import proofmachine_v2 as v2
from proofmachine_v2 import (root_state, advance, heads, referenced_mask, _scs_pair,
                             canon, A_PROVEN, MEMO_CAP, MASK_BYTES, prune_dominated)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass


def _disable_power_throttling():
    """Windows EcoQoS opt-out (R4/R5 lesson: background python ran 47x slow on the Komax laptop).
    Process-scoped, user-mode, no admin; ControlMask=EXECUTION_SPEED with StateMask=0 explicitly
    DISABLES throttling for this process. Silent no-op off-Windows or on failure. Doubles as the
    mechanism test: if a background run at full rate follows this call, EcoQoS WAS the throttle."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        class _PPTS(ctypes.Structure):
            _fields_ = [("Version", ctypes.c_ulong),
                        ("ControlMask", ctypes.c_ulong),
                        ("StateMask", ctypes.c_ulong)]

        st = _PPTS(1, 0x1, 0)  # version 1, EXECUTION_SPEED, state 0 = throttling OFF
        ok = ctypes.windll.kernel32.SetProcessInformation(
            ctypes.windll.kernel32.GetCurrentProcess(), 4,  # ProcessPowerThrottling
            ctypes.byref(st), ctypes.sizeof(st))
        return bool(ok)
    except Exception:
        return False


def code_fingerprint_v3():
    """v2.3 audit fix ported (2026-07-20, pre-reg): memo entries are CONCLUSIONS derived under a
    specific (advance, prune_dominated, lb3, _group_lb, canon, _scs_pair, A_PROVEN, MASK_BYTES).
    v3's original runner loaded an unauthenticated pickle — the exact BUG-1 false-theorem vector
    the audit reproduced in v2. Memos are signed and REFUSED (hard exit 2) on any mismatch."""
    import hashlib, inspect
    src = "".join(inspect.getsource(fn)
                  for fn in (advance, prune_dominated, lb3, _group_lb, canon, _scs_pair))
    src += repr(sorted(A_PROVEN.items())) + f"|MASK_BYTES={MASK_BYTES}"
    return hashlib.sha256(src.encode()).hexdigest()


def _group_lb(blocks, n):
    """LB for a symbol-disjoint group of blocks: max of B1 per block, longest, referenced."""
    best = 0
    ref = 0
    for s, r in blocks:
        ref |= (1 << s) | r
        k = bin(r).count("1")
        term = 1 + A_PROVEN.get(k, 0) if k < n and k in A_PROVEN else 1 + k
        if term > best:
            best = term
        if 1 + k > best:
            best = 1 + k
    n_ref = bin(ref).count("1")
    if n_ref > best:
        best = n_ref
    # pair-SCS inside the group (top 2 by rest size)
    big = sorted(blocks, key=lambda b: -bin(b[1]).count("1"))[:2]
    if len(big) == 2:
        (s1, r1), (s2, r2) = big
        shared = r1 & r2
        sh = [t for t in range(n) if shared & (1 << t)]
        o1 = [t for t in range(n) if (r1 & ~shared) & (1 << t)]
        o2 = [t for t in range(n) if (r2 & ~shared) & (1 << t)]
        v = _scs_pair((s1,) + tuple(sh) + tuple(o1), (s2,) + tuple(reversed(sh)) + tuple(o2))
        if v > best:
            best = v
    return best


def lb3(blocks, n):
    """v3 bound: universe term (from v2) OR disjoint-group additive sum of B1/B2/B3 terms."""
    if not blocks:
        return 0
    # group blocks by symbol-connectivity (greedy union-find over referenced masks)
    groups = []  # list of [mask, [blocks]]
    for b in blocks:
        s, r = b
        bm = (1 << s) | r
        merged = [bm, [b]]
        rest = []
        for gm, gl in groups:
            if gm & bm:
                merged[0] |= gm
                merged[1].extend(gl)
            else:
                rest.append([gm, gl])
        groups = rest + [merged]
    total = sum(_group_lb(gl, n) for _, gl in groups)
    best = total
    # v2's universe term still applies globally (complete-over-u recursion)
    by_universe = {}
    ref = referenced_mask(blocks)
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


def prove_no(n, length, log_every=2_000_000, persist_every=5_000_000, node_budget=None,
             wall_budget=None):
    # wall_budget (seconds) is enforced IN-PROCESS and uses time.time(), not perf_counter:
    # 2026-07-21 finding — MSYS `timeout` does not kill native Windows python (a 60-min-capped
    # run lived 14.5h), and QPC-based clocks may not count suspend. Epoch wall is the honest axis.
    import pickle, os
    memo_path = f"memo_v3_n{n}_L{length}.pkl"
    fingerprint = code_fingerprint_v3()
    seen = {}
    if os.path.exists(memo_path):
        with open(memo_path, "rb") as fh:
            payload = pickle.load(fh)
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
    w0 = time.time()
    sys.setrecursionlimit(1_000_000)

    class BudgetExceeded(Exception):
        pass

    def snapshot():
        payload = {"__fingerprint__": fingerprint, "n": n, "length": length, "entries": seen}
        with open(memo_path + ".tmp", "wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
            fh.flush(); os.fsync(fh.fileno())
        os.replace(memo_path + ".tmp", memo_path)
        print(f"  [snapshot] memo {len(seen):,} -> {memo_path}")

    def dfs(blocks, depth_left):
        nodes[0] += 1
        if node_budget is not None and nodes[0] > node_budget:
            raise BudgetExceeded()
        if wall_budget is not None and nodes[0] % 4096 == 0 and time.time() - w0 > wall_budget:
            raise BudgetExceeded()
        if nodes[0] % log_every == 0:
            print(f"  ... {nodes[0]:,} nodes, memo {len(seen):,}, {time.perf_counter()-t0:.0f}s")
        if nodes[0] % persist_every == 0:
            snapshot()
        if not blocks:
            return False
        if lb3(blocks, n) > depth_left:
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

    try:
        verdict = dfs(root_state(n), length)
    except BudgetExceeded:
        dt = time.perf_counter() - t0
        snapshot()
        print(f"[v3] n={n} L={length}: BUDGET-EXCEEDED at {nodes[0]:,} nodes ({dt:.1f}s) — "
              f"pre-registered falsifier fires; NO verdict banked.")
        return None
    dt = time.perf_counter() - t0
    snapshot()
    print(f"[v3] n={n} L={length}: {'PROVED-NO' if verdict else 'WORD EXISTS (no-proof fails)'}"
          f"  ({nodes[0]:,} nodes, memo {len(seen):,}, {dt:.1f}s)")
    return verdict


LADDER = {3: 7, 4: 12, 5: 19, 6: 28, 7: 39}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rungs", type=int, nargs="+", default=[3, 4, 5],
                        help="ladder rungs; each runs BOTH directions (v2.3b port)")
    parser.add_argument("--no", type=int, nargs=2, metavar=("N", "L"), default=None,
                        help="single prove_no(N, L) target run (skips the ladder)")
    parser.add_argument("--node-budget", type=int, default=None,
                        help="abort the --no run past this many nodes (pre-registered falsifier)")
    parser.add_argument("--wall-budget", type=float, default=None,
                        help="abort the --no run past this many SECONDS, enforced in-process "
                             "(external `timeout` does not kill native Windows python)")
    parser.add_argument("--log-every", type=int, default=2_000_000,
                        help="progress-line cadence in nodes (small values give early rate signal)")
    parser.add_argument("--no-throttle", action="store_true",
                        help="opt this process out of Windows EcoQoS power throttling (R4 fix)")
    args = parser.parse_args()
    if args.no_throttle:
        print(f"[qos] power-throttling opt-out: {'OK' if _disable_power_throttling() else 'FAILED/na'}")
    if args.no is not None:
        n, L = args.no
        verdict = prove_no(n, L, node_budget=args.node_budget, wall_budget=args.wall_budget,
                           log_every=args.log_every)
        sys.exit(3 if verdict is None else 0)
    all_ok = True
    for n in args.rungs:
        a_n = LADDER[n]
        print(f"=== rung n={n}: BOTH directions (ground truth a({n})={a_n}) ===")
        ok_no = prove_no(n, a_n - 1)
        if not ok_no:
            print("  *** RUNG FAILED (no-direction): prove_no(n, a(n)-1) must be True ***")
            all_ok = False
        ok_yes = prove_no(n, a_n)
        if ok_yes:
            print("  *** RUNG FAILED (YES-direction): prove_no(n, a(n)) returned True — OVER-PRUNING ***")
            all_ok = False
    print("LADDER:", "ALL RUNGS GREEN (both directions)" if all_ok else "FAILURE — do not proceed")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
