# P3 — pilot v5 cand-071 (arm C author a5, candidate 7; the one module that DOMINATED lb3 on the
# n=4 table: above on 945 states, below on 0) translated to the lane's candidate contract and
# generalized to any n. Translation by the orchestrator (linux-claude-5534b575, 2026-09-02);
# admissibility at n=3/4/5 decided by the lane's oracle, never trusted from the n=4 proof.
#
#   needed(x): x heads a block or lies in a rest.
#   cond(S):   every t in S heads a block whose rest contains S \ {t}  (then every ordering of S is
#              forced, so the S-restriction of any completion has length >= A(|S|)).
#   LB5 (head stacking with deletion): max over nonempty sets J of heads of
#              |J| + min_{t in J} max_{blocks (t,R)} ( A(|R|) + #{needed x : x not in J, x not in R} )
#   LB6 (partition-additive): max over set partitions of the referenced symbols of
#              sum_G L(G),  L(G) = max( #needed in G, max_{S in G, cond(S)} A(|S|),
#                                       max_{blocks (t,R), t in G} 1 + A(|R intersect G|) )
#   bound = max(LB5, LB6).
# Cost note: subsets and set partitions are enumerated over the REFERENCED symbols only (the
# unreferenced ones contribute nothing), which keeps n=6 states tractable; Stage B decides.

def lb_cand(blocks, n):
    if not blocks:
        return 0
    A = (0, 1, 3, 7, 12, 19, 28)

    def pop(m):
        return bin(m).count("1")

    ref = 0
    for s, r in blocks:
        ref |= (1 << s) | r
    syms = [t for t in range(n) if (ref >> t) & 1]
    heads = {}
    for s, r in blocks:
        heads.setdefault(s, []).append(r)
    head_set = set(heads)

    # cond(S) for every nonempty subset mask S of ref
    def cond(S):
        for t in syms:
            if not (S >> t) & 1:
                continue
            need = S & ~(1 << t)
            ok = False
            for r in heads.get(t, ()):
                if r & need == need:
                    ok = True
                    break
            if not ok:
                return False
        return True

    # enumerate subset masks of ref (nonempty)
    submasks = []
    sub = ref
    while sub:
        submasks.append(sub)
        sub = (sub - 1) & ref
    conds = {S: cond(S) for S in submasks}

    # LB5
    lb5 = 0
    for J in submasks:
        if J & ~sum(1 << h for h in head_set):
            continue  # J must consist of heads only
        mn = None
        for t in syms:
            if not (J >> t) & 1:
                continue
            gt = 0
            for r in heads[t]:
                outside = pop(ref & ~J & ~r)
                v = A[pop(r)] + outside
                if v > gt:
                    gt = v
            if mn is None or gt < mn:
                mn = gt
        val = pop(J) + (mn or 0)
        if val > lb5:
            lb5 = val

    # LB6: L(G) per subset mask G, then max over set partitions of syms
    L = {}
    for G in submasks:
        val = pop(ref & G)
        for S in submasks:
            if S & ~G == 0 and conds[S]:
                a = A[pop(S)]
                if a > val:
                    val = a
        for s, r in blocks:
            if (G >> s) & 1:
                v = 1 + A[pop(r & G)]
                if v > val:
                    val = v
        L[G] = val

    def partitions(items):
        if not items:
            yield []
            return
        first = items[0]
        for part in partitions(items[1:]):
            for i in range(len(part)):
                yield part[:i] + [part[i] | first] + part[i + 1:]
            yield [first] + part

    lb6 = 0
    for part in partitions([1 << t for t in syms]):
        total = 0
        for G in part:
            total += L[G]
        if total > lb6:
            lb6 = total
    return lb5 if lb5 > lb6 else lb6
