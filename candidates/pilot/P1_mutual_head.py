# P1 — pilot v5 cand-151 (arm C author a3, candidate 9) translated to the evolution lane's
# candidate contract and GENERALIZED from n=4 to any n. Translation by the orchestrator
# (linux-claude-5534b575, 2026-09-02); admissibility at n=3/4/5 is decided by the lane's
# oracle (Stage A), never trusted from the n=4 Z3 proof.
#
# Terms kept (n-independent arguments): per head s, after its first occurrence the completion
# must hold every ordering of every rest with head s, so
#   g_s = max( max over rests r of A(|r|),                      # one rest forces A(|r|)
#              |M_s| + adder )                                  # M_s = union of rests of s;
#          adder = 0 if no size-2 rest; 2 if >= 3 distinct size-2 rests and |M_s| == 3
#          (three pairs on a 3-set need 5 = 3 + 2); else 1 (a size-2 rest needs ab AND ba)
#   outside_s = |U \ (M_s u {s})|   every other required symbol takes a further position
#   mut_s = 1 if s not in M_s and some block j has head_j in M_s and s in rest_j
#           (the MUTUAL-HEAD term: the first s_j either precedes the first s -- a position in M_s
#            before p, uncounted -- or follows it, forcing a second s after p)
#   per_s = 1 + g_s + outside_s + mut_s
# Term DROPPED: the n=4-specific full-block count table (0, 8, 10, 11, 12), which used a(4) = 12.
# bound = max over heads of per_s.

def lb_cand(blocks, n):
    if not blocks:
        return 0
    A = (0, 1, 3, 7, 12, 19, 28)  # A062714 a(0)..a(6), proven values

    def pop(m):
        return bin(m).count("1")

    U = 0
    for s, r in blocks:
        U |= (1 << s) | r
    heads = {}
    for s, r in blocks:
        heads.setdefault(s, []).append(r)
    best = 0
    for s, rests in heads.items():
        M = 0
        amax = 0
        k2 = 0
        seen2 = set()
        for r in rests:
            M |= r
            k = pop(r)
            if k < len(A) and A[k] > amax:
                amax = A[k]
            if k == 2 and r not in seen2:
                seen2.add(r)
                k2 += 1
        p = pop(M)
        if k2 == 0:
            adder = 0
        elif k2 >= 3 and p == 3:
            adder = 2
        else:
            adder = 1
        g = amax if amax > p + adder else p + adder
        covered = M | (1 << s)
        outside = pop(U & ~covered)
        mut = 0
        if not (M >> s) & 1:
            for hj, rj in blocks:
                if (M >> hj) & 1 and (rj >> s) & 1:
                    mut = 1
                    break
        val = 1 + g + outside + mut
        if val > best:
            best = val
    return best
