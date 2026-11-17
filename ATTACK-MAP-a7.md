# ATTACK MAP — a(7) impossibility wall (A062714)

*Banked 2026-08-14 (session f1735d07, operator-directed). Living document — BREACH intake (#8)
ranks it when fired; rows get dated status changes, never silent deletions. Context: gen-1
champion banked (6.07M nodes / 1036.8s vs gen-0's 39.36M / 4621s on the n=6 no-27 sealed task);
n=7 no-38 projects ~2.4e11 nodes at gen-0 strength, ~3.7e10 at champion strength — still
infeasible; the map below is the portfolio of ways to close that gap.*

*CORRECTED 2026-08-14, same session, vector A's first result: the original header called a(7)
"a new OEIS value" — WRONG. OEIS A062714 lists a(1..9) = 1,3,7,12,19,28,39,52,66; the open cell
is **a(10)** (as this repo's own name says). n=7 (then 8, 9) are KNOWN-TRUTH CALIBRATION RUNGS
for the machine — the campaign's own minted pattern — en route to the real prize. Note also:
**n^2-2n+4 is already dead at n=9** (formula 67, truth 66; Engen-Vatter survey + OEIS), so
a(10) is not "84 per formula": best published upper bound is Radomirovic's ceil(n^2-7n/3+19/3)
= 83, and the pattern-break at 9 makes the true value genuinely open. Every vector below is
unchanged — they attack the machine's scaling, which climbs the whole ladder.*

## Core vectors

| # | Vector | Lineage | Status | Attacks | Honest note |
|---|---|---|---|---|---|
| 1 | Hand-built bound lb3 + proof machine (v3) | campaign | DONE | per-rung impossibility | closed a(6); defines the wall |
| 2 | Signed-memo lineage + witness-walk | campaign | DONE (n=6) | trust + yes-direction | reusable as-is at n=7 |
| 3 | Symmetry quotient + state compression (v1/v2) | campaign | DONE (v2.2) | state-space size | superseded by v3; compression not exhausted |
| 4 | Evolution gen-1 | 2026-08-14 | DONE — champion banked | bound strength | 6.5x node cut; residual: admissibility exhaustive n<=5 only |
| 5 | Gen-2 unhinted arm | sealed pre-reg | READY | does the loop compound? | caps re-sealed to champion; bank bar 694.7s |
| 6 | Gen-2 hinted arm (amortized-progress + relaxation families) | sibling-problem import (operator) | READY (sealed A/B) | untouched bound families | falsifier: U >= H => hints are decoration |
| 7 | Dominance/subsumption pruning | sorting-network n=13 import | staged, needs go | the SEARCH, not the bound | orthogonal axis, composes multiplicatively; needs own design + birth battery |
| 8 | BREACH pass on the wall | v7.x lineage -> Researches breach.md | staged, needs go | vector generation | meta: converts this map into a ranked list with cost estimates |
| 9 | WHY<=>HOW on champion inequalities | Condition Weakening v3 (operator) | staged | condition slack in banked bounds | CONVENIENT condition weakened = strictly stronger bound; inverse mode generates k-wise families |
| 10 | CTA operator algebra over the bound family | Principle-Operator Algebra (operator) | staged | mechanical recombination | reduction_factor missing-atom + compose/parameterize; feeder, not standalone |
| 11 | Inverted Reduction Gate | CRYSTAL.md | ALREADY LOAD-BEARING | — | it IS the engine core; licenses wilder proposer arms |
| 12 | Lean GAP-DETECTION on champion admissibility | Formalization capability (operator) | staged — STANDOUT | the named n<=5-only residual | sorry-list = exactly what is unproven at general n; symbolic closure would be a fragment of the missing induction (bound admissible FOR ALL n) |
| 13 | KG-EXP-NN blind audit of the champion | Multi-Lens Blind Audit (operator) | staged | plausible-but-wrong champion | 3-5 blind arms + MANDATORY null arm before champion carries n=7 weight |

## Additions from the v7.2 plugin-family evaluation (2026-08-14)

| ID | Vector | Most recent form | Note |
|---|---|---|---|
| A | FRONTIER literature re-scan | Deep Investigation / FRONTIER | lower-bound anchor is Kleitman-Kwiatkowski 1976 — 50 years unchecked; cheapest row on the board; could reorder everything. **RUNNING FIRST (operator go 2026-08-14) — cheapest-probe-first rule.** |
| B | Feasibility Oracle on our own 2.4e11 | Compute-Re-Audit capability | the steering number is an uncertified extrapolation; analytic recount per bound-strength scenario turns "years, roughly" into a decision surface for how many generations before the n=7 run is rational |
| C | REVERSAL-META over the campaign log | reversal_meta capability | measure which move-classes produced the wins; allocate gen-2+ effort by root-drivers |
| D | Framework Genesis | framework_genesis capability | ESCALATION ONLY: if #12's symbolic fragment shows life, "build the for-all-n framework" |
| E | Paper + OEIS lane | Paper Writing + auto-runtime/oeis-draft-watch.py | endgame when 39 is real; TRIAD fires on the outward artifact |

Remaining v7.2 plugins evaluated 2026-08-14: already mechanized into the current stack and
standing on this problem (discovery_engine->Self-Directed Search, campaign, provenance,
computation->ENVELOPE/PROBE-EXTEND, scale, triad, mathematics) or out of domain (lcars,
emergence, felt_creation, file_forensics, physics, paper-until-endgame). Full mapping in the
2026-08-14 session log.

## Axis structure (why rows stack instead of competing)

- Bound strength: 5, 6, 9, 10, 12
- Search mechanics: 7, 3-revival
- Trust: 12, 13, 2
- Vector generation / allocation: 8, A, B, C
- Endgame: D, E
