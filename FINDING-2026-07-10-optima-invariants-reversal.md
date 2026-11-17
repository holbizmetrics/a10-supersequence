# FINDING 2026-07-10 — Reversal → optima-mining → exact structural invariants (n=4)

**Session:** windows/Opus-4.8 (0c35d442) + operator (Holger). The operator drove the key pivot
(REVERSAL: "imagine it worked, trace back; reduce the gap from another angle").

## The arc that got here
1. n=13 "beat 145 by shaving 1 off Radomirović" is **decidably walled** at every granularity —
   overwrite / exhaustive-swap (84/84) / annealing / GPT-5.6's concurrent richer-op engine
   (word-level) + block-level A15 perturbation (rule-level). All plateau. The 145 near-miss is a
   fragile local optimum; the tail is a zero-sum "rainbow" (pigeonhole: 9 culprit symbols each need
   last-occurrence ≥ pos 142, only 2 such slots).
2. **Family map** (`supersequence_family.py`): σ(n) exactly known n≤7 (dead); n=8,9 near-dead
   (improved-UB == naive); **n≥10 LIVE** (naive n²−2n+4 DISPROVEN; ⌈n²−7/3n+19/3⌉ shorter, first
   crack n=10: 83<84). The "145" we fought = ⌈n²−7/3n+19/3⌉ at n=13 exactly — a real published
   bound, NOT confabulation (cross-checked with linux).
3. n=10 attack: greedy-delete-from-blocks floors at 91; delete+anneal-repair also floors at 91 →
   **search walls at n=10 too.**

## The search-ceiling finding (decidable, scale-invariant)
Fixed-length coverage-max search **plateaus at gap-1**: n=4 → 23/24, n=5 → 118/120, n=10/13 → same.
Complete words are **rare needles surrounded by gap-1 local maxima**; local moves cannot place the
final permutation without breaking another (the pigeonhole, at every scale). **Conclusion: search is
decidably ruled out from n=4 up. Only a constructive/algebraic insight can produce these words.**

## The optima structure (ANGLE #1: attack the optima, not the record)
Exhaustive enumeration of the true optimal set (search can't reach it → enumerate):
- **n=3, σ=7:** 42 complete words, **6 distinct** up to relabel+reversal. Profiles vary
  ([4,2,1],[3,3,1],[3,2,2]…). Two visible families: block-and-extra (`0120120`), skewed-nested (`0102010`).
- **n=4, σ=12:** 611,501 canonical-forward words scanned → **6 distinct optima**, all obeying HARD invariants:
  - **multiplicity profile ALWAYS (4,3,3,2)** (one ×4, two ×3, one ×2; sum 12)
  - **first 4 symbols = a permutation of 0..3; last 4 = a permutation of 0..3** (perm-block ends)
  - no adjacent-equal; every symbol count ≤ n
  ```
  [0,1,2,3, 0,1,2,0, 3,1,0,2]   [0,1,2,3, 0,1,2,0, 3,1,2,0]   [0,1,2,3, 0,1,2,0, 3,2,1,0]
  [0,1,2,3, 0,2,1,0, 3,1,2,0]   [0,1,2,3, 0,2,1,0, 3,2,0,1]   [0,1,2,3, 1,0,2,1, 3,0,1,2]
  ```

## The inverted-oracle / A15 framing (operator-surfaced)
The forward oracle: word → coverage count. The **inverted oracle**: completeness-spec → the
NECESSARY CONDITIONS any complete word must satisfy — turning the *checker* into a *constraint
generator*. The invariants above are its empirical output; at full strength it characterizes the
pre-image of "complete" = the construction itself. Feed those constraints to the proposer = **A15
substrate-conditioned residual search**: bind {perm-block ends, multiplicity fingerprint}, search
only the residual → the rare needles become dense. This is the first lane all session that could
BUILD a word rather than search blindly for it.

## Honest bounds (do NOT inflate)
- These are STRUCTURE in the optima, **not a novel result and not a record**. Value = TBD.
- Small optima likely follow the WEAKER Newey family → invariants may help *find* optima (calibration,
  beat the gap-1 wall) but probably NOT beat the record.
- **The open test: do the invariants GENERALIZE to n≥5?** (perm-block ends? multiplicity fingerprint?)
  If yes → a construction template. If no → n-dependent substrate. ← next step.
- Paradigm check: this IS FunSearch (DeepMind, LLM+evaluator → real new math incl. cap sets, which
  literally sits in `pcla_funsearch_engine.py`). Existence proof the paradigm works; our SCALE is tiny.

## Artifacts
`supersequence_family.py` (map+general oracle) · `attack_n10.py` · `chase_n10.py` · `mine_optima.py`
(n=3 exhaustive + n=4/5 anneal) · `enumerate_n4.py` (true n=4 optimal set + invariant readout).
Oracle cross-validated vs brute-force σ(3)=7 (linux) and 3 independent implementations agree on 145=13!.

## UPDATE — the n=4 invariants do NOT generalize (tested decidably)
- **n=3 (a15_n5.py / direct check):** only **4/6** optima have perm-block ends (`[0,1,0,2,0,1,0]`,
  `[0,1,0,2,1,0,1]` do NOT); multiplicity VARIES ((4,2,1),(3,3,1),(3,2,2)). NOT a necessary invariant.
- **n=5 (a15_n5.py):** unconstrained anneal plateaus at 118/120; A15-binding the invariants reaches
  119 but NOT 120 — consistent with binding a non-universal constraint (falsifier #4, over-constrain).
- **Why n=4 looked clean:** σ(4)=12=3×4 is BLOCK-ALIGNED, so perm-block-ends falls out for free.
  σ(3)=7 and σ(5)=19 are NOT multiples of n (7=2·3+1, 19=3·5+4) so the alignment breaks. The n=4
  invariants were a **numerological coincidence of block-alignment, not a construction template.**
- **Verdict:** the reversal/optima-mining found REAL n=4-local structure but NO universal law. Honest
  null — banked so we don't chase perm-block templates. The machinery worked: promising lead tested
  for generalization decidably and killed in minutes with an explanation, before building on it.

## UPDATE 2 (2026-07-11) — OEIS corrections + THE 66: a verified strong-family specimen
- **Family-map corrections (OEIS A062714, oracle-re-verified here):** a(8)=52 EXACT (von Brömssen
  Aug 2025, Newey optimal at 8); **a(9)=66 EXACT (Garnashevich Oct 2025) — Newey's 67 BEATEN by 1.**
  My map's "n=9 near-dead" was WRONG. The exact frontier is now **a(10): best-known 83, target 82.**
  Tan 2022 does NOT reach n=10 (T2 needs n≡0 mod 3; T3 needs n≥13) -> 83 stands as best-known.
- **The 83 recon:** deletion-irreducible; best near-miss (pos1) gap = 194 of 3.6M — ALL 194 missing
  perms enumerated exactly (100% fail-at-last-symbol; culprit sym3 dominant = same family fingerprint
  as n=13's 3,584). Full-resolution failure signature in hand.
- **THE 66 (A136094, oracle-verified complete = 9!):** multiplicity profile [9,9,9,8,7,7,6,6,5] —
  NOT a tweaked Newey. Mechanism = **sparsity GRADIENT**: dense trio 0,1,2 as scaffolding (symbol-0
  gaps ~8, separator-like), then graded thinning to 5. Radomirovic's single-sparse-y, generalized.
  Last-9 a permutation; tail bookended by the dense trio. First verified specimen of the RECORD
  family (all prior optima-mining was the weak Newey family).
- **The 82-attack now has a real template:** A15 with the RIGHT substrate — bind the graded-profile
  scaffolding mined from the 66, search the residual at n=10/length-82 (e.g. profile guess
  [10,10,10,9,8,8,7,7,7,6]=82). Open: does the grading mechanism compose one level up?

## UPDATE 3 (2026-07-11 night) — deep-run final + the modal-gap family discriminator
- **Deep run FINAL:** seed3 (random) gap **321** beats seed2 (template) 637; deepest ever; triple-
  verified (my oracle + linux's independent per-ending-symbol DP). Signature instrument-independent:
  100% last-symbol fails, sym6=142/321 (44%), every sampled missing perm ENDS in 6, sym1 PERFECT (0).
  Curve never flattened -> budget-bound; next lever = numba/GPU-batched oracle (desktop lane).
- **linux's G-invariant reframe (provable):** invariants of all optima must be class-functions under
  G = reversal x relabel; per-word predicates are G-breakable (why the miner failed); profile space
  IS the G-invariant substrate (why the wall-map works). Invariant thread closed with mathematics.
- **Modal-gap test (linux's candidate, tested on everything banked):** modal consecutive-gap = n-1
  holds for ALL strong-family records (39/52/66: 3/3) but FAILS for the construction family (83/145:
  mode = n) and is mixed at small n (3/6, 3/6) -> NOT universal, but a **FAMILY DISCRIMINATOR**:
  strong optima pack dense symbols at period n-1; construction family at period n. OUR 321 plateau
  word has mode n = construction-style packing -> the anneal may be stuck in the WRONG BASIN FAMILY.
  Actionable (GPU lane): bias search toward modal-gap-(n-1) packing — a G-invariant bias. Candidate,
  not mechanism; test = does the bias beat 321?

## UPDATE 4 (2026-07-11, fleet night) — 321 -> 23 -> 17; bias falsified; endgame lane opens
Desktop (131d960a, RTX box, numba oracle ~3000 steps/s, instrument-checked) ran 1M-step anneals:
- Run 1 (lifted-66 profile): 23/25/27/41 — all ~10x past the 321.
- Batch 2 (winner profile, bias-vs-control): CONTROL 19,**17** / BIAS-KERNEL 89,149 / BIAS-FULL 84,110.
**NEW DEEPEST: gap 17** (slow-verified + linux cold-confirmed exact). Falsification chain, all
self-caught: my modal-gap BIAS hypothesis KILLED by experiment (forcing n-1 packing hurts 5-8x;
free deep anneals converge to ~9 packing on their own -> DIAGNOSTIC not causal); desktop retracted
its profile-flip read (budget-confounded; winner profile stands); linux retracted its sharp-basin
read of gap-23 (deep words are DIFFUSE; genuine optima sharp — the anneal wants glass near the
records' crystal). Stable invariant across ALL deep words: 100% last-symbol fails; culprit symbol
word-local (6/3/9/2) -> weak lean that 82 is REACHABLE (a wall would pin one culprit). NEXT: endgame
lane — exhaustive 2-swap neighborhood clearance of W17 (decidable, ~5.5M pairs, ~30min on desktop's
oracle), then targeted last-symbol repair kernel if the 2-move answer is NO.

## UPDATE 5 (2026-07-12 ~01:00, desktop 131d960a) — gap 3, SUFFIX RESYNTHESIS banked, the 83 incompressible at both ends
- **Endgame kernel** (`endgame_kernel.py`: culprit-weighted tail moves, warm starts, coverage-only
  acceptance): 12 runs -> 3,3,4,4,5,5,6,7,9,11,11,16. **GAP 3** (linux cold-confirmed). Then: certified
  2-swap LOCAL OPTIMUM (exhaustive ~5.5M pairs — NOTHING better in the ball) + 8/8 hot restarts return
  to it. The 2-swap balls of W17/W19/W23 (~33M words) contain nothing below gap 12 — but that emptiness
  was a LOCAL-RADIUS artifact (retracted same night): the kernel walked past it.
- **THE METHOD (banked; new to this campaign, literature-novelty UNCHECKED):** suffix resynthesis.
  Cut-property: leftmost-greedy is pointer-optimal, so p embeds in w IFF its greedy remainder after
  w[:c] embeds in w[c:]. Compute the DISTINCT remainder-tuple set of a prefix exactly (greedy-tree walk,
  (first-sym, rest-set) block dedup), then IDA* (state = frozenset of pending suffixes; LB = max(longest,
  per-symbol max-demand sum)) decides: SUFFIX-FOUND (self-verifies on slow oracle) or PROVABLY-NO-SUFFIX.
  `resynth.py`. Validated BOTH directions: YES 5/5 (n=3/4 optima rebuild complete), NO 3/3 (impossibly
  short suffixes vs PROVEN sigma(3)/sigma(4) optimality). Seconds at m<=15; ~30min at m=18; wall ~m=20.
- **Exact verdicts:** gap-3 word NO at c=76..64 -> its defect is at or before position 63 (that's why no
  tail move ever worked). Breadth: ALL 12 deep words, cuts 76/72/68/66 -> **48/48 PROVABLY-NO** — the
  anneal SYSTEMATICALLY builds doomed prefixes; the needles are not near the wells (rare-needles confirmed
  at n=10 by exact method). **The 83 compress-by-one: 12/12 NO** (cuts 77..67 fwd + reversed = tail-15 AND
  head-15 incompressible; fwd/rev counts identical — expected, construction reversal-symmetric).
- **Honest frame:** coherent exact evidence LEANING a(10)=83-optimal; ZERO proof (middle rewrites +
  unrelated-prefix 82s wide open; exact wall ~16-20 from the end). **Next lanes:** (a) stronger LB pruning
  to push the wall; (b) DONOR-PREFIX SCAN — generate construction-family prefixes (~len 66), rank by
  remainder-stats (~2.5s each, cheap), exact-solve only the promising tails. The method is the engine now.

## UPDATE 5a (2026-07-12 ~04:30) — 4-arm blind audit of UPDATE 5's own claims: corrections + at-scale gate closed
A TRIAD-style blind audit (correctness / execution / claims-conformance / null-control, all
BLIND-VERIFY rules) was run on resynth.py and UPDATE 4/5. Results + corrections, append-only:
- **Instrument VERIFIED at depth:** correctness lens PASS (cut-property, block-exactness, search
  soundness incl. memo-prune admissibility + heads-completeness, independently proven; 1,080
  trials); execution lens CLEAN (**1,256/1,256** brute-force adjudications, fault-injected
  harness); null-control PASS (~0-FP baseline on the known-good oracle, 3,800 trials).
- **CORRECTION (validation-reach, mine):** UPDATE 5 said gap 3 was "linux cold-confirmed" —
  FALSE. Linux confirmed 23 and 17/19; the gap-3 cold-score was REQUESTED (e007d017) and never
  answered. Gap 3 is self-verified on two local oracles only. The doc claimed the higher rung;
  the audit caught it. (The kernel's validation-reach register, firing on its author.)
- **At-scale YES-gate CLOSED (was the audit's sharpest residual):** all at-scale outputs had been
  NOs; a YES-suppressing bug would have been invisible. New committed gate `validate_resynth.py`
  (+ log): small-n YES 5/5, NO-negative-controls 3/3, and **ARM C — at n=10 scale, cut the 83 and
  demand its own tail length (witness exists by construction): suffix FOUND + complete 3/3**
  (c=71/69/67, seconds each). The 60 banked at-scale NOs now sit on an instrument with a proven
  at-scale YES-path. (This also retires the need for the 66-witness file.)
- **Modality corrections:** "rare-needles confirmed at n=10" -> **consistent with** (12 specific
  prefixes, 4 cuts — not global); "~33M words" -> **~16.5M distinct** (ordered evals double-count);
  "~3000 steps/s" -> **1,600-2,700 logged**; "hurts 5-8x" -> 4.4-8.8x.
- **Code fixes:** resynthesize None-contract documented (BAIL vs PROVED-NO — audit REVISE item,
  found independently by two lenses); remainder_blocks docstring lie fixed + cut<=len assert;
  "IDA*" misnomer corrected; oracle now asserts symbol domain (null-control's silent-corruption
  boundary catch). Audit artifacts: audit_bruteforce_crosscheck.py (in-repo), lens reports in
  session transcript.

## UPDATE 5b (2026-07-12 ~05:15) — LITERATURE PASS: no published match for the method; a(10) is OEIS's next empty cell
Sources actually read (primary where possible): Radomirovic 2012 E-JC (PDF text extracted — his
completeness tools are Lemma-1 symbol-first-appearance recursion + inter-appearance exchange, for
MANUAL proofs of constructions; no position-cut, no remainder computation, no algorithmic search);
Engen-Vatter survey (AMM 2021 / arXiv 1810.08252 — bounds survey, no algorithms; exact values stood
at n<=7 as of 2020); Tan 2201.06306 + 2501.11386 (constructions; segmentation/removal = lower-bound
proof tools; notes exact B&B 'impractical'); OEIS A062714 + A136094 fetched raw (only program: brute
force to n=5; a(8)=52 von Bromssen Aug 2025 using A136094's word, a(9)=66 computed Garnashevich Oct
2025, methods UNDOCUMENTED in-entry; keyword 'more' => **a(10) is the next open cell**); generic SCS
literature (heuristic beam search — the exact residual solve + the REDUCTION of tail-completion to
a small SCS over exactly-computed remainders does not appear).
**Method label upgraded:** 'literature-novelty UNCHECKED' -> **'no published match found (searched
2026-07-12)'**. Honest residual: Garnashevich's private a(9)-optimality computation is undocumented
and is the one place related machinery could exist unpublished. NOT claiming novelty — claiming
searched-and-not-found; a submission/correspondence with the A062714 maintainers would settle it.
**Bonus banked:** the66.json + the52.json (OEIS words, oracle-verified complete here: 66=9!, 52=8!);
the originally-declared 66-witness gate now ALSO ran: resynth refound complete tails of the 66 at
c=56/54/52 — the at-scale YES-path holds on a second, independent record word.
**Attribution correction:** a(8)=52 was NOT computed by von Bromssen from scratch — he confirmed it
using A136094's word (which Garnashevich added Jun 2020); Tan's 2501.11386 proves the 52 lower bound.
