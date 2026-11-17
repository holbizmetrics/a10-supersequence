# GEN-3 PRE-REGISTRATION — **SEALED**

**SEAL TIME 2026-09-17T23:24:31Z** (clock substituted programmatically at the write, not typed). The commit
carrying this file IS the seal. Post-seal amendments may only TIGHTEN. **The seal precedes every
measurement in this round; any candidate number produced before this commit is not a gen-3 result.**

All three ⟨OPERATOR⟩ items of §7 were ruled by the operator before sealing (lane contract clause 5,
gen-3 composition and lane continuation are his): composition = pilot terms as PROPOSER INPUT with
no scored arm; k = 8; the sealed `D:` desktop is available for the attended foreground run.
Originally drafted 2026-09-17T23:03:46Z (clock substituted programmatically, not typed — a first draft of this line carried a GUESSED 2026-09-18T00:04:31Z while the clock read 23:03Z; second G12 fire this session, same mechanism both times: in one Bash call the heredoc is authored before the `date` output exists) by `termux-claude-a2f0c934`, phone, opus-5.
**Drafting is not running. No candidate has been sampled.**

## 0. Why this round is not a copy of gen-2's entry

Two consecutive candidates died of the SAME mechanism, and the lane has never measured it.

| | nodes vs champion | wall vs champion | outcome |
|---|---|---|---|
| gen-2 ARM H (cand_H_…_0) | **fewer** (3,776,512 < 3,857,090) | CAP-EXCEEDED | falsifier fired, arm dropped |
| P2 (champion + pilot terms) | **-32.5%** (2,602,809) | 0.948x — missed the 0.67x bar | NO BANK |

Both produced the strongest bound available and could not pay for it per node. Gen-2's own words:
*"10x stronger but 100x slower loses."* P2's entry adds the cross-box twist: the per-node penalty
was x1.074 on one box and x1.405 on the sealed one, so the economics are themselves substrate-
dependent and **wall RATIOS do not transfer between boxes**.

The lane's fitness axis is wall. The quantity that decided the last two rounds is **microseconds per
node**, and it has never been a pre-registered reported quantity. That is this entry's one addition.

## 1. Substrate — fixed, and the reason is now stronger than "units"

Sealed substrate: the operator's Windows desktop (`D:` box), **attended foreground**. Unchanged
since the 08-14 re-seal. The P2 result showed the single-substrate rule is not merely normalising
units so numbers compare — it is *the only thing that makes the candidate RANKING well-defined at
all*, because a candidate can win on one box and no-bank on another with no change to its code.

**No cross-box number may be used to predict this bar, in either direction.** A second-box reading
is disclosed if it exists (concealing it would not make it unknown) and licenses nothing.

## 2. Caps and bar — the standing formula, unchanged

Caps at the gen-2 champion `cand_U_1786732349_0`:
- `node_cap = 3,857,090`
- `wall_cap = 580.9s` → **floored to 580** by the harness's int argument, following gen-2's own
  precedent (1036.8 → 1036). 0.9s stricter than the formula, i.e. only ever harder to bank.
- **bank bar: wall ≤ 389.2s (0.67 × 580.9)** — the rule since the 2026-07-21 seal, applied verbatim
  in gen-1 and gen-2. Not chosen for this round or these candidates.

## 3. THE ADDITION — µs/node is a required reported quantity

For every candidate reaching Stage D, and for the champion re-run back-to-back in the same session:

    us_per_node = wall_seconds * 1e6 / nodes

Reported for every candidate whatever its verdict, banked or not. **This does not change the bank
bar** — wall ≤ 389.2s remains the sole banking criterion, so this addition can only add information,
never rescue a candidate. It exists because two rounds were decided by a quantity the ledger did not
carry, and a third would be a choice.

Pre-registered reading, fixed before data: if every candidate that reduces nodes below the champion
also raises µs/node enough to miss the bar, that is **evidence the cheap-amortised-progress shape is
not reachable by this proposer** — a real finding, to be reported as such. It is NOT a reason to
sample more candidates and look again.

## 4. Composition — RULED

Operator ruling, taken before the seal:

- **Target shape:** amortised-progress bound **implemented cheaply**. The gen-2 adjudication named
  this; P2 confirms the constraint is cost-per-node, not bound strength.
- **The two pilot terms** (size-2 adder, mutual-head) are carried as **proposer hints / candidate
  shapes**, which the courier row's "carry them as proposer hints" explicitly survives the P2
  no-bank. They are NOT a scored arm. **RULED: proposer input, no scored arm.**
- **NO ARM H.** Gen-2's falsifier fired on "hints earn a standing place" and hints stay DROPPED as an
  arm. One population, one scoring path. ⟨OPERATOR⟩ — this is the distinction most worth vetoing if
  I have read it wrong: hint-as-proposer-input survives, hint-as-scored-arm does not.
- **k = 8. RULED.** Gen-2's round size, which lost 3 of 8 to spawn races and a codeless reply and
  still closed. **Fixed before sampling; no optional stopping.** A round that scores fewer than 8 for
  mechanical losses is reported with its loss count, exactly as gen-2 was; losses are not resampled
  to reach 8.

## 5. No-retry — inherited verbatim from the P2 entry

ONE attended foreground run per candidate. **The first completed run is the result**: no best-of-N,
no warm-cache re-run, no discarding a number after reading it. An invocation that dies before
`prove_no` opens a timed window produces no number and does not engage this clause — but both
invocations are recorded, never one quietly dropped.

## 6. Falsifier for the ROUND

- **NULL:** no candidate banks → gen-3 closes with no champion, the n=7 rung stays gated exactly as
  the charter says, and the honest projection (2.3e10 – 8.1e10 nodes, 35–125 days single-core) stands
  unimproved. A null round is reported as a null round.
- **REFUTED:** if the banking candidate's µs/node is *higher* than the champion's, the "cost-per-node
  is the binding constraint" reading in §0 is wrong and this entry says so rather than keeping the
  frame that produced it.
- No candidate is rescued by a rule written after its number was read. Post-seal amendments may only
  TIGHTEN.

## 7. Owed before seal — ALL DISCHARGED 2026-09-17T23:24:31Z

1. ⟨OPERATOR⟩ §4 composition — **RULED: proposer input, no scored arm**
2. ⟨OPERATOR⟩ `k` — **RULED: 8**
3. ⟨OPERATOR⟩ sealed `D:` box available for an attended foreground run — **RULED: available**
4. Seal commit — **this commit**

## 8. What happens next, and who can do it

The proposer round may now open. **It cannot open here.** This file was written on the termux phone,
and the lane's fitness axis is wall on the sealed `D:` desktop under attended foreground — the P2
result established that wall RATIOS do not transfer between boxes, so no number produced anywhere
else is a gen-3 reading. The round is handed to whoever drives that box.

Handover contents, fixed by this seal and not renegotiable downstream:
- caps `node_cap=3,857,090`, `wall_cap=580` (floored int, gen-2 precedent), bank bar `wall ≤ 389.2s`
- k = 8, fixed; losses reported, never resampled
- proposer target: amortised-progress implemented **cheaply**; pilot terms as input shapes; no ARM H
- **µs/node reported for every Stage D candidate AND for the champion re-run back-to-back**
- one attended foreground run per candidate; first completed run is the result
