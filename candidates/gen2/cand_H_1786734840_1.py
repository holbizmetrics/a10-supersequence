def lb_cand(blocks, n):
    if not blocks:
        return 0
    # fast popcount when available (Py>=3.10); safe fallback otherwise
    try:
        pc = int.bit_count
        pc(0)
    except Exception:
        def pc(z):
            return bin(z).count("1")
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
        best = pc(gref)  # every referenced symbol appears at least once

        heads = {}   # head symbol -> [union of rests, [(a(|r|), |r|, r), ...]]
        by_u = {}    # exact universe mask -> bitmask of head symbols
        t1 = t2 = t3 = None  # top-3 blocks by rest size (stable order)
        for s, r in gl:
            kb = pc(r)
            if kb < n:
                a = AT[kb] if kb < 7 else 2 * kb - 1
            else:
                a = kb  # all-perms invariant not trusted at |r| >= n: plain count
            h = heads.get(s)
            if h is None:
                heads[s] = [r, [(a, kb, r)]]
            else:
                h[0] |= r
                h[1].append((a, kb, r))
            u = (1 << s) | r
            hm = by_u.get(u)
            by_u[u] = (1 << s) if hm is None else (hm | (1 << s))
            if t1 is None or kb > t1[0]:
                t1, t2, t3 = (kb, s, r), t1, t2
            elif t2 is None or kb > t2[0]:
                t2, t3 = (kb, s, r), t2
            elif t3 is None or kb > t3[0]:
                t3 = (kb, s, r)

        # per-head term: after the first s all perms of each rest of head s must
        # embed: 1 + max_i(a(|r_i|) + |U\r_i|) + one per referenced symbol
        # outside {s}|U (all counted positions distinct).
        for s, hd in heads.items():
            ur = hd[0]
            extras = pc(gref & ~((1 << s) | ur))
            inner = 0
            for a, kb, r in hd[1]:
                v = a + pc(ur & ~r)
                if v > inner:
                    inner = v
            v = 1 + inner + extras
            if v > best:
                best = v

        # universe terms: m heads sharing exact universe u: the m distinct
        # first-occurrences all lie at/before the latest one p; after p all
        # perms of that head's rest (size k-1) must embed: m + a(k-1) + ex.
        # If all k symbols of u are heads, all perms of u are pending: a(k).
        for u, hm in by_u.items():
            k = pc(u)
            m = pc(hm)
            ex = pc(gref & ~u)
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

        # NEW sweep term — generalizes the universe term to heads with UNEQUAL
        # universes. For any subset S of heads (|S| = m >= 2): the m distinct
        # first-occurrences lie at/before the latest one p, owned by some
        # (adversarial) head j in S; every rest r of head j pends fully after
        # p, so >= a(|r|) occurrences of r-symbols land strictly after p; the m
        # head first-occurrences are at/before p (distinct positions, distinct
        # symbols); every referenced symbol outside (S-heads | r) occurs at
        # least once at a position with a symbol counted nowhere else. Hence
        # m + min_{j in S} max_{r of j} (a(|r|) + |gref \ (S|r)|) is admissible.
        # Heuristic subset choice: prefixes of heads sorted by strongest rest.
        nh = len(heads)
        if nh >= 2:
            hlist = []
            for s, hd in heads.items():
                wa = 0
                for a, kb, r in hd[1]:
                    if a > wa:
                        wa = a
                hlist.append((wa, s, hd[1]))
            hlist.sort(reverse=True)
            hm2 = 0
            pref = []
            m = 0
            for wa, s, rl in hlist:
                hm2 |= 1 << s
                pref.append(rl)
                m += 1
                if m < 2:
                    continue
                mn = -1
                for rl2 in pref:
                    wj = 0
                    for a, kb, r in rl2:
                        v = a + pc(gref & ~(hm2 | r))
                        if v > wj:
                            wj = v
                    if mn < 0 or wj < mn:
                        mn = wj
                v = m + mn
                if v > best:
                    best = v
                # mn only shrinks as the prefix grows and m <= nh: bail early
                if nh + mn <= best:
                    break

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
                    ex = pc(gref & ~u12)
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
