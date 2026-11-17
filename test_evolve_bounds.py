"""test_evolve_bounds.py — birth battery for the evolution-lane harness (NULL-CONTROL-AT-BIRTH).

Ships in the same commit as evolve_bounds.py; run before any candidate verdict is trusted.
Controls both directions: a planted INADMISSIBLE bound must be REFUSED (stage A), a weak
ADMISSIBLE bound must pass A and die at C (dominated) — the instrument discriminates, not
just fires. Plus: canon_blocks <-> packed-canon bijection, lb3 reproduction (R3's exhaustive
zero-violation result), canon-wrap pointwise identity on lb3, import/type refusal, and an
end-to-end stage-D smoke at n=4 through the real subprocess path.

Run:  python test_evolve_bounds.py          (~30s; stage-A n=5 dominates the runtime)
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_DIR)

import evolve_bounds as eb  # noqa: E402
import proofmachine_v2 as v2  # noqa: E402
import proofmachine_v3 as v3  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)


def write_candidate(source):
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8",
                                     dir=tempfile.gettempdir())
    fh.write(source)
    fh.close()
    return fh.name


def random_relabel(state, n, rng):
    perm = list(range(n))
    rng.shuffle(perm)
    out = set()
    for s, r in state:
        nr = 0
        for t in range(n):
            if r & (1 << t):
                nr |= 1 << perm[t]
        out.add((perm[s], nr))
    return frozenset(out)


def sample_states(n, count, rng):
    states = []
    while len(states) < count:
        state = v2.root_state(n)
        for _ in range(rng.randrange(0, 3 * n)):
            hs = sorted(v2.heads(state))
            if not hs or not state:
                break
            state = v2.advance(state, rng.choice(hs))
        if state:
            states.append(state)
    return states


def main():
    t0 = time.time()
    # battery must not pollute the real ledger
    eb.LEDGER_PATH = os.path.join(tempfile.gettempdir(), f"evolution-ledger-battery-{os.getpid()}.jsonl")

    print("[1] canon_blocks <-> packed canon bijection (sampled, incl. relabeled pairs)")
    rng = random.Random(62714)
    mismatches = 0
    pairs_checked = 0
    for n in (4, 5):
        states = sample_states(n, 120, rng)
        for state in states:
            twin = random_relabel(state, n, rng)
            other = states[rng.randrange(len(states))]
            for a, b in ((state, twin), (state, other)):
                packed_equal = v2.canon(a, n) == v2.canon(b, n)
                unpacked_equal = eb.canon_blocks(a, n) == eb.canon_blocks(b, n)
                pairs_checked += 1
                if packed_equal != unpacked_equal:
                    mismatches += 1
    check("bijection holds on every sampled pair", mismatches == 0,
          f"{pairs_checked} pairs, {mismatches} mismatches")

    print("[2] refuse-plant: constant-100 bound (inadmissible) must be caught at stage A")
    plant = write_candidate("def lb_cand(blocks, n):\n    return 100\n")
    fn, _ = eb.load_candidate(plant)
    res = eb.admissibility_check(eb.make_wrapped(fn), 3)
    check("stage A verdict = VIOLATION", res["outcome"] == "VIOLATION",
          f"outcome={res['outcome']} violations={res['violation_count']}")
    check("counterexample recorded (claimed > truth)",
          bool(res["violations"]) and res["violations"][0]["claimed"] > res["violations"][0]["truth"])
    check("null control intact (root truth = 7)", res.get("root_truth") == 7)

    print("[3] sharp refuse-plant: lb3+1 must violate somewhere on the n<=5 ladder")
    caught = None
    for n in (3, 4, 5):
        res = eb.admissibility_check(lambda b, k: v3.lb3(b, k) + 1, n)
        if res["outcome"] == "VIOLATION":
            caught = (n, res["violation_count"])
            break
    check("lb3+1 caught (slack-0 class exists, R3)", caught is not None,
          f"first violation at n={caught[0]} ({caught[1]} classes)" if caught else "NOT caught")

    print("[4] weak-plant: zero bound is admissible (A clean) but dies at C (dominated)")
    weak = write_candidate("def lb_cand(blocks, n):\n    return 0\n")
    fn, _ = eb.load_candidate(weak)
    wrapped_weak = eb.make_wrapped(fn)
    stage_a = [eb.admissibility_check(wrapped_weak, n) for n in (3, 4)]
    check("stage A clean at n=3,4", all(r["outcome"] == "CLEAN" for r in stage_a))
    bc = eb.cost_and_strength(wrapped_weak)
    verdict = eb.screen_verdict(stage_a, bc)
    check("screen verdict = DEAD-C-DOMINATED", verdict == "DEAD-C-DOMINATED",
          f"verdict={verdict} vs_lb3={bc['vs_lb3']}")
    check("depth-floor: wrapped zero-bound is 1 on nonempty, 0 on empty (dfs invariant)",
          wrapped_weak(v2.root_state(4), 4) == 1 and wrapped_weak(frozenset(), 4) == 0)

    print("[5] reproduction control: canon-wrapped lb3 through the full stage-A ladder (n<=5)")
    wrapped_lb3 = eb.make_wrapped(v3.lb3)
    ladder = [eb.admissibility_check(wrapped_lb3, n) for n in (3, 4, 5)]
    check("zero violations on all rungs (reproduces R3)",
          all(r["outcome"] == "CLEAN" for r in ladder),
          "; ".join(f"n={r['n']}:{r['classes']}cls" for r in ladder))
    check("root truths 7/12/19 (oracle null controls)",
          [r.get("root_truth") for r in ladder] == [7, 12, 19])

    print("[6] canon-wrap identity on lb3 (relabel-invariant bound => wrap changes nothing)")
    bench_states = eb.sample_bench_states()
    diffs = sum(1 for s in bench_states if wrapped_lb3(s, 6) != v3.lb3(s, 6))
    check("pointwise equal on the 300 fixed n=6 states", diffs == 0, f"{diffs} diffs")

    print("[7] contract refusals")
    refused = False
    try:
        eb.load_candidate(write_candidate("import os\ndef lb_cand(blocks, n):\n    return 0\n"))
    except eb.CandidateContractError:
        refused = True
    check("import statement refused at load", refused)
    float_cand = write_candidate("def lb_cand(blocks, n):\n    return 1.5\n")
    fn, _ = eb.load_candidate(float_cand)
    died = False
    try:
        eb.admissibility_check(eb.make_wrapped(fn), 3)
    except eb.CandidateContractError:
        died = True
    check("non-int return dies loudly", died)

    print("[8] stage-B calibration sanity (live lb3 cost on this box)")
    bc = eb.cost_and_strength(wrapped_lb3)
    check("lb3 median in sane band (2-500us; R2 banked ~21us)",
          2 <= bc["lb3_median_us"] <= 500, f"measured {bc['lb3_median_us']}us")

    print("[9] end-to-end stage-D smoke at n=4 L=11 (real subprocess path, scratch cwd)")
    gen0 = eb.fitness(None, 4, 11, node_cap=200_000, wall_cap=60)
    check("gen-0 smoke: PROVED-NO", gen0.get("outcome") == "PROVED-NO",
          f"outcome={gen0.get('outcome')} nodes={gen0.get('nodes')}")
    check("workdir cleaned", gen0.get("workdir_removed") is True)
    weak_fit = eb.fitness(weak, 4, 11, node_cap=200_000, wall_cap=60)
    check("weak-bound smoke: PROVED-NO (candidate path end-to-end)",
          weak_fit.get("outcome") == "PROVED-NO",
          f"outcome={weak_fit.get('outcome')} nodes={weak_fit.get('nodes')}")
    both_counted = isinstance(gen0.get("nodes"), int) and isinstance(weak_fit.get("nodes"), int)
    check("node counts parsed for both arms", both_counted)
    if both_counted:
        check("discrimination: gen-0 searches fewer nodes than the zero bound",
              gen0["nodes"] < weak_fit["nodes"],
              f"gen0={gen0['nodes']:,} vs zero-bound={weak_fit['nodes']:,}")

    print("[9b] root check (row 528): a bound that asserts the answer at the root is CIRCULAR")
    # Shape of row 513 INCIDENT-3, at n=4 (a(4)=12, L=11): exact-root value, floor 1 elsewhere.
    # Admissible everywhere (truth at the root IS 12), so stage A cannot catch it; without the
    # root check prove_no returns PROVED-NO in one node.
    root_bound_src = ("def lb_cand(blocks, n):\n"
                      "    full = (1 << n) - 1\n"
                      "    if blocks == frozenset((s, full ^ (1 << s)) for s in range(n)):\n"
                      "        return {K}\n"
                      "    return 1\n")
    circ = write_candidate(root_bound_src.replace("{K}", "12"))
    circ_fit = eb.fitness(circ, 4, 11, node_cap=200_000, wall_cap=60)
    check("PLANTED NEGATIVE: root value 12 > L=11 -> CIRCULAR, never PROVED-NO",
          circ_fit.get("outcome") == "CIRCULAR" and circ_fit.get("root_value") == 12,
          f"outcome={circ_fit.get('outcome')} root_value={circ_fit.get('root_value')}")
    tie = write_candidate(root_bound_src.replace("{K}", "11"))
    tie_fit = eb.fitness(tie, 4, 11, node_cap=200_000, wall_cap=60)
    check("BOUNDARY: root value 11 == L is searched, not refused -> PROVED-NO with nodes > 1",
          tie_fit.get("outcome") == "PROVED-NO" and isinstance(tie_fit.get("nodes"), int)
          and tie_fit["nodes"] > 1,
          f"outcome={tie_fit.get('outcome')} nodes={tie_fit.get('nodes')}")

    print()
    print("[10] feedback loop: failures + scored attempts + champion selection (amendment (5))")
    # write synthetic rows to the BATTERY ledger (LEDGER_PATH already tmp-redirected above)
    import json as _json
    with open(eb.LEDGER_PATH, "w", encoding="utf-8") as fh:
        fh.write(_json.dumps({"kind": "screen", "cand": "candX.py", "verdict": "DEAD-A-VIOLATION-n4",
                              "stage_a": [{"violations": [{"state": [[1, 3]], "claimed": 9,
                                                           "truth": 7}]}]}) + "\n")
        fh.write(_json.dumps({"kind": "fitness", "cand": None, "outcome": "PROVED-NO",
                              "nodes": 100, "wall_seconds": 50.0}) + "\n")
    champ_path = write_candidate("def lb_cand(blocks, n):\n    return 1 if blocks else 0\n")
    with open(eb.LEDGER_PATH, "a", encoding="utf-8") as fh:
        fh.write(_json.dumps({"kind": "fitness", "cand": champ_path, "outcome": "PROVED-NO",
                              "nodes": 40, "wall_seconds": 20.0}) + "\n")
    fails = eb.recent_failures()
    check("planted DEAD row renders as counterexample", "counterexample" in fails
          and '"claimed": 9' in fails, fails[:90])
    attempts = eb.recent_attempts()
    check("scored attempts render with fitness numbers", "gen-0 (lb3)" in attempts
          and "20.0s wall" in attempts, attempts[:90])
    champ_src, champ_label = eb.current_champion()
    check("champion selection picks the banked candidate over lb3",
          os.path.basename(champ_path) == champ_label and "return 1 if blocks else 0" in champ_src,
          f"label={champ_label}")
    rendered = eb.build_prompt(champ_src, fails, attempts)
    check("prompt integrates all three memory sections",
          "counterexample" in rendered and "20.0s wall" in rendered
          and "(none yet)" not in rendered)
    # negative control: a clean ledger must feed NOTHING (no fabricated corpses)
    with open(eb.LEDGER_PATH, "w", encoding="utf-8") as fh:
        fh.write(_json.dumps({"kind": "screen", "cand": "candY.py",
                              "verdict": "SCREEN-PASS"}) + "\n")
    src2, label2 = eb.current_champion()
    check("negative control: clean ledger -> empty failures/attempts + lb3 fallback",
          eb.recent_failures() == "" and eb.recent_attempts() == "" and label2 == "gen-0 lb3",
          f"label={label2}")

    print()
    dt = time.time() - t0
    if FAILURES:
        print(f"BATTERY: {len(FAILURES)} FAILURE(S) in {dt:.1f}s -> " + ", ".join(FAILURES))
        sys.exit(1)
    print(f"BATTERY: ALL GREEN ({dt:.1f}s). Instrument discriminates in both directions; "
          "no candidate verdict is trusted without this battery green.")


if __name__ == "__main__":
    main()
