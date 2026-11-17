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
        best = bin(gref).count("1")  # every referenced symbol appears at least once

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

        # per-head inner cost = symbols forced strictly after the first s.
        # Rests of one head split into overlap-connected components with
        # pairwise-disjoint alphabets; component costs occupy disjoint symbol
        # sets after the first s, so they ADD (champion took only the max).
        hinfo = []
        innerof = {}
        for s, hd in heads.items():
            ur, bl = hd
            if len(bl) == 1:
                kb = bl[0][0]
                if kb < n:
                    inner = AT[kb] if kb < 7 else 2 * kb - 1
                else:
                    inner = kb
            else:
                comps = []
                for kb, r in bl:
                    cm = r
                    cl = [(kb, r)]
                    nrest = []
                    for m0, l0 in comps:
                        if m0 & cm:
                            cm |= m0
                            cl.extend(l0)
                        else:
                            nrest.append((m0, l0))
                    nrest.append((cm, cl))
                    comps = nrest
                inner = 0
                for cm, cl in comps:
                    cb = 0
                    for kb, r in cl:
                        if kb < n:
                            a = AT[kb] if kb < 7 else 2 * kb - 1
                        else:
                            a = kb
                        v = a + bin(cm & ~r).count("1")
                        if v > cb:
                            cb = v
                    inner += cb
            hinfo.append((inner, s, ur))
            innerof[s] = (inner, ur)
            # champion per-head term: first s + inner + one per extra symbol
            v = 1 + inner + bin(gref & ~((1 << s) | ur)).count("1")
            if v > best:
                best = v

        nh = len(hinfo)
        if nh >= 2:
            hinfo.sort(reverse=True)
            # multi-head term: t distinct head first-occurrences all lie
            # at/before the latest one p; after p that (adversarially chosen)
            # head's whole inner obligation still embeds, plus one occurrence
            # per referenced symbol outside the counted alphabets.
            pmask = 0
            pref = []
            t = 0
            for inner, s, ur in hinfo:
                pmask |= 1 << s
                pref.append((inner, ur))
                t += 1
                if t >= 2:
                    mn = -1
                    for inj, uj in pref:
                        v = inj + bin(gref & ~(pmask | uj)).count("1")
                        if mn < 0 or v < mn:
                            mn = v
                    v = t + mn
                    if v > best:
                        best = v
            # disjoint packing: heads whose {s}|U alphabets are pairwise
            # disjoint spend (1 + inner) on disjoint symbol sets, so they add.
            acc = 0
            wsum = 0
            cnt = 0
            for inner, s, ur in hinfo:
                vm = (1 << s) | ur
                if acc & vm == 0:
                    acc |= vm
                    wsum += 1 + inner
                    cnt += 1
            if cnt >= 2:
                v = wsum + bin(gref & ~acc).count("1")
                if v > best:
                    best = v

        # universe terms: m heads sharing exact universe u. The m distinct
        # first-occurrences all lie at/before the latest one p; after p all
        # perms of that head's rest (size >= k-1) must embed: m + A(k-1).
        for u, hm in by_u.items():
            k = bin(u).count("1")
            m = bin(hm).count("1")
            ex = bin(gref & ~u).count("1")
            km = k - 1
            a1 = AT[km] if km < 7 else 2 * km - 1
            v = m + a1 + ex
            if v > best:
                best = v
            if m >= 2:
                # refined: after the latest first-occurrence, that head's FULL
                # inner obligation embeds (adversary picks which head is last)
                mn = -1
                hh = hm
                while hh:
                    low = hh & -hh
                    hh ^= low
                    inj, uj = innerof[low.bit_length() - 1]
                    v = inj + bin(gref & ~(hm | uj)).count("1")
                    if mn < 0 or v < mn:
                        mn = v
                v = m + mn
                if v > best:
                    best = v
            if k < n:
                ak = AT[k] if k < 7 else 2 * k - 1
                v0 = ak + ex
                if v0 > best:
                    # all-perms coverage (generalizes m==k case): if every
                    # symbol of u heads some block whose universe CONTAINS u,
                    # then every perm of u is a prefix of a pending suffix,
                    # so all perms of u embed: A(|u|) inside u.
                    ok = True
                    uu = u
                    while uu:
                        low = uu & -uu
                        uu ^= low
                        hd = heads.get(low.bit_length() - 1)
                        if hd is None:
                            ok = False
                            break
                        found = False
                        for kb2, r2 in hd[1]:
                            if u & ~(low | r2) == 0:
                                found = True
                                break
                        if not found:
                            ok = False
                            break
                    if ok:
                        best = v0

        # pair-SCS over top-3 blocks (shared symbols opposed), plus one per
        # referenced symbol outside the pair's alphabet; skip DP when even
        # len(x)+len(y)+extras cannot beat current best.
        cands = [tt for tt in (t1, t2, t3) if tt is not None]
        nc = len(cands)
        if nc >= 2:
            for i in range(nc - 1):
                k1, s1, r1 = cands[i]
                for j in range(i + 1, nc):
                    k2, s2, r2 = cands[j]
                    u12 = (1 << s1) | r1 | (1 << s2) | r2
                    ex = bin(gref & ~u12).count("1")
                    if 2 + k1 + k2 + ex <= best:
                        continue
                    shared = r1 & r2
                    sh = [ts for ts in range(n) if shared >> ts & 1]
                    x = [s1] + sh + [ts for ts in range(n) if (r1 & ~shared) >> ts & 1]
                    sh.reverse()
                    y = [s2] + sh + [ts for ts in range(n) if (r2 & ~shared) >> ts & 1]
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
