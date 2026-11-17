# EVOLUTION LANE — v3 FunSearch over admissible pruning bounds (opener, 2026-07-21)

**Why.** H1+H3 falsified the 10M bar at n=6; H4 measured gen-0's true figure (21.3M nodes /
7.47M states, 65.5 min laptop). n=7 projects ~2.4e11 nodes ⇒ per the charter, evolved bounds
are MANDATORY before the next rung. This file is the lane's design; the sealed decision rules
live in CAMPAIGN-a10.md § Rung log (2026-07-21 evolution-lane PRE-REG).

**Shape (inverse reduction gate, PCLA CRYSTAL.md).** This is novelty generation: the proposer
is free to be wildly wrong because the evaluator is mechanical. Rigor sits at the BACK:

```
propose (claude -p, unconstrained)  →  evaluate (4-stage mechanical cascade)  →  bank survivors
```

Nothing from the proposal stream is trusted or banked; only evaluator output is.

## Candidate contract

A candidate is a Python source file defining:

```python
def lb_cand(blocks, n):    # -> int >= 0
    ...
```

- `blocks`: frozenset of `(symbol, rest_bitmask)` pairs — the CANONICAL representative
  (the harness always feeds `canon_blocks(state)`; see soundness note below).
- Must return a non-bool `int`. The harness FLOORS the deployed value at 1 on nonempty
  states — load-bearing: the prover's dfs has no explicit depth guard, `bound > depth_left`
  IS the depth guard, so a 0-on-nonempty bound makes the prover unsound in the completeness
  direction (hallucinated words). Found by the birth battery's weak-plant arm at birth
  (zero bound returned WORD-EXISTS at n=4 L=11 vs proven sigma(4)=12). Truth of any
  nonempty state is >= 1, so the floor is always admissible.
- Executed under curated builtins + `math` only; imports are refused at load. This is the
  engine's threat model (our own LLM's buggy code), not an adversarial sandbox.
- Admissibility is NEVER trusted — every candidate goes through the oracle. A candidate may
  use any helper logic it writes inline; it may not read files, import, or keep state.

**Canon-wrap (load-bearing soundness rule).** The exhaustive admissibility oracle checks ONE
representative per canon-key class; that decides the class only if the bound is constant on
the class. Arbitrary evolved code has no such guarantee, so every candidate is deployed as
`lb_cand(canon_blocks(state), n)` — **constant on canon-key classes BY CONSTRUCTION** (note:
`v2.canon` is deliberately imperfect under relabeling — label-dependent tiebreaks — so this is
NOT full relabel-invariance; it is exactly the granularity the oracle enumerates and the
prover memoizes, which is all soundness needs). `canon_blocks` reproduces `v2.canon`'s
relabeling, unpacked; since the packed key is an injective encoding of `sorted(out)`,
packed-equal ⟺ unpacked-equal exactly — locked by the birth battery. The wrap's cost (one
extra canonicalization per bound call) is charged to the candidate: it is deployed reality,
not a harness artifact.

## Evaluator cascade (all mechanical; each stage's kill is pre-committed in the PRE-REG)

| stage | check | cost | kill condition |
|---|---|---|---|
| A | **Admissibility oracle**: exhaustive DP over every reachable canon class, n=3/4/5 (12 / 183 / 84,974 classes), built-in null controls (DP root truth must equal 7/12/19) — `exhaustive_lb_check` method, bound parameterized | ~13s | any violation, any crash, any non-int return, wall >300s in-process (+hard-kill backstop) |
| B | **Cost bench**: median per-call µs on the fixed 300 reachable n=6 states (seed 62714, min-of-50) — `bench_lb_cost` method; live lb3 reference measured alongside | ~30s | median ≥2ms AND no stage-C edge (the R2 algorithmic bar) |
| C | **Strength screen**: bound values vs lb3 on the same 300 states (higher/equal/lower counts) | ~1s | never higher than lb3 (dominated ⇒ cannot cut nodes) |
| D | **Fitness (the banked number)**: attended foreground fresh-memo `prove_no(6,27)` in a per-candidate scratch cwd, in-process node+wall caps set from gen-0's calibration run; fitness = **wall seconds to PROVED-NO** (nodes reported alongside) | ≤ gen-0's wall | cap exceeded (ranked below every verdicting candidate) |

**Fitness is WALL-CLOCK, never nodes-pruned alone** — the R2 lesson: a bound that prunes 10x
but costs 100x per call is a regression. Stage D measures the product directly.

**Substrate rules (R1/R4):** all Stage D runs attended foreground with in-process budgets;
background/unattended runs are INVALID substrate on the laptop. Never MSYS `timeout`.

**Memo hygiene:** each candidate runs in its own scratch cwd (fresh memo by construction);
the patched module's `code_fingerprint_v3` is overridden to hash (original fingerprint +
candidate source), so any snapshot written under a candidate self-identifies and can never be
resumed by a different bound. Fitness runs never resume.

**Failure feedback (the FunSearch signal):** a Stage A violation is logged with its
counterexample `(state, claimed, truth)`; screen/fitness scores are logged per candidate in
`evolution-ledger.jsonl` (append-only). The next generation's prompt carries the champion's
source + scores + the killed kin's counterexamples.

## Proposer

`claude -p` backend (proven on this box; no API key by design — feedback_no_api_key).
Gen-1 = flat best-of-N through the cascade; islands/migration (the engine's mechanisms) are
deferred until the flat loop shows signal — proportionality, not architecture appetite.
`evolve_bounds.py generate --dry-run` prints the exact prompt; the spawn loop is
WRITTEN-first, marked proven only after its first real run.

## What would count as winning

- **Gen-1 bank bar (sealed):** Stage A clean AND Stage D PROVED-NO under caps AND
  wall ≤ 0.67 × gen-0's fresh-memo wall (≥1.5x wall-clock cut at n=6).
- **Campaign relevance bar (not gen-1's problem):** n=7 needs orders of magnitude, not 1.5x.
  The lane iterates generations (champion re-seeds the prompt) until the n=6 figure projects
  n=7 into feasible territory (measured growth, per the honest rule: no scaling claim without
  a measured rung) — or until the loop plateaus, which is itself a finding that routes the
  campaign to the fleet/correspondence fallbacks.

## Files

- `evolve_bounds.py` — harness: loader (curated exec), canon-wrap, cascade stages A-D,
  ledger, proposer prompt. CLI: `screen` / `fitness` / `baseline-fitness` / `generate`.
- `test_evolve_bounds.py` — birth battery (NULL-CONTROL-AT-BIRTH, same commit): refuse-plant
  (inadmissible must be caught), weak-plant (admissible-but-dominated must die at C, not A),
  lb3 reproduction + canon-wrap invariance controls, packed/unpacked canon consistency,
  import-refusal, end-to-end Stage D smoke at n=4.
- `evolution-ledger.jsonl` — append-only candidate ledger (created on first use).
