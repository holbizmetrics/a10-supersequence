# P2 — gen-2 champion cand_U_1786732349_0 (Researches/a10-supersequence, sha of source below)
# PLUS the two pilot-v5 terms (size-2 adder, mutual-head). Only the per-head block is changed;
# everything else is the champion verbatim. Translation by linux-claude-5534b575, 2026-09-02.
def lb_cand(blocks, n):
    if not blocks:
        return 0
    try:
        bc = int.bit_count  # py>=3.10 fast popcount
    except AttributeError:
        def bc(x):
            return bin(x).count("1")
    AT = (0, 1, 3, 7, 12, 19, 28)  # proven A062714 values a(0)..a(6)

    # --- symbol-connectivity groups (pairwise-disjoint referenced masks) ---
    groups = []
    for b in blocks:
        s, r = b
        bm = (1 << s) | r
        gl = [b]
        rest = []
        for m0, l0 in groups:
            if m0 & bm:
                bm |= m0
                gl.extend(l0)
            else:
                rest.append((m0, l0))
        rest.append((bm, gl))
        groups = rest

    total = 0
    for gref, gl in groups:
        best = bc(gref)  # every referenced symbol appears at least once

        heads = {}   # head symbol -> [union of rests, [(|r|, r), ...]]
        by_u = {}    # exact universe mask -> bitmask of head symbols
        t1 = t2 = t3 = None  # top-3 blocks by rest size (stable order)
        for s, r in gl:
            kb = bc(r)
            h = heads.get(s)
            if h is None:
                heads[s] = [r, [(kb, r)]]
            else:
                h[0] |= r
                h[1].append((kb, r))
            u = (1 << s) | r
            hm = by_u.get(u)
            by_u[u] = (1 << s) if hm is None else (hm | (1 << s))
            if t1 is None or kb > t1[0]:
                t1, t2, t3 = (kb, s, r), t1, t2
            elif t2 is None or kb > t2[0]:
                t2, t3 = (kb, s, r), t2
            elif t3 is None or kb > t3[0]:
                t3 = (kb, s, r)

        # per-head term: every embedding of s-suffixes uses an s at/after the
        # first s, so after the first s the completion must hold all perms of
        # each rest of head s: 1 + max_i(A(|r_i|) + |U\r_i|) + one per extra
        # referenced symbol outside {s}|U (all counted positions distinct).
        hl = []
        for s, hd in heads.items():
            ur = hd[0]
            alph = (1 << s) | ur
            extras = bc(gref & ~alph)
            inner = 0
            for kb, r in hd[1]:
                if kb < n:
                    a = AT[kb] if kb < 7 else 2 * kb - 1
                else:
                    a = kb
                v = a + bc(ur & ~r)
                if v > inner:
                    inner = v
            # --- pilot v5 (R14) terms, translated 2026-09-02 ---
            # (a) size-2 adder: a size-2 rest needs both orders (ab, ba) after the first s,
            #     so |ur| + 1; three distinct size-2 rests on a 3-set need 5 = |ur| + 2.
            k2 = 0
            seen2 = set()
            for kb, r in hd[1]:
                if kb == 2 and r not in seen2:
                    seen2.add(r)
                    k2 += 1
            p_ur = bc(ur)
            adder = 0 if k2 == 0 else (2 if (k2 >= 3 and p_ur == 3) else 1)
            if p_ur + adder > inner:
                inner = p_ur + adder
            # (b) mutual-head term: s not in ur and some block j in the group has head_j in ur
            #     and s in rest_j -> one further position (first s_j before p is an ur-symbol
            #     before p, uncounted; after p it forces a second s after p).
            mut = 0
            if not (ur >> s) & 1:
                for hj, rj in gl:
                    if (ur >> hj) & 1 and (rj >> s) & 1:
                        mut = 1
                        break
            v = 1 + inner + extras + mut
            if v > best:
                best = v
            hl.append((inner, s, alph))

        nh = len(hl)
        if nh > 1:
            hl.sort(reverse=True)

            # multi-head term (generalizes the exact-universe term to heads
            # with DIFFERENT universes): every head symbol occurs, so for any
            # set H of heads the |H| distinct first-occurrences all lie
            # at/before the latest one p, held by some head j in H; after p
            # all of head j's per-head requirements embed. Valid for every
            # completion: |H| + min_{j in H}(inner_j + |gref \ (H|alph_j)|).
            # Try H = top-t heads by inner for each t.
            hmask = 0
            for t in range(nh):
                hmask |= 1 << hl[t][1]
                if t == 0:
                    continue
                mn = -1
                for j in range(t + 1):
                    ij = hl[j][0] + bc(gref & ~(hmask | hl[j][2]))
                    if mn < 0 or ij < mn:
                        mn = ij
                v = t + 1 + mn
                if v > best:
                    best = v

            # disjoint-alphabet packing: a head's 1+inner positions all carry
            # symbols from its own alphabet, so heads with pairwise-disjoint
            # alphabets contribute on disjoint positions and ADD, plus one
            # per uncovered referenced symbol (greedy by inner desc).
            cov = 0
            acc = 0
            for inner, s, alph in hl:
                if not (alph & cov):
                    cov |= alph
                    acc += 1 + inner
            v = acc + bc(gref & ~cov)
            if v > best:
                best = v

        # universe terms: m heads sharing exact universe u. The m distinct
        # first-occurrences all lie at/before the latest one p; after p all
        # perms of that head's rest (size >= k-1) must embed: m + A(k-1).
        # If all k symbols of u are heads, all perms of u are pending: A(k).
        for u, hm in by_u.items():
            k = bc(u)
            m = bc(hm)
            ex = bc(gref & ~u)
            km = k - 1
            a1 = AT[km] if km < 7 else 2 * km - 1
            v = m + a1 + ex
            if v > best:
                best = v
            if m == k and k < n:
                ak = AT[k] if k < 7 else 2 * k - 1
                v = ak + ex
                if v > best:
                    best = v

        # pair-SCS over top-3 blocks (shared symbols opposed), plus one per
        # referenced symbol outside the pair's alphabet; skip DP when even
        # len(x)+len(y)+extras cannot beat current best.
        cands = [t for t in (t1, t2, t3) if t is not None]
        nc = len(cands)
        if nc >= 2:
            for i in range(nc - 1):
                k1, s1, r1 = cands[i]
                for j in range(i + 1, nc):
                    k2, s2, r2 = cands[j]
                    u12 = (1 << s1) | r1 | (1 << s2) | r2
                    ex = bc(gref & ~u12)
                    if 2 + k1 + k2 + ex <= best:
                        continue
                    shared = r1 & r2
                    sh = [t for t in range(n) if shared >> t & 1]
                    x = [s1] + sh + [t for t in range(n) if (r1 & ~shared) >> t & 1]
                    sh.reverse()
                    y = [s2] + sh + [t for t in range(n) if (r2 & ~shared) >> t & 1]
                    ly = len(y)
                    prev = [0] * (ly + 1)
                    for a_ in x:
                        cur = [0] * (ly + 1)
                        c = 0
                        for jj in range(1, ly + 1):
                            if a_ == y[jj - 1]:
                                c = prev[jj - 1] + 1
                            else:
                                pj = prev[jj]
                                if pj > c:
                                    c = pj
                            cur[jj] = c
                        prev = cur
                    v = len(x) + ly - prev[ly] + ex
                    if v > best:
                        best = v
        total += best
    return total
