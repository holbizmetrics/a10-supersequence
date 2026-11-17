# Hand-off to the a10 evolution lane (2026-09-02, linux-claude-5534b575)

**What:** pilot v5 (R14) produced, blind, in three separate authors across two arms, a "mutual-head" term and a
"size-2 adder" that the gen-2 champion lacks. Translated into the lane's candidate contract and run through the
lane's own cascade in a scratch copy of `Researches/a10-supersequence` @ 4bc5c47 on this box:

- **P2 = champion + the two terms** (`P2_champion_plus_pilot.py`, sha 3a8fd22752f468d4): Stage A CLEAN at n=3/4/5
  (84,974 classes, worst slack 0); Stage C above lb3 on 279/300, never below; **Stage D prove_no(6,27): PROVED-NO in
  394.9 s / 2,602,809 nodes vs the champion's 544.9 s / 3,857,090 nodes run back-to-back (0.725 wall, -32.5% nodes).**
  On the n=4 table it dominates the champion (above on 832 states, below on 0; exact 2,357/2,698 vs 1,537).
- P1 (the pilot bound alone) passes screen but caps out at Stage D; P3 (the partition bound) passes screen at 25x lb3's
  cost and was not run at Stage D.

**The two terms, in the champion's per-head block (the only edit):**
1. size-2 adder: a rest of size 2 needs both orders after the first head, so the per-head inner is at least
   |union of rests| + 1; three distinct size-2 rests on a 3-set need |union| + 2.
2. mutual-head: if s is not in its own rest-union and some block j in the group has head_j in that union and s in
   rest_j, one further position is forced.

**What this is not:** not banked. Banking is the lane owner's, on the sealed substrate, per the PRE-REG in
CAMPAIGN-a10.md. The bank bar there is against gen-0; against the champion P2 is at 0.725. The translation from the
n=4 Z3 modules to n-general Python is mine; the oracle, not the Z3 proof, is what certifies admissibility at n<=5,
and n=6 admissibility is not certified by anything here (the prover's soundness at n=6 rests on the bound being
admissible there; the lane's own practice is the same for every evolved bound).

**Suggested next in the lane:** run P2 on the laptop under the PRE-REG; if it holds, P2 is the gen-3 seed and the
next proposer prompt should carry the two terms' arguments as hints.

Files: `P1_mutual_head.py`, `P2_champion_plus_pilot.py`, `P3_partition_stack.py`, `TABLE-n4-comparison.md`,
`STAGE-RESULTS.md`; logs /tmp/lane-*.log on this box (screens and fitness JSON).
