# Packing upgrade of cand_1786683341_0: every structural term (per-head, universe,
# pair-SCS) is a certified count of occurrences of symbols WITHIN its own alphabet
# mask, so terms with pairwise-DISJOINT masks count disjoint position sets and ADD.
# Champion took only the single best term (+1 per uncovered referenced symbol);
# here: bound = |referenced| + max disjoint-mask sum of gains (gain = weight -
# |mask|), via 3-start greedy. Pointwise >= champion on every state (greedy's
# first pick is the max-gain item = champion's best), so nodes can only drop;
# pair-DP guard now compares against the higher packed bound => fewer DPs run.
def lb_cand(blocks, n):
    if not blocks:
        return 0
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
        base = bin(gref).count("1")  # every referenced symbol appears at least once
        best = base

        heads = {}   # head symbol -> [union of rests, [(|r|, r), ...]]
        by_u = {}    # exact universe mask -> bitmask of head symbols
        t1 = t2 = t3 = None  # top-3 blocks by rest size (stable order)
        for s, r in gl:
            kb = bin(r).count("1")
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

        items = []  # (gain, alphabet mask); weight counts only mask-symbol occurrences

        # per-head term: 1 (first s) + after it A(|r_i|) occurrences of r_i-symbols
        # + one occurrence of each symbol of U\r_i -- all inside {s}|U.
        for s, hd in heads.items():
            ur = hd[0]
            hmask = (1 << s) | ur
            inner = 0
            for kb, r in hd[1]:
                if kb < n:
                    a = AT[kb] if kb < 7 else 2 * kb - 1
                else:
                    a = kb
                v = a + bin(ur & ~r).count("1")
                if v > inner:
                    inner = v
            g = 1 + inner - bin(hmask).count("1")
            if g > 0:
                items.append((g, hmask))

        # universe terms: m first-occurrences of the m head symbols (all in u)
        # + A(k-1) occurrences of u-symbols after the latest one; if all k
        # symbols of u are heads: A(k) occurrences of u-symbols.
        for u, hm in by_u.items():
            k = bin(u).count("1")
            m = bin(hm).count("1")
            km = k - 1
            a1 = AT[km] if km < 7 else 2 * km - 1
            g = m + a1 - k
            if g > 0:
                items.append((g, u))
            if m == k and k < n:
                ak = AT[k] if k < 7 else 2 * k - 1
                g = ak - k
                if g > 0:
                    items.append((g, u))

        # disjoint-mask packing: bound = base + sum of gains over pairwise-
        # disjoint masks (uncovered referenced symbols already in base).
        li = len(items)
        if li == 1:
            best = base + items[0][0]
        elif li:
            items.sort(reverse=True)
            gsum = 0
            for st in (0, 1, 2)[: li if li < 3 else 3]:
                g0, tk = items[st]
                gs = g0
                for idx in range(li):
                    if idx != st:
                        g, m = items[idx]
                        if not (m & tk):
                            tk |= m
                            gs += g
                if gs > gsum:
                    gsum = gs
            best = base + gsum

        # pair-SCS over top-3 blocks (shared symbols opposed); the SCS value
        # counts only u12-symbol occurrences, so it is also packable with
        # disjoint head/universe items; skip DP when even len(x)+len(y)+extras
        # cannot beat the current (already packed) best.
        cands = [t for t in (t1, t2, t3) if t is not None]
        nc = len(cands)
        if nc >= 2:
            for i in range(nc - 1):
                k1, s1, r1 = cands[i]
                for j in range(i + 1, nc):
                    k2, s2, r2 = cands[j]
                    u12 = (1 << s1) | r1 | (1 << s2) | r2
                    p12 = bin(u12).count("1")
                    ex = base - p12
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
                    scs = len(x) + ly - prev[ly]
                    v = scs + ex
                    if v > best:
                        best = v
                    pg = scs - p12
                    if pg > 0 and items:
                        tk = u12
                        gs = pg
                        for g, m in items:
                            if not (m & tk):
                                tk |= m
                                gs += g
                        v = base + gs
                        if v > best:
                            best = v
        total += best
    return total
