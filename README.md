# a10-supersequence — cracking A062714's next open cell

**Question:** what is a(10) — the minimal length of a word over 10 symbols containing all 10!
permutations as subsequences? Best known: 83 (Radomirović construction). Open question: does an
82 exist? OEIS A062714 ends at a(9)=66 (Garnashevich, Oct 2025), keyword "more" — a(10) is the
encyclopedia's next empty cell.

**Origin:** graduated 2026-07-12 from PCLA's EXPLORE sandbox
(`Prometheus-Crystal-Lab-Auto/.prometheus/explore/pcla-funsearch-loop/` — full falsification
history stays there as provenance). Produced in one overnight fleet session (desktop/laptop/linux
over the SecuredChat bus) + the Sunday graduation. This directory is the load-bearing core.

## GRADE stamps (per PCLA promotion discipline)

| Artifact | Grade | Basis |
|---|---|---|
| Suffix-resynthesis method (`resynth.py`) | **STANDARD**, correspondence-pending | 4-arm blind audit PASS/CLEAN (correctness proofs closed; 1,256/1,256 brute-force adjudication); literature pass found **no published match** (2026-07-12; Radomirović read primary; Engen–Vatter, Tan, OEIS, SCS lit swept). NOT claimed NOVEL: Garnashevich's private a(9) machinery is undocumented — correspondence is the settling move. |
| Exact verdicts (48/48 doomed prefixes; 83 rigid to depth 18 both ends; gap-3 word a certified 2-swap local optimum) | **DEFINITIONAL** given the instrument | Decidable procedure outputs; instrument validated both directions (YES 5/5+3/3 at-scale witnesses, NO 3/3 negative controls) + audit. |
| n=9 calibration PASS (pipeline independently found a fresh complete 66-word) | **STANDARD** | Pre-registered decision rule honored; slow-oracle 0-missing; word differs from Garnashevich's. Consequence (CORRECTED 2026-11-17, cross-family review by Codex): the calibration shows the pipeline CAN find a complete word at n=9; it does NOT turn the n=10 negative ledger into evidence for a(10)=83. A budget-capped search that finds nothing means NO FIND WITHIN BUDGET; only an exhaustive search or a proof establishes 83. Desktop lean 82-exists ~40% is a SUBJECTIVE judgment, not a calibrated probability, and says nothing about whether a given search can find such a word. |
| Search records 321→23→17→3 | historical | All provably dead-ended by resynthesis; kept as landscape data. |
| Proof machine rung zero (`search_suffix` from empty prefix) | **STANDARD** | Re-proved σ(3)=7, σ(4)=12, σ(5)=19 from scratch, BOTH directions (no-18 in 319 s). |
| Proof-machine ladder, v1 → v3.2 (`proofmachine_v{1,2,3}.py`) | **STANDARD**; n=6 CITES as theorem (2026-07-21) | Ladder n=3/4/5 green BOTH directions under audited v3. n=6 NO-direction: PROVED-NO on a signed-from-birth memo chain (21.3M-node final sitting, gen-0 bounds, H4/R6 — supersedes the unsigned v2.2 run). n=6 YES-direction: closed by verified witness-walk (`witness_walk.py` + `the28.json` — Newey's word, independently checker-verified, lb3 clean at all 28 steps; method amendment openly labeled after 3 search finders failed). |
| v2.3 audit, 4-lens + null control (2026-07-13) | instrument event, not a claim | Two CATASTROPHIC plumbing bugs found + fixed (unauthenticated memo = false-theorem vector, reproduced live; one-byte mask = the prover could not run at its own target n=10). Mathematics cleared exhaustively n≤5. Ladder made two-directional (v2.3b) — the one-directional ladder was structurally blind to over-pruning. |
| gen-0 bounds lb3 = B1/B2/B3 (`proofmachine_v3.py`) | **STANDARD** | One-line admissibility proofs PLUS exhaustive brute-force check n≤5 (12 / 183 / 84,974 canon classes, zero violations, null controls pass — `exhaustive_lb_check.py`, which doubles as the evolution-lane admissibility oracle) PLUS measured cheaper-AND-stronger than v2 lb per call (0.77x median cost; ≥ on 299/300 states). |

## Gate ledger (what ran at promotion)

- VERIFY-EXECUTIONALLY: pervasive (every verdict slow-oracle re-verified; fast/slow oracle exact-agreement instrument checks 10/10, 40/40).
- BLIND-VERIFY and beyond: 4-arm blind audit (correctness / execution / claims-conformance / null-control) — including a claims lens that caught and corrected the author's own "linux cold-confirmed" overclaim (FINDING UPDATE 5a).
- PARALLAX-literature: primary-source pass 2026-07-12 (FINDING UPDATE 5b).
- IMPLICIT SCAN (at this promotion): resonant — Deep Investigation, Mathematical Awareness, Self-Directed Search (the inverted-gate/FunSearch shape), Novelty Catechism (fired correctly, repeatedly), Compute-Re-Audit (budget-bound catches), PROBE-EXTEND (n=4 invariants killed at n=5). Deliberately silent — Formalization/Lean (correct: coverage is finite exact computation; reserved for the believability layer), Paper Writing (resonates at submission time).
- OWED (named, not hidden): cold-reader TRIAD standpoint on the FINDING doc; linux cold-score of the gap-3 word (requested, never answered — it is self-verified ×2 local oracles only); Garnashevich/von Brömssen correspondence.
- Falsifier-first pre-registration (2026-07-20/21): H1 sealed by commit BEFORE measurement → falsified by its own rule (wall axis; the run was killed per the sealed rule) → cause discriminated by a second sealed micro-bench (environmental, not algorithmic) → H2 filed for the correct substrate. The full H1/H2 + R1/R2/R3 chain lives in PCLA's hypothesis/results registries and CAMPAIGN-a10.md § Rung log.
- NULL-CONTROL-AT-BIRTH honored on both new instruments: v3.1 memo-signing (planted forged memo refused, exit 2, at birth) and the exhaustive checker (DP root-truth must reproduce proven a(3)/a(4)/a(5) before any verdict counts — passed 7/12/19).

## The campaign

See `CAMPAIGN-a10.md`: one complete search decides both outcomes (finds the 82, or exhausts =
proof a(10)=83). Validation ladder n=3..9 has proven ground truth at every rung. Current state
(2026-07-21): ladder green n≤5 in BOTH directions under audited v3.1; n=6 a full theorem BOTH
directions — no-27 on a signed-from-birth memo chain (21.3M-node final sitting, H4/R6;
supersedes the unsigned v2.2 96.25M run, which agrees) and yes-28 by verified witness-walk
(`the28.json`). Engineering ladder: v1 canonical states (shipped) → v2 block-compressed states
+ dominance + signed memos (shipped) → v3 gen-0 proven bounds (shipped; measured cheaper AND
stronger than v2's lb) → v3 evolution (OPEN — opener shipped 2026-07-21: `EVOLUTION-LANE.md`
+ `evolve_bounds.py`, birth battery 18/18; every candidate gates through the uncheatable
admissibility oracle `exhaustive_lb_check.py`; gen-0 Stage-D calibration fixes the caps). Honest rule: **no n=10 run
before n=9 terminates; no scaling claim without measured rungs.** Live state, pre-registrations,
and every adjudication: `CAMPAIGN-a10.md` § Rung log (append-only).

Kinship: `../ai-discovering-mathematics/` (the reflective campaign this one is a live specimen of).
