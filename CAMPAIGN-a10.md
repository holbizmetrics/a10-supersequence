# CAMPAIGN: crack a(10) — the proof machine (operator: "I am in", 2026-07-12 ~07:00)

**Goal.** Determine a(10) (A062714, OEIS's next open cell). One complete search decides BOTH
outcomes: it finds an 82-word if one exists, or exhausts the tree = proof that a(10)=83
(the 83 is already in hand; a no-82 run closes the cell).

**The machine already exists at rung zero.** `search_suffix(all n! perms, n, L)` from the empty
prefix IS the decision procedure "does any complete word of length L over n symbols exist."

**Validation ladder (every rung has proven ground truth):**
| rung | question | truth | v0 status |
|---|---|---|---|
| n=3 | no-6 / yes-7 | sigma(3)=7 (Newey, proven) | BOTH OK, <0.01s |
| n=4 | no-11 / yes-12 | sigma(4)=12 (proven) | BOTH OK, 0.04s |
| n=5 | no-18 / yes-19 | sigma(5)=19 (proven) | **BOTH OK — no-18 proved in 318.6s** |
| n=6 | no-27 / yes-28 | sigma(6)=28 (proven) | open — needs v1 |
| n=7 | no-38 / yes-39 | sigma(7)=39 (proven) | open |
| n=8 | no-51 / yes-52 | a(8)=52 (Tan proof + word) | open |
| n=9 | no-65 / yes-66 | a(9)=66 (Garnashevich) | open — the big calibration |
| n=10 | no-82 (or find 82) | **OPEN — the target** | after n=9 terminates |

**Engineering ladder (v0 -> the machine that reaches n=10):**
1. v1 — canonical states + symmetry quotient (relabel x n!, reversal x2; linux's G frame).
   State = set of pending remainder suffixes; canonicalize under symbol-permutation.
2. v2 — block-compressed states (the (first, rest-set) representation from resynth) +
   state-dominance pruning (state A dominates B if every pending suffix of A is a suffix
   of one in B — prune dominated).
3. v3 — EVOLVED pruning bounds: FunSearch loop proposing admissible LB functions; oracle =
   (a) admissibility mechanically verified vs brute-force SCS on small tuple sets (decidable,
   uncheatable), (b) strength scored by nodes pruned on a fixed benchmark. The loop improving
   its own prover.
4. At each version: re-run the ladder bottom-up; each rung's wall-clock extrapolates the next.
   HONEST RULE: no n=10 run before n=9 terminates; no scaling claim without measured rungs.
5. Believability layer (before any a(10) claim): proof-logging of pruned branches, second
   independent implementation spot-checking subtrees (decorrelated, the linux pattern),
   published code, OEIS submission; optional Lean-checked verdict layer (two-kernel rung).

**Fallbacks if n=9 extrapolates beyond desktop:** distribute across the fleet / cloud;
correspondence with Garnashevich + von Brömssen (they hold private methods for a(8)/a(9);
our evidence packet + method are the opening).

**Context (what tonight established — FINDING doc UPDATEs 4-6):** search records 321->3 all
provably dead-ended; suffix resynthesis built+audited (4 blind lenses)+literature-checked
(no published match); 83 rigid to depth 18 both ends; warmth-lane walls structurally;
calibration hunt PASSED at n=9 (pipeline independently found a fresh complete 66) => the
negative ledger is real evidence [CORRECTED 2026-11-17 (Codex cross-family review): it is NOT -- the
calibration shows the pipeline can find a word at n=9; a capped search that finds nothing at n=10 means
NO FIND WITHIN BUDGET, never a(10)=83; see README row 'n=9 calibration']; desktop lean (subjective, not
calibrated): 82 exists ~40%. Either way the campaign
resolves it: the search IS the theorem.

## Rung log (append-only)
- 2026-07-12 v0: n=3/4/5 both directions GREEN (no-18: 318.6s, frozenset states, no quotient).
- 2026-07-12 v1 (canonical states, symmetry folded into memo): no-6 18 nodes / no-11 747 nodes /
  no-18 1,527,436 nodes @ 87.6s (3.6x v0). Measured growth n=4->n=5 ~2000x nodes => v1 does NOT
  reach n=6 in pure Python (nodes ~1e9+, memo > RAM). v2 requirements, from data: jitted core,
  compressed state encoding, stronger admissible LB (the evolved-bounds program earns its place
  here), possibly disk-backed or bounded memo.
- 2026-07-12 v1.1 (pair-SCS + outside-demand additive bound): no-6 12 / no-11 386 /
  no-18 610,390 @ 72.9s (2.5x fewer nodes than v1; verdicts unchanged). Growth n=4->5 ~1580x
  => n=6 ~1e9 nodes / ~33h / memo >30GB in pure Python. v2 (packed states + jit + memo policy)
  is the gate to n=6.
- 2026-07-13 v2.2 RUNG n=6 GREEN: **no-27 PROVED** (96,252,664 nodes, memo 17.0M, 3h13m, round 3
  — rounds 1-2 externally killed ~36-40M; detached+snapshotted run sailed through; kills traced
  to outside the process, harness task-tracker suspected). Third ground-truth match. Growth
  n=5->n=6 = 22,700x nodes => **n=7 no-38 projects ~2e12 nodes = out of reach for v2** — the
  evolved-bounds program (v3) is now MANDATORY before the next rung, per charter. Memo snapshot
  (memo_n6_L27.pkl, ~800MB) kept local, not committed.
- 2026-07-13 v3 gen-0 RUNG n=6 RE-PROVED: 39,357,621 nodes / 69min (2.45x under v2's 96.25M;
  same verdict from independent bound-set = cross-implementation consistency). Ladder: no-6 10 /
  no-11 22 / no-18 1,868. HONEST n=7 MATH: ~2e12 / 2.45 ~ 8e11 nodes ~ 2.7 YEARS at current
  rate => gen-0 alone does NOT unlock n=7. The EVOLUTION HALF of v3 (bounds_lab: FunSearch over
  candidate bounds; admissibility falsifier = exact-solve on small states; strength = nodes
  pruned on benchmark sampled from the 17M-state n=6 memo; evolve->prove->deploy contract) is
  now the campaign's critical path. Also candidates for v4 machinery: numba'd core (~10x),
  better canon (perfect canonicalization), parallel root-branch split across processes.
  *(Entry restored 2026-08-14 from stranded desktop commit abbbf40 — see the 2026-08-14
  MERGE-NOTE at the end of this log.)*
- 2026-07-20 PRE-REG (laptop session a7d4ea17, sealed BEFORE the measurement — falsifier-first):
  **v3 gen-0 strength at n=6.** INSTRUMENT CONDITION found on resume: the v3 runner is MISSING both
  deep v2.3 audit fixes — its own `memo_v3_*` path loads an unauthenticated pickle (BUG-1 class,
  the false-theorem vector, reopened) and its ladder runs the no-direction only (BUG-3 class, blind
  to over-pruning). Port signed-memo + both-directions ladder into v3 BEFORE any run; ladder
  n=3/4/5 both directions must be green under lb3, else STOP (bug hunt; nothing banks).
  MEASUREMENT: prove_no(6,27) from a FRESH v3-signed memo on this laptop.
  DECISION RULE (pre-registered): PASS = PROVED-NO at ≤10,000,000 nodes AND ≤60 min wall
  (v2.2 baseline 96.25M nodes / 3h13m => the bar is a ≥9.6x node cut; deliberately looser than
  the 326x cut gen-0 showed at n=5, because bounds decay with n). On PASS: bank the strength
  datum; growth n=5→n=6 measured v3-native; n=7 projection = nodes(6) × that growth; if the
  projection exceeds ~5e9 nodes, the evolution loop (v3 FunSearch) is MANDATORY anyway.
  FALSIFIED = either budget exceeded => kill the run, verdict "gen-0 insufficient at n=6",
  evolution mandatory before n=7, and the n=6 signed-theorem re-run waits for stronger bounds
  or the desktop. Either way: NO n=6 theorem citation until BOTH directions at n=6 have run from
  fresh signed memos (the no-28/YES direction is budgeted after the no-27 result lands — its cost
  is reported, not pre-committed). Registry: PCLA `hypothesis-registry.md` row H1 (the registry's
  first forward-only row, per operator ruling 2026-07-20).
- 2026-07-21 RESULT (adjudicating the 2026-07-20 pre-reg): **FALSIFIED — gen-0 insufficient at n=6
  on this substrate.** Run killed per the sealed rule at ~14.5h wall (60-min budget exceeded ~14.5x);
  last in-process progress 4,000,000 nodes @ 51,796s, snapshot at 5M (memo 973,341 entries, signed,
  kept local). The 10M-node axis was never adjudicated — the wall axis decided. Two instrument
  findings ride the verdict: (1) MSYS `timeout 3600` did NOT kill native Windows python — the wall
  axis was theater; the falsifier fired by observation + manual tree-kill (tasklist re-scan verified).
  FIX in this commit: wall budget now enforced IN-PROCESS (`--wall-budget`, time.time()-based so
  suspend counts), same mechanism as the node budget. (2) Throughput anomaly: ~46 nodes/s to 2M
  (overnight — sleep/throttle suspected), ~237 nodes/s from 2M to 4M (machine awake) vs v2.2's
  ~8,300 nodes/s on the same rung. Even awake, ~35x slower per node — lb3's per-node cost is the
  suspect, UNDIAGNOSED. This shapes the evolution lane: fitness must be WALL-CLOCK (nodes x
  per-node cost), never nodes-pruned alone — a bound that prunes 10x but costs 100x per node is a
  regression. DIAGNOSIS OWED before evolution-lane design: micro-bench lb vs lb3 on fixed n=6 states.
  CONSEQUENCES per pre-reg: evolution lane (v3 FunSearch) MANDATORY before n=7; the n=6
  signed-theorem re-run waits for cheaper/stronger bounds, the desktop, or a jitted core. Honest
  residual: gen-0's true nodes-to-completion at n=6 remains UNKNOWN (may still beat v2.2's 96.25M;
  what is refuted is exactly H1's claim — ≤10M nodes inside 60 min on this laptop). Registries:
  PCLA R1 filed, H1 → dropped (falsified).
- 2026-07-21 PRE-REG (micro-bench, sealed before running — the R1 owed diagnosis): time v2.lb vs
  v3.lb3 per-call on the SAME ~300 reachable n=6 states (random advance-walks from root; min-of-50
  timing per state) + compare bound VALUES on those states. DECISION RULE: ratio lb3/lb (median)
  ≤5x AND lb3 median <500µs → gap was ENVIRONMENTAL (sleep/throttle) → file H2 (n=6 within budget
  on an awake/desktop box) rather than jumping to evolution; ratio ≥20x OR lb3 median ≥2ms →
  ALGORITHMIC → evolution fitness = wall-clock, first target = cheaper lb3; in between → both
  lanes named, operator picks. Strength side reported alongside (lb3>lb / = / < counts) — no
  decision rides on it here.
- 2026-07-21 RESULT (micro-bench, adjudicating the same-day pre-reg): **ENVIRONMENTAL — and gen-0
  is BOTH cheaper and stronger per call.** 300 reachable n=6 states (seed 62714, min-of-50):
  v2.lb median 27.4µs vs v3.lb3 median 21.0µs → ratio **0.77x** (environmental bar was ≤5x AND
  <500µs — passed with two orders of margin); strength on the same states: lb3>lb 244 / equal 55 /
  weaker 1. The bound is ~0.5% of the observed 4.2ms/node awake pace → the 35x collapse is the
  SUBSTRATE, not the algebra (leading suspect: Win11 EcoQoS/efficiency throttling of a detached
  background python on the Komax laptop overnight; named, unproven, sidestepped by moving boxes).
  CONSEQUENCES per rule: **H2 filed** — n=6 no-27 within both in-process budgets on the awake
  DESKTOP (the 8.3k-nodes/s box: 10M nodes ≈ 33 min, inside the wall; this laptop even awake
  ≈ 12h, never the H2 substrate). Evolution machinery WAITS on H2: the charter's v3-before-n=7
  mandate stands, but if gen-0 alone clears n=6 cheaply on real hardware, the n=7 extrapolation
  base resets before any FunSearch spend. Parked cheap option: max(lb, lb3) per node (+27µs,
  covers the 1 weaker state) — only if H2 shows node count dominates per-node cost. Registries:
  R2 filed; courier row stages the desktop run.
- 2026-07-21 EXHAUSTIVE ADMISSIBILITY n≤5, BOTH bounds (`exhaustive_lb_check.py`): **lb AND lb3
  admissible on EVERY reachable canon class** — n=3: 12 classes / n=4: 183 / n=5: 84,974 (12.1s
  laptop), zero violations, tightest slack 0 for both. Built-in null controls PASS at every rung
  (DP root-truth reproduced a(3)=7 / a(4)=12 / a(5)=19). Method: memoized completion DP over canon
  classes (truth = 1 + min over heads; heads-only WLOG; class-level check sound by the canon
  bijection argument — truth/lb/lb3 all relabel-invariant). SUPERSEDES the dangling 2026-07-13
  sampled n=5 fuzz (coverage: every class vs 400 samples; the sampled BFS-per-state design is why
  it hung — near-root states re-swept millions of states per sample). lb re-check REPRODUCES the
  v2.3 audit's exhaustive zero-violation verdict (instrument cross-validation); lb3 — the bound H2
  deploys — now has exhaustive-n≤5 empirical evidence on top of its one-line proofs. This is also
  the EVOLUTION-LANE ADMISSIBILITY ORACLE: any evolved candidate bound must pass this same
  instrument (swap the bound, run n≤5) before touching a proof run. PCLA registry: R3.
- 2026-07-21 PRE-REG (throughput probe, sealed before running): foreground/attended n=6 probe on
  the Komax laptop — prove_no(6,26) (L=26 so the L27 evidence memo stays untouched), node budget
  300,000 / wall 90s in-process; the BUDGET-EXCEEDED line's nodes+seconds IS the measurement
  (verdict-free by design). DECISION RULE: ≥1500 nodes/s attended → background-throttle (EcoQoS
  class) CONFIRMED as the R1 mechanism; a laptop-ATTENDED H2 variant becomes viable (~≤2h) as a
  second-substrate option. ≤400 nodes/s → laptop is simply slow; desktop remains the sole H2
  substrate. Between → partial throttle; desktop still preferred. Probe memo (memo_v3_n6_L26.pkl)
  is a discardable probe artifact, deleted after with the deletion announced.
- 2026-07-21 RESULT (throughput probe): **THROTTLE CONFIRMED — the attended laptop beats the
  desktop baseline.** 300,001 nodes in 26.9s foreground = **~11,152 nodes/s**, vs 237/s background
  (47x) and 8,300/s desktop-v2.2. The ≥1500 bar passed 7.4x over → EcoQoS-class background
  throttling IS the R1 mechanism, and "laptop never the H2 substrate" is OVERTURNED for ATTENDED
  runs (10M nodes ≈ 15 min attended on this box). **H3 filed:** n=6 no-27 within budgets via
  chunked ATTENDED foreground runs (signed-memo resume across chunks; background/unattended chunks
  remain INVALID substrate — the throttle is the substrate). H2 (desktop) stays open in parallel;
  whichever box adjudicates first closes the rung. PCLA registry: R4. Probe memo deleted per
  pre-reg.
- 2026-07-21 RESULT (H3 chunked attended run): **FALSIFIED at exactly 10,000,001 cumulative nodes,
  no verdict.** Chunk 1: 5,783,552 nodes / 540.3s (10,704/s); chunk 2: 4,216,449 / 402.6s
  (10,473/s) — attended rate HELD, so this is an ALGORITHMIC answer: gen-0 does not deliver the
  ≥9.6x node cut at n=6 (the 326x cut at n=5 decayed with n, the possibility the H1 pre-reg
  priced in). Signed memo banked at 2,926,878 entries — durable; future runs resume it.
  CONSEQUENCES per the sealed chain (H1+H3 both falsified the 10M bar): **EVOLUTION LANE NOW
  MANDATORY before n=7.** H2 (desktop, same 10M bar): cumulative fresh exploration ≈15M nodes
  without verdict makes its bar near-certainly unreachable → H2 DROPPED (withdrawn bet, not a
  claimed negation — a fresh-memo run explores in different order and is not strictly bounded by
  our chunked count). The desktop task is RE-TASKED (bus follow-up to 78ab3b54): **H4 — measure
  gen-0's TRUE completion cost at n=6** (wall-budget only, NO node cap, fresh or resumed memo,
  either box attended): if total < 96.25M nodes, gen-0 beats v2.2 and is the evolution baseline;
  if ≥, the three proven bounds add nothing at n=6 and evolution starts from v2-lb. Fitness for
  evolution stays WALL-CLOCK (nodes x per-node cost) per the R2 lesson.
- 2026-07-21 H4 LAPTOP LANE (operator GO; accounting sealed before chunks): attended 9-min chunks
  resuming the banked signed memo, NO node budget, single logical core (pure single-threaded
  python; RAM is the real watch-item — memo could grow toward v2.2's 17M entries). ACCOUNTING:
  chunked resume OVER-counts nodes vs one sitting (re-walk of memoized territory) → adjudicate H4
  conservatively on CUMULATIVE chunk nodes: cumulative < 96,252,664 ⇒ gen-0 beats v2.2 under any
  accounting; also report final-chunk standalone count (the figure most comparable to v2.2's own
  resumed round-3 number). STOP rules: verdict / memo file >~1.5GB / fresh-entries-per-chunk
  collapses (<~200K = thrash, hand to desktop) / operator says stop. Desktop H4 (bus 913fb6eb)
  stays live in parallel — a fresh-memo desktop run is its own clean measurement; first completion
  closes H4.
- 2026-07-21 MECHANISM CORRECTION (R4 attribution downgraded; the record punishes overclaiming):
  chunk 1 of the laptop lane ran 3.05M nodes/541s with fresh-progress decay (thrash trajectory) →
  switched to a single-sitting background run with an in-process EcoQoS opt-out (v3.2,
  `--no-throttle`). The opt-out API returned FAILURE — yet the unwrapped background spawn runs at
  ~3.4–5.9k nodes/s, matching the attended rate at current memo size (3.52M entries). So: the R1
  phenomenon (that process 47x slow, even after the machine woke) STANDS as measured; the
  "EcoQoS-class" mechanism attribution is WITHDRAWN — prime suspects now the MSYS `timeout`
  wrapper parentage or spawn-time machine state; genuinely UNRESOLVED, and operationally moot
  (unwrapped background = full rate). H4 single-sitting run live: 4h wall cap, no node cap,
  signed-memo resume from 3,519,365 entries, snapshots every 5M nodes.
- 2026-07-21 RESULT — **H4 PASSES: n=6 no-27 PROVED-NO, and gen-0 IS the evolution baseline.**
  Final sitting: 21,310,406 nodes / 3,931.7s (65.5 min, laptop, one core), final memo 7,468,678
  entries, ENTIRE memo lineage signed-from-birth on this box (fingerprint-verified at every
  resume) — the audit's "re-run n=6 from a fresh signed memo" recommendation is DISCHARGED for
  the no-direction. Adjudication per sealed rule: conservative cumulative across ALL runs on this
  rung ≈ 39.4M nodes (≈5M killed-H1 + 5.78M + 4.22M + 3.05M chunks + 21.31M sitting) —
  **beats v2.2's 96,252,664 by ~2.4x under any accounting**; cleaner strength metric:
  **7.47M memo states vs v2.2's 17.0M = 2.3x state-space cut.** v3-native growth n=5→n=6 ≈
  1,868 → ~21-39M ≈ 11,400-21,100x ⇒ **n=7 projects ~2.4e11+ nodes — evolution lane stays
  MANDATORY, now with a measured baseline** (evolved bounds must beat gen-0's 21.3M-node /
  7.47M-state n=6 figure at wall-clock-honest fitness). YES-direction (no-28, required by the H1
  seal for full theorem citation): probe BUDGET-EXCEEDED at 5,644,288 nodes / 540s, own memo
  snapshotted (1,097,222 entries) — cost reported as pre-committed; continuation running in
  background; **n=6 theorem citation stays PENDING until it lands False.** Registries: H4 →
  satisfied-by R6; desktop task 913fb6eb/bc0e3201 SUPERSEDED (fleet notified).
- 2026-07-21 WITNESS-WALK instrument (`witness_walk.py`) — closure-by-witness for YES-directions:
  find a complete word, verify with the INDEPENDENT checker (`is_complete`, shares no code with
  the prover), then walk it through advance+lb3 asserting bound ≤ depth_left at every step (if a
  complete path survives every bound check, the prover cannot over-prune it — the YES-direction's
  epistemic content, decidable, no search luck). Openly-labeled METHOD AMENDMENT vs the seal's
  "run prove_no(n,a(n))" wording; DFS route stays available. **n=5: CLOSED-BY-WITNESS in 1.9s**
  (fresh 19-word 1432041234012430214, checker-complete, walk clean at all 19 steps). **n=6: witness
  NOT FOUND by three finders** — greedy rollouts 0/20,000, coverage hill-climb saturates
  near-complete, best-first DFS 5M nodes (plus the arbitrary-order DFS's 82.16M-node / 2h wall
  earlier, memo 16.2M entries banked in memo_v3_n6_L28.pkl) — exact-length witnesses at n=6 are
  razor-sparse for these finders. Honest state: n=6 theorem citation REMAINS PENDING. Parked
  next routes: literature's explicit σ(6)=28 word (Newey/Koutas-Hu construction — fetch + verify
  with is_complete + walk = minutes), or a bigger best-first budget on the desktop.
- 2026-07-21 **n=6 YES-DIRECTION CLOSED — THEOREM CITATION UNLOCKED.** The parked literature route
  executed: Newey's explicit σ(6)=28 word (OEIS A351468; search-sourced, so provenance treated as
  UNTRUSTED and every property re-established locally): `is_complete` (independent checker, no
  shared code) confirms all 720 permutations; witness-walk confirms lb3 ≤ depth_left at ALL 28
  steps → the prover provably cannot over-prune a completion path at (6,28). Word banked as
  `the28.json` (source-annotated). **n=6 rung now cites as theorem** with the method note stated
  plainly: NO-direction = signed-memo exhaustive search (H4/R6); YES-direction =
  verified-witness-walk (method amendment vs the seal's DFS wording, openly labeled — 3 search
  finders had failed; the property established is identical). Ladder state: n≤5 both directions
  by search, n=6 both directions (search + witness-walk). Next rung n=7 remains gated on the
  evolution lane (~2.4e11 projected nodes).
- 2026-07-21 EVOLUTION-LANE OPENER (design + harness + birth battery; PRE-REG sealed before any
  candidate measurement). Design: `EVOLUTION-LANE.md`; harness `evolve_bounds.py` (canon-wrap
  deploy form — constant on canon-key classes by construction, packed↔unpacked bijection
  battery-locked; evaluator cascade A admissibility-exhaustive-n≤5 / B cost / C strength-screen /
  D wall-clock fitness; curated-exec loader; per-candidate scratch cwd + candidate-covering memo
  fingerprint; claude -p proposer WRITTEN, dry-run-verified only). Birth battery
  `test_evolve_bounds.py`: 18/18 GREEN — and its FIRST run caught a real contract gap (weak-plant
  arm: zero bound returned WORD-EXISTS at n=4 L=11 vs proven sigma(4)=12 — prove_no's dfs has NO
  explicit depth guard; `bound > depth_left` IS the guard, so deployed bounds must be ≥1 on
  nonempty states). FIX: the deploy wrap floors at 1 on nonempty (always admissible:
  truth(nonempty) ≥ 1); floor battery-locked. NULL-CONTROL-AT-BIRTH earned its keep on its own
  harness, birth day.
  SEALED RULES (before any measurement, falsifier-first):
  (1) CALIBRATION — gen-0 (lb3 as deployed, unwrapped) through Stage D: attended foreground
  fresh-memo prove_no(6,27), NO node cap, wall cap 7200s in-process. Its measured (nodes_0,
  wall_0) fix the candidate caps: node_cap = nodes_0, wall_cap = wall_0 — verdict-under-cap ≡
  beats gen-0 by construction. If calibration exceeds its wall cap: no candidate measurement
  until caps are re-sealed from v2.2's figures in a fresh entry.
  (2) BANK RULE (gen-1) — a candidate BANKS iff Stage A CLEAN (zero violations n=3/4/5, root
  truths 7/12/19 intact) AND Stage D PROVED-NO under caps AND wall ≤ 0.67 × wall_0 (≥1.5×
  wall-clock cut — fitness axis is WALL-CLOCK per R2; nodes reported alongside, never the axis).
  (3) SCREEN KILLS (pre-committed) — Stage A violation / crash / non-int / 300s in-process wall;
  Stage C dominated (never higher than lb3 on the fixed 300 states, seed 62714); Stage B median
  ≥2ms (R2's algorithmic bar).
  (4) SUBSTRATE — all Stage D runs attended foreground with in-process budgets (R1/R4:
  background = invalid substrate on this laptop; MSYS timeout never used).
  Context: gen-0's H4 figure (21.3M nodes / 65.5 min) was RESUMED-lineage; the calibration run is
  its fresh-memo replacement and the first per-candidate-comparable baseline.
- 2026-08-14 MERGE-NOTE (un-stranding, courier row 204, session d9d555c1, dispatch cacc78af):
  the 2026-07-13 "v3 gen-0 RUNG n=6 RE-PROVED" entry above was stranded in local-only desktop
  commit abbbf40 while the 2026-07-20/21 laptop arc was written unaware of it; restored here in
  chronological position, BOTH accounts kept per the dispatch's falsifier-first rule.
  Reconciliation recorded, not adjudicated: (1) the desktop figure ANSWERS the 07-21 H1 honest
  residual ("gen-0's true nodes-to-completion at n=6 remains UNKNOWN") — 39.36M fresh-run desktop
  nodes, beating v2.2 2.45x; the near-identity with the laptop arc's conservative cumulative
  ≈39.4M is a coincidence of DIFFERENT quantities (one fresh sitting vs cross-run cumulative),
  not corroboration. (2) The desktop run PRE-DATES the 07-20 instrument findings (unauthenticated
  memo pickle; ladder no-direction-only — and its recorded ladder is indeed no-direction), so
  theorem-grade citation keeps preferring the signed-memo H4 lineage + witness-walk closure; the
  desktop entry stands as the cross-implementation consistency datum its own text claims, at
  hypothesis tier. (3) The evolution-lane calibration seal (07-21 rule 1) named laptop substrate
  + attended-foreground; the desktop figure does not discharge it. Baseline tension for the
  evolution lane is now explicit: gen-0 n=6 = 21.3M nodes (laptop resumed lineage) vs 39.36M
  (desktop fresh, pre-fix instrument) vs 96.25M (v2.2) — the sealed calibration run remains the
  arbiter for candidate caps.
- 2026-08-14 **DESKTOP RE-SEAL (fresh sealed entry, PRE-REG before any measurement)** — session
  f1735d07 (PCLA engine lane, courier row 209), operator ruling relayed via bus 477e87ef
  (Holger, in session d9d555c1's chat): calibration substrate re-registered to THIS DESKTOP
  (D: box), attended foreground. Authority = the 2026-07-21 seal's own re-seal provision; this is
  re-registration, not loosening — every rule below sealed BEFORE the calibration run, and this
  entry is pushed to origin/main before any Stage D measurement (its commit SHA relayed to
  d9d555c1 per the ruling's decidable-check).
  (1) CALIBRATION (desktop) — gen-0 (lb3 as deployed, unwrapped) through Stage D: attended
  foreground, FRESH MEMO, prove_no(6,27), NO node cap, wall cap 7200s in-process, single
  logical core, no MSYS timeout wrapper (R1/R4 carried). Its measured (nodes_0, wall_0) alone
  fix the candidate caps: node_cap = nodes_0, wall_cap = wall_0. If calibration exceeds 7200s:
  no candidate measurement until caps are re-sealed from v2.2's figures in a fresh entry
  (07-21 provision carried verbatim).
  (2) DEAD BASELINES (operator condition 2) — the 2026-07-13 desktop figure (39.36M nodes,
  abbbf40; pre-dates the 07-20 instrument fixes) and the laptop resumed-lineage figure (21.3M)
  are CONTEXT ONLY. Neither fixes caps; only this entry's fresh calibration numbers do.
  (3) SUBSTRATE COEXISTENCE (operator condition 3) — the 1e7 prime-gap run (PID 56000) owns
  background CPU on this box: it is not killed, starved, or touched. Load-comparability rule,
  falsifier-first: calibration and every gen-1 Stage D measurement must run under the SAME
  background-load condition (PID 56000 present-throughout or absent-throughout). If the
  prime-gap run lands mid-lane, candidate measurement HALTS until calibration is re-run under
  the new load and caps re-fixed in a dated addendum here. A cap comparison across load
  conditions is invalid by construction.
  (4) UNCHANGED FROM 07-21 SEAL — bank rule (Stage A CLEAN + PROVED-NO under caps + wall
  <= 0.67 x wall_0; fitness axis WALL-CLOCK, nodes reported never the axis) and screen kills
  (Stage A violation / crash / non-int / 300s in-process wall; Stage C dominated on the fixed
  300 states seed 62714; Stage B median >= 2ms) carry verbatim.
  (5) PRECONDITION DISCHARGED — birth battery test_evolve_bounds.py re-run on THIS box
  2026-08-14: ALL GREEN (23.0s), discrimination confirmed both directions (gen-0 22 nodes vs
  zero-bound 547 at n=4 L=11). No candidate verdict is trusted without this battery green on
  the measuring box.
- 2026-08-14 **DESKTOP CALIBRATION RESULT (the sealed run above, executed): PROVED-NO —
  nodes_0 = 39,357,621 · wall_0 = 4621.4s · memo 7,468,678 entries.** Fresh memo, no node
  cap, in-process wall cap 7200s, single core, workdir evolution-runs/gen0-n6L27-1786673468
  (kept). **CAPS NOW FIXED per rule 1: candidate node_cap = 39,357,621, wall_cap = 4621.4s;
  bank bar wall <= 3096.3s (0.67x).** Load condition: absent-throughout (PID 56000 landed
  03:23; a first calibration attempt begun 03:1x under present-load was VOIDED at the
  boundary per rule 3 and discarded unread — this run started 04:11:07 on the quiet box).
  Rate ~8,500 nodes/s sustained, inside the unthrottled band. TRANSIENTS DISCLOSED
  (falsifier kept, bus ac2a3386): two minute-scale suite runs overlapped the 77-min sitting
  (this session's row-204 verification ~2.5 min at 04:5x incl. one lean subprocess; session
  675bcb24's row-203 full suite) plus ambient constants (two bus wake-monitors, spool
  server). Ruled below rule-3 granularity — the named axis is the sustained ~1-core load,
  and candidates run under the same ambient; any future candidate verdict within noise of
  the 0.67x bar names these transients first suspect. CROSS-LINEAGE CONSISTENCY, recorded
  not adjudicated: nodes reproduce the 2026-07-13 pre-fix desktop figure (39.36M) to ~0.01%,
  and final memo count EQUALS the laptop H4 signed-lineage end state (7,468,678 entries
  exactly) — deterministic state space across boxes and instrument versions; wall is the
  substrate-dependent axis, which is why fitness is wall-clock on ONE sealed substrate.
- 2026-08-14 **GEN-1 ROUND (first real evolution round) — CANDIDATE 1 BANKS: PROVED-NO in
  6,067,024 nodes / 1036.8s = 0.22x wall_0 (bank bar was 0.67x).** 6.5x node cut, 4.5x wall
  cut, memo 7.47M -> 1.19M entries vs gen-0 on the identical sealed task (fresh memo,
  node_cap 39,357,621 / wall_cap 4621s, same substrate; run completed 07:5x BEFORE the
  box's day-sleep — wall figure contains no suspend gap; internal pacing coherent at
  ~170us/node = the bound costs ~1.45x per node and prunes 6.5x, economics consistent).
  Candidate: `candidates/gen1/cand_1786683341_0.py` (claude -p proposer, sample 1) — novel
  content vs lb3: per-head aggregation over union-of-rests, PARTIAL-universe inequality
  (m heads sharing exact universe u => m + A(k-1) + extras; lb3 required all-k heads),
  top-3 pair-SCS with extras added and an early-skip, admissible 2k-1 fallback beyond the
  proven table. Stage A CLEAN (exhaustive n<=5), Stage B/C passed, verdict agrees with
  gen-0's independent PROVED-NO (cross-validated result). **HONEST RESIDUAL, named at
  bank time: admissibility is exhaustively verified at n<=5 ONLY; n=6 soundness rests on
  construction + agreement-with-gen-0. Theorem-grade citation for the n=6 rung stays with
  the signed gen-0/H4 lineage; this bank is the evolution lane's champion designation, per
  the sealed bank rule's own terms.** Proposer round note: 3 candidates SCREEN-PASS from
  4+3 samples; 2 samples lost to the documented claude.exe spawn-handle race — proposer
  plumbing patched mid-round (pipes -> file redirect + per-sample timeout tolerance, openly
  labeled in evolve_bounds.py; sealed stages/caps/bank rules untouched; battery re-green
  21.1s post-patch). Candidates 2-3 Stage D pending, same caps.
- 2026-08-14 **GEN-1 ROUND CLOSED — 3/3 candidates BANK.** cand_2 (1786684411_0): PROVED-NO
  7,108,021 nodes / 1272.6s = 0.275x wall_0. cand_3 (1786685512_2): PROVED-NO 9,784,305
  nodes / 1657.9s = 0.359x wall_0 (run spanned two box-sleeps; wall is process-internal,
  suspend-free). Champion stands: cand_1 at 0.224x. 100% bank rate against the 0.67x bar —
  every evolved candidate at least halved the requirement. All three verdicts agree with
  gen-0's independent PROVED-NO. Ladder framing corrected same day (see ATTACK-MAP-a7.md):
  a(7..9) are literature-known (39, 52, 66 — OEIS; n^2-2n+4 dies at n=9), open cell =
  a(10); n=7/8/9 serve as known-truth calibration rungs per the campaign's own
  calibration-hunt pattern. Next: gen-2 per the sealed pre-reg (hint A/B, caps at champion).
- 2026-08-14 **GEN-2 PRE-REG (sealed BEFORE any gen-2 sampling; operator-confirmed in-chat,
  session f1735d07).**
  (1) CAPS RE-SEALED to the gen-1 champion: candidate node_cap = 6,067,024, wall_cap =
  1036s in-process; **bank bar = wall <= 694.7s (0.67 x 1036.8)** — verdict-under-cap ==
  beats the champion by construction. Substrate, load-comparability rule, and
  battery-green-on-the-measuring-box precondition carry unchanged from the 08-14 desktop
  re-seal. Champion source in the proposer prompt becomes cand_1786683341_0 (it replaces
  lb3 as the "beat it" target); the failures section may cite gen-1's lost/dominated
  samples.
  (2) HINT A/B EXPERIMENT (the operator's cross-domain question, made measurable): two
  arms, identical in everything but the prompt. ARM U = unhinted (current prompt), 4
  samples. ARM H = hinted, 4 samples — prompt gains a short hint block naming exactly two
  cross-domain bound FAMILIES, no formulas: (a) amortized-progress accounting (each
  appended symbol charged against the pending work it can serve — the superpermutation
  lower-bound import), (b) relaxation-based bounds (solve a cheap relaxed problem at the
  node; its optimum is admissible — the TSP/Held-Karp import). PRE-REGISTERED MEASURES:
  per-arm SCREEN-PASS rate; per-arm best Stage D wall; whether any H candidate genuinely
  INSTANTIATES a hinted family (code-read, labeled BEFORE its Stage D runs). DECISION
  RULE: hints earn a standing place in gen-3+ iff ARM H's best wall < ARM U's best wall
  AND >=1 H candidate genuinely instantiates a hinted family (kills the
  generic-improvement confound). FALSIFIER: U >= H means hints are decoration — dropped.
  (3) STAGED, NAMED, NOT RUN (await separate operator go): dominance/subsumption-pruning
  import from the sorting-network n=13 campaign (search-side axis, orthogonal to bound
  evolution — needs its own design + birth battery); BREACH pass on the n=7 wall.
  (4) DISCOURSE-BLINDING REFINEMENT (2026-08-14 same day, linux-claude 9ec46f00, adopted
  openly BEFORE any gen-2 sampling): in addition to no-candidate-formulas, NO PREDICTIONS
  about WHICH HINT FAMILY WILL WIN on any channel a hint-block author might read — a bet
  carries mathematical steering without containing a formula. Binds all fleet discussion of
  this experiment until both arms' Stage D verdicts are banked.
  (5) MEMORY AMENDMENT (2026-08-14, pre-sampling, openly labeled; applies to BOTH arms
  identically so A/B validity is preserved): the base proposer prompt gains (a) CHAMPION
  SELECTION FROM THE LEDGER — generate() presents the current banked champion's source
  (gen-2: cand_1786683341_0 per rule (1)) instead of hardcoded lb3, with lb3 fallback when
  no candidate has banked; (b) a SCORED-ATTEMPTS section — recent fitness rows (label,
  outcome, nodes, wall) so the proposer sees measured selection pressure, not just the
  champion; (c) the existing counterexample-failures section unchanged (it was plumbed and
  verified empty-for-the-right-reason: gen-1 had zero screen deaths). Battery checks for all
  three ship in the same commit per NULL-CONTROL-AT-BIRTH.
- 2026-08-14 **GEN-2 SAMPLING DONE + INSTANTIATION LABELS (recorded BEFORE any gen-2 Stage D
  run, per prereg (2); driver switched fable-5 -> opus-5 at sampling end, G21 split noted).**
  ARM U: 4 samples -> 3 landed, **3/3 SCREEN-PASS** (1 lost to the claude spawn-race, skipped
  cleanly). ARM H: 4 samples -> 2 landed, **2/2 SCREEN-PASS** (1 race-timeout, 1 reply with no
  code block). Both arms screened against the GEN-1 CHAMPION's dominance bar, so every passer
  is strictly tighter than cand_1 somewhere.
  **INSTANTIATION LABELS (code-read, blind to fitness — no H candidate measured at label time):**
  - cand_H_1786734235_0: **PARTIAL-YES, family (a) amortized-progress.** Adds per-head inner
    cost as symbols FORCED STRICTLY AFTER a first occurrence, with overlap-connected components
    ADDING where the champion took a max, plus an adversarial latest-first-occurrence charge and
    a disjoint-packing term. Charging appended symbols against the obligations they can serve =
    family (a) in substance; the word "amortized" never appears.
  - cand_H_1786734840_1: **PARTIAL-YES, family (a).** Adds a "sweep term" generalizing the
    universe term to heads with UNEQUAL universes via the same latest-first-occurrence /
    adversarial-owner argument. Also a popcount micro-opt (cost axis, not a family).
  - **NEITHER instantiates family (b) relaxation-based bounds** — no relaxed subproblem is
    solved to optimality in either candidate.
  Pre-registered "genuinely instantiates a hinted family" condition: **MET by both H candidates
  for family (a), NOT met for (b)**. The wall comparison that decides the A/B is the Stage D
  queue, unrun at label time.
- 2026-08-15 **GEN-2 CLOSED — THE LOOP COMPOUNDS, AND THE HINTS FAIL THEIR OWN BAR.**
  Adjudicated against the sealed rules (prereg (1)-(5)); raw rows in evolution-ledger.jsonl,
  this entry is the adjudication, not the substrate.
  **ARM U (unhinted, 4 sampled / 3 landed / 3 SCREEN-PASS):**
    cand_U_1786732349_0  PROVED-NO  3,857,090 nodes /  580.9s  = 0.56x wall_0  **BANKS**
    cand_U_1786732698_1  PROVED-NO  5,308,349 nodes /  804.6s  = 0.78x        no bank
    cand_U_1786733692_3  PROVED-NO  4,733,078 nodes / 1018.6s  = 0.98x        no bank
  **ARM H (hinted, 4 sampled / 2 landed / 2 SCREEN-PASS):**
    cand_H_1786734235_0  CAP-EXCEEDED at 1037.9s (3,776,512 nodes at the cut)
    cand_H_1786734840_1  CAP-EXCEEDED at 1037.9s (5,181,440 nodes at the cut)
  **VERDICT 1 — COMPOUNDING: YES.** New champion cand_U_1786732349_0 at 580.9s beats the
  gen-1 champion's 1036.8s by 1.79x and clears the 694.7s bank bar with room. Cumulative vs
  the hand-built gen-0 baseline: **8.0x wall (4621.4 -> 580.9s), 10.2x nodes (39.36M ->
  3.86M).** Two generations, each banking against caps sealed before its own data existed.
  Note the SPREAD, which is the bar doing its job: all three U candidates beat the champion,
  exactly ONE cleared the 1.5x bank requirement.
  **VERDICT 2 — HINT A/B: FALSIFIER FIRES, hints are DECORATION and are DROPPED from gen-3.**
  Decision rule (prereg (2)): hints earn a standing place iff ARM H's best wall < ARM U's best
  wall AND >=1 H candidate genuinely instantiates a hinted family. Instantiation condition was
  MET (both H candidates instantiate family (a) amortized-progress; neither touched family (b)
  relaxation — labels sealed pre-measurement above). Wall condition FAILED: H produced no
  completed run at all. So the conjunction fails and the pre-registered falsifier fires as
  written. No re-tuning, no "H was close": the rule was fixed before the data.
  **THE INFORMATIVE FAILURE, worth carrying to gen-3:** H's first candidate cut MORE nodes than
  the U winner (3,776,512 < 3,857,090) and still blew the wall cap. The hinted family produced
  the STRONGEST BOUND of the round and could not pay for it per node — which is precisely the
  economics the wall-clock fitness axis exists to catch (R2's lesson: "10x stronger but 100x
  slower loses"). Recorded as a cost problem, NOT a dead idea: an amortized-progress bound
  implemented more cheaply is a live gen-3 candidate shape, and the two H sources are kept.
  **Substrate/method notes:** both arms screened against the GEN-1 CHAMPION's dominance bar, so
  every passer was strictly tighter than cand_1 somewhere. 3 of 8 samples lost (2 spawn-race
  timeouts, 1 reply with no code block) — the patched proposer skipped each without aborting
  its round, as designed. Driver: fable-5 for sampling and labels, opus-5 from the operator's
  mid-round /model switch onward (G21: attribution split, no blended row).
- 2026-09-02 05:27Z **SECOND-BOX REPRODUCTION of the gen-2 champion — NODE-EXACT and MEMO-EXACT.**
  Session linux-claude-5534b575 (Claude Code web container, Linux, 4 cores, Python 3.11.15),
  checkout = Researches origin/main 4bc5c47 in a detached worktree; nothing on the sealed desktop
  touched. Precondition discharged first: `test_evolve_bounds.py` ALL GREEN on this box (12.9s).
  Ladder n=3/4/5 with gen-0 reproduces node-exact (no-6 10 / no-11 22 / no-18 1,868).
  **Champion `cand_U_1786732349_0` at (6,27): PROVED-NO, 3,857,090 nodes, memo 765,530, 510.6s**
  (desktop banked 2026-08-15: 3,857,090 / 765,530 / 580.9s). Nodes and memo IDENTICAL; wall is the
  substrate axis as the lane's own note predicted — this box runs 7,554 nodes/s = 1.14x the desktop.
  Raw harness output, verbatim: `{"outcome":"PROVED-NO","wall_seconds":511.3,"node_cap":6067024,
  "wall_cap":5400,"nodes":3857090,"memo_entries":765530}`.
  **NOT A BANK, and not claimed as one:** substrate is not the sealed desktop and the run was
  background, not attended-foreground — both outside the 08-14 re-seal. What it IS: the first
  independent reproduction of the champion's VERDICT (deterministic state space, box-independent),
  which the lane had never had, and a wall datum for this box only.
  **New data — the champion below n=6 (never measured before):** n=4 L=11 = 20 nodes (gen-0 22),
  n=5 L=18 = 646 nodes (gen-0 1,868). The cut vs gen-0 WIDENS with n: 1.1x / 2.9x / 10.2x.
  **HONEST n=7 PROJECTION (nodes(6) x growth, the charter's own method):** champion's own 5->6
  growth = 5,971x, gen-0's = 21,069x, so n=7 no-38 projects **2.3e10 .. 8.1e10 nodes** — 35 to 125
  days single-core at this box's rate, and per-node cost at n=7 is unmeasured, so those are FLOORS.
  The charter's fallbacks stand as the only two routes: (a) another ~10x from gen-3+ (the live shape
  the gen-2 adjudication named: amortized-progress implemented cheaply; hints stay DROPPED), or
  (b) a distribution design, which the DFS+memo shape does not give for free. No scaling claim
  beyond this line; the n=7 rung remains gated on the evolution lane exactly as written.
  Ledger: the harness appended 3 fitness rows in the worktree; they are NOT committed (the sealed
  ledger records sealed-substrate runs only) — this entry carries the numbers instead.

- 2026-09-02 17:06Z SECOND-BOX CANDIDATE (linux-claude-5534b575, NOT banked, not on the sealed substrate): PCLA pilot v5
  (R14) produced blind, in three authors across two arms, two bound terms the gen-2 champion lacks (size-2 adder; mutual-head).
  Translated to the lane contract as `candidates/pilot/P2_champion_plus_pilot.py` (= champion 4abfe3a64b392782 + the two
  terms in the per-head block only; sha 3a8fd22752f468d4). Lane cascade in a scratch copy @ 4bc5c47 on this box: Stage A
  CLEAN n=3/4/5 (worst slack 0); Stage C vs lb3 279 higher / 0 lower on the 300 bench states; Stage D prove_no(6,27)
  PROVED-NO **394.9 s / 2,602,809 nodes** vs the champion **544.9 s / 3,857,090** run back-to-back (0.725 wall, -32.5%
  nodes; champion node count reproduced this morning's exactly). P1 (pilot bound alone) caps out; P3 screens at 25x lb3
  cost, not run at D. Hand-off: `candidates/pilot/LANE-HANDOFF.md`; PCLA R15. Lane owner: run on the laptop under the
  PRE-REG; if it holds, gen-3 seed.

- 2026-09-04 **PILOT-VERIFICATION PRE-REG for P2 (sealed BEFORE any Stage D measurement on
  this box; scoped to P2 ALONE — this is NOT a gen-3 pre-reg)** — session bc4d5e5e (windows
  desktop, D: box); courier row filed 2026-09-02 by linux-claude-5534b575; operator approval in-chat.
  SEAL TIME 2026-09-04 01:09:38Z (clock read at write, not felt).
  (0) SCOPE, and why this is not gen-3. P2 (`candidates/pilot/P2_champion_plus_pilot.py`,
  sha256 3a8fd22752f468d4…) is not a proposer sample: it is a hand-translation of the gen-2
  champion cand_U_1786732349_0 with two terms imported from the Generation-Engine pilot
  (size-2 adder, mutual-head; LANE-HANDOFF.md). No gen-3 proposer round has been sampled.
  Sealing gen-3's caps on one hand-made cross-check would bundle two decisions; gen-3 gets its
  own entry when its round opens. This entry judges P2 and nothing else.
  (1) BAR — the standing formula, unchanged: caps at the gen-2 champion (node_cap = 3,857,090,
  wall_cap = 580.9s in-process), **bank bar = wall <= 389.2s (0.67 x 580.9)**. Not chosen for
  this candidate: 0.67x has been the rule since the 07-21 seal and was applied verbatim in
  gen-1 and gen-2.
  (2) DISCLOSED PRIOR, and what it does NOT license. A second-box measurement of P2 exists and
  is KNOWN to this session before the run: 394.9s / 2,602,809 nodes on linux-claude-5534b575's
  box, back-to-back against the champion at 544.9s / 3,857,090 there (results-registry R15,
  explicitly NOT banked). It sits 1.5% ABOVE this entry's bar. It is disclosed because
  concealing it would not make it unknown. It is NOT a reading on the sealed axis: wall is
  substrate-dependent by this campaign's own 08-14 finding (nodes reproduce across boxes to
  ~0.01%, wall does not), so 394.9s predicts nothing about this box's number.
  (3) NO-RETRY — the clause this entry exists for. ONE attended foreground run. The FIRST
  completed run is the result: no best-of-N, no warm-cache re-run, no discarding a number after
  reading it. The ONLY void condition is a rule-3 load-boundary crossing, and it must be
  DECLARED BEFORE THE NUMBER IS READ with the run discarded unread — the 08-14 precedent (a
  calibration attempt begun under present-load, voided at the boundary, discarded unread). A
  run void-declared after its number is visible is a protocol violation and the verdict is
  forfeit.
  (4) SUBSTRATE / LOAD / PRECONDITION carry verbatim from the 08-14 desktop re-seal: this D:
  box, attended foreground, single logical core, no MSYS timeout wrapper, fresh memo,
  per-candidate scratch cwd. Load condition = ABSENT-THROUGHOUT (no PID-56000-class sustained
  ~1-core background job). **Ambient constants permitted and disclosed, same class and scale as
  the 08-14 disclosure ("two bus wake-monitors, spool server"):** `spool_server.py`, two
  `pcla_console.py`, and a concurrent session's `bus_wake_monitor.py --identity pcla-work` +
  read-only `omni_bus_tail.py`. That session offered to stop them and was asked NOT to —
  stopping them moves AWAY from the calibrated ambient, not toward it.
  **DISK STATE, disclosed as a named condition (NEW — this axis was unnamed in the 07-21 and
  08-14 seals and is named here because it was measured, not because it fired):** D: 37.2 GiB
  free (2.0%), C: 13.8 GiB (1.5%) at seal time. This matters because the memo snapshot lands
  INSIDE the timed window — the harness times `wall_started -> v3.prove_no(...) -> elapsed`
  and prove_no writes its memo pickle before returning — so every Stage D wall figure this
  campaign has banked includes one large serialized write. Measured write+fsync on D: at seal
  time: 100 MB in 1.8s, 400 MB in 7.7s (52-56 MB/s). Champion-scale memo (~40-90 MB) therefore
  contributes under 2s to a ~389s window: real, an order of magnitude below the margin, NOT a
  blocker. If P2 lands within noise of the bar, disk state is named FIRST SUSPECT alongside the
  08-14 transients.
  (5) STAGES A-C carry verbatim: Stage A exhaustive admissibility n<=5 must be CLEAN; Stage B
  median < 2ms; Stage C not dominated on the fixed 300 states (seed 62714). A Stage A violation
  kills P2 regardless of wall.
  (6) VERDICT SPACE, fixed now, both sides meaningful:
      Stage A CLEAN + PROVED-NO under caps + wall <= 389.2s -> **P2 BANKS** as a pilot-verified
      bound; its two terms carry as gen-3 proposer hints per the courier row.
      PROVED-NO but wall > 389.2s -> **NO BANK**, and the run still stands as the first
      sealed-substrate measurement of P2 — the cross-box reproduction datum R15 lacks.
      CAP-EXCEEDED / Stage A violation / crash -> **NO BANK**, recorded as such.
  (7) DECIDABLE-CHECK: this entry is pushed to origin/main and its commit SHA recorded BEFORE
  the Stage D process starts. FAILS IF the ledger's P2 fitness row carries a timestamp earlier
  than this entry's commit timestamp.
- 2026-09-04 **P2 PILOT-VERIFICATION RESULT (the sealed run above, executed): PROVED-NO —
  2,602,809 nodes / 550.7s. NO BANK.** Bar was 389.2s; P2 missed it by 161.5s (1.415x the bar).
  Sealed by commit faab50579e9c6db1b1a53c59544d4453e8de0fd6 (01:10:04Z); Stage D worker started
  01:12:50Z and ended 01:22:02Z, so the clause-(7) decidable-check is satisfied in the required
  direction (seal precedes measurement). Workdir
  evolution-runs/3a8fd22752f468d4-n6L27-1788484370, fresh memo, 515,006 entries.
  **SCREEN (same session, before Stage D):** Stage A CLEAN — 0 violations, worst slack 0, DP
  root truth 19 correct at n=5, 13.6s. Stage B median 57.1us vs lb3's 26.3us (bar 2ms). Stage C
  vs lb3 on the fixed 300 states (seed 62714): 279 higher / 21 equal / **0 lower** — P2 is
  nowhere dominated. Battery green on the measuring tree (19.9s, discrimination both directions).
  **DEVIATION, disclosed:** the seal wrote wall_cap = 580.9s; the harness takes an int and
  refused the float, so the cap was FLOORED to 580 following gen-2's own precedent (1036.8 ->
  1036). 0.9s stricter than sealed, i.e. the direction that can only make banking harder. The
  first invocation died in argparse before prove_no was called — no timed window opened and no
  number was produced, so clause (3)'s no-retry rule (which forbids discarding a NUMBER) was
  not engaged; both invocations are recorded here rather than one being quietly dropped.
  **The disk first-suspect clause was NOT invoked and did not need to be:** P2's memo is 515,006
  entries (~28 MB at the measured 52-56 MB/s, under 1s inside a 550.7s window) and the miss is
  161.5s. All the care about the 1.5% margin protected a decision that was never close.

  **THE FINDING, and it is worth more than the verdict: CROSS-BOX WALL *RATIOS* DO NOT TRANSFER.**

  |                      | champion (gen-2) | P2      | P2/champ | us/node champ -> P2 | penalty |
  |----------------------|------------------|---------|----------|---------------------|---------|
  | this D: box (sealed) |  580.9s          | 550.7s  | **0.948**| 150.6 -> 211.6      | x1.405  |
  | linux-claude-5534b575|  544.9s          | 394.9s  | **0.725**| 141.3 -> 151.7      | x1.074  |

  **Nodes reproduced EXACTLY: 2,602,809 on both boxes, to the unit.** So the search is
  bit-identical and the entire wall difference is execution cost, not different work.
  This campaign already knew wall was substrate-dependent (08-14: "nodes reproduce across boxes
  to ~0.01%, wall is the substrate-dependent axis"). What that entry assumed, without saying so,
  is that the substrate contributes a **scale factor** — and a scale factor CANCELS in a ratio.
  This one does not cancel: 0.725 vs 0.948. The mechanism is in the last column. P2's bound
  costs 7% more per node on linux and 40% more per node here — same bound, same nodes, a
  five-fold difference in the cost penalty. A bound that trades "more expensive per node"
  against "fewer nodes" sits on a trade-off whose optimum depends on the ratio of
  bound-evaluation cost to node-expansion cost, and THAT ratio is a property of the box.
  **Consequence, binding on the campaign's own claims:** any "improves the champion by X"
  figure must name the box it was measured on, and cannot be carried to another. In particular
  results-registry R15 ("Pilot-derived bound terms improve the a10 gen-2 champion on the
  evolution lane's own fitness axis") is currently carrying 0.725x as if it were a property of
  P2; on the sealed substrate the same candidate measures 0.948x. R15 is not refuted — the
  improvement is real in both places — but its magnitude is a fact about linux-claude-5534b575,
  and the row needs that qualifier. AMENDMENT OWED to R15; not made from here.
  The sealed-single-substrate rule is therefore doing more work than it was credited with: it
  is not merely normalizing units so numbers are comparable, it is the only thing that makes
  the candidate RANKING well-defined at all.

  **P2 is not a dead idea.** It prunes 32% fewer nodes than the champion (2.60M vs 3.86M),
  which is genuine progress on the pruning axis; it simply cannot pay for that pruning on this
  substrate. Structurally identical to gen-2's ARM H failure (strongest bound of the round, blew
  the cap — "10x stronger but 100x slower loses"), now with a cross-box twist: the economics are
  themselves substrate-dependent, so the same candidate can be a winner on one box and a
  no-bank on another with no change to its code. The two pilot terms (size-2 adder, mutual-head)
  are kept and remain a live gen-3 candidate SHAPE if implemented more cheaply — the courier
  row's "carry them as proposer hints" survives the no-bank.
  **HONEST BOUND:** n=1 run per box on two boxes. This is not a controlled study of substrate
  effects and does not measure which box is representative. What it does establish, and what
  needs no controls, is that identical node counts with a 1.074-vs-1.405 per-node penalty is
  not a scale factor — which is the only claim the paragraph above rests on.

- 2026-09-17T23:25:03Z **GEN-3 ROUND PRE-REG — SEALED (this commit is the seal).** Full entry:
  `GEN3-PREREG.md`, kept as its own file because it is longer than a rung line and is the
  handover document for whoever drives the sealed box. Drafted on the termux phone
  (`termux-claude-a2f0c934`, opus-5); the three clause-5 items were ruled by the operator BEFORE
  the seal: composition = the two pilot terms (size-2 adder, mutual-head) as **proposer input with
  NO scored arm** (gen-2's falsifier killed hints as an ARM; the courier row's "carry them as
  proposer hints" survives the P2 no-bank), **k = 8** fixed with no optional stopping and
  mechanical losses reported rather than resampled, and the sealed `D:` desktop confirmed
  available for attended foreground runs.
  **Caps and bar unchanged from the standing formula:** node_cap 3,857,090, wall_cap 580.9s
  (floored to 580 by the harness int, gen-2 precedent, 0.9s stricter), **bank bar wall ≤ 389.2s**
  (0.67× since the 07-21 seal). Not chosen for this round.
  **THE ONE ADDITION, and the reason this entry is not a copy of gen-2's:** `µs/node` =
  wall×1e6/nodes is now a REQUIRED reported quantity for every Stage D candidate and for the
  champion re-run back-to-back. It does **not** change the bank bar, so it can only add information
  and can never rescue a candidate. It exists because the last two rounds were both decided by it
  and neither recorded it: gen-2's ARM H cut MORE nodes than the winner and blew the wall cap, and
  P2 cut 32.5% of nodes and missed the bar by 161.5s. Pre-registered reading, fixed before data:
  if every node-reducing candidate raises µs/node enough to miss the bar, that is evidence the
  cheap-amortised-progress shape is **not reachable by this proposer** — a finding to report, NOT a
  reason to sample more and look again.
  **Round falsifier, both directions.** NULL = no candidate banks; gen-3 closes with no champion and
  the n=7 rung stays gated exactly as the charter says. REFUTED = if the banking candidate's µs/node
  is HIGHER than the champion's, the "cost-per-node is the binding constraint" frame this entry
  rests on is wrong and the entry says so rather than keeping the frame that produced it.
  **No number from any other box is a gen-3 reading** — P2 established that wall RATIOS do not
  transfer (×1.074 vs ×1.405 per-node penalty on identical node counts), so single-substrate is not
  unit normalisation, it is the only thing making candidate ranking well-defined.
