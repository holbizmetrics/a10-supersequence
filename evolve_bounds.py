"""evolve_bounds.py — evolution-lane harness: propose / evaluate / bank admissible LB bounds.

Design: EVOLUTION-LANE.md. Sealed decision rules: CAMPAIGN-a10.md § Rung log (2026-07-21
evolution-lane PRE-REG). Birth battery: test_evolve_bounds.py (NULL-CONTROL-AT-BIRTH).

Candidate contract: a .py file defining  def lb_cand(blocks, n) -> int >= 0  where blocks is a
frozenset of (symbol, rest_bitmask) pairs — always the CANONICAL representative (canon_blocks).
Curated builtins + math only; imports refused. Admissibility never trusted: oracle-gated.

CLI:
  python evolve_bounds.py screen  --cand cand.py            # stages A (n<=5) + B + C, ledger row
  python evolve_bounds.py fitness --cand cand.py --node-cap N --wall-cap S   # stage D
  python evolve_bounds.py baseline-fitness --wall-cap S     # gen-0 (lb3 as deployed) stage D
  python evolve_bounds.py generate --gen K [--samples N] [--dry-run]         # claude -p proposer
"""
from __future__ import annotations

import argparse
import builtins as builtins_module
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_DIR)

import proofmachine_v2 as v2  # noqa: E402
import proofmachine_v3 as v3  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

A_TRUE = {3: 7, 4: 12, 5: 19}          # proven ground truth — the oracle's built-in null control
LEDGER_PATH = os.path.join(REPO_DIR, "evolution-ledger.jsonl")
COST_BENCH_SEED = 62714                 # the R2 micro-bench convention: same fixed 300 states
COST_BENCH_STATES = 300
COST_BENCH_REPS = 50
SCREEN_WALL_BUDGET = 300                # in-process seconds for the whole stage-A ladder
SCREEN_KILL_BACKSTOP = 420              # outer hard-kill for a wedged candidate call


class CandidateContractError(Exception):
    pass


# ---------------------------------------------------------------- canonical representative

def canon_blocks(blocks, n):
    """The relabeling of v2.canon, UNPACKED: returns frozenset of (symbol, rest_mask).

    v2.canon packs sorted(out) with a fixed-width injective encoding, so
    canon(a) == canon(b)  <=>  canon_blocks(a) == canon_blocks(b)  exactly.
    A canon-wrapped candidate is therefore CONSTANT on canon-key classes by construction —
    the granularity the exhaustive oracle checks and the prover memoizes. (True relabel
    invariance is not required anywhere; constancy per canon-key class is.)
    Battery-locked against the packed key: test_evolve_bounds.py.
    """
    def label_free_key(b):
        s, r = b
        return (bin(r).count("1"),)
    order = sorted(blocks, key=lambda b: (label_free_key(b), b))
    mapping = {}

    def lab(s):
        if s not in mapping:
            mapping[s] = len(mapping)
        return mapping[s]

    out = []
    for s, r in order:
        ns = lab(s)
        rest = sorted(lab(t) for t in range(n) if r & (1 << t))
        nr = 0
        for t in rest:
            nr |= 1 << t
        out.append((ns, nr))
    return frozenset(out)


# ---------------------------------------------------------------- candidate loading + wrap

CURATED_BUILTIN_NAMES = (
    "abs", "all", "any", "bin", "bool", "dict", "divmod", "enumerate", "filter",
    "frozenset", "int", "len", "list", "map", "max", "min", "pow", "range",
    "reversed", "set", "sorted", "str", "sum", "tuple", "zip",
)
CURATED_BUILTINS = {name: getattr(builtins_module, name) for name in CURATED_BUILTIN_NAMES}


def load_candidate(path):
    """Load lb_cand from a source file under curated globals. Imports are refused."""
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    if re.search(r"^\s*(import|from)\s", source, re.MULTILINE):
        raise CandidateContractError("import statements are refused in candidate source")
    namespace = {"__builtins__": CURATED_BUILTINS, "math": math}
    exec(compile(source, path, "exec"), namespace)  # threat model: our own LLM's buggy code
    fn = namespace.get("lb_cand")
    if not callable(fn):
        raise CandidateContractError("candidate must define lb_cand(blocks, n)")
    return fn, source


def make_wrapped(candidate_fn):
    """Deploy form: candidate always sees the canonical representative; int-typed; FLOORED AT 1
    on nonempty blocks. The floor is load-bearing, not cosmetic: prove_no's dfs has no explicit
    depth guard — `bound > depth_left` is the only thing stopping recursion below depth 0, so a
    bound returning 0 on a nonempty state makes the prover UNSOUND in the completeness direction
    (it can 'find' words longer than the budget). Caught by the birth battery on its first run
    (zero-bound arm returned WORD-EXISTS at n=4 L=11, contradicting proven sigma(4)=12).
    Sound: truth(nonempty) >= 1 always, so the floor never overclaims."""
    def lb_evolved(blocks, n):
        if not blocks:
            return 0
        value = candidate_fn(canon_blocks(blocks, n), n)
        if type(value) is not int:
            raise CandidateContractError(f"lb_cand returned {type(value).__name__}, must be int")
        return value if value > 1 else 1
    return lb_evolved


def candidate_sha(source):
    return hashlib.sha256(source.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- stage A: admissibility oracle

def admissibility_check(bound_fn, n, wall_budget=None, max_recorded_violations=5,
                        progress_every=100_000):
    """exhaustive_lb_check's DP, parameterized on the bound. Exhaustive over every reachable
    canon-key class at n; truth from completion DP (advance/heads only — uncheatable).
    Null control: DP root truth must equal the proven a(n). In-process wall budget (R1)."""
    started = time.time()
    truth_memo = {}
    stats = {"n": n, "classes": 0, "violations": [], "violation_count": 0, "worst_slack": None}
    sys.setrecursionlimit(200_000)

    def truth(state):
        if not state:
            return 0
        key = v2.canon(state, n)
        hit = truth_memo.get(key)
        if hit is not None:
            return hit
        if wall_budget is not None and time.time() - started > wall_budget:
            raise TimeoutError
        best = None
        for x in sorted(v2.heads(state)):
            t = 1 + truth(v2.advance(state, x))
            if best is None or t < best:
                best = t
        truth_memo[key] = best
        stats["classes"] += 1
        if stats["classes"] % progress_every == 0:
            print(f"  ... n={n}: {stats['classes']:,} classes, {time.time()-started:.0f}s")
        claimed = bound_fn(state, n)
        if claimed > best:
            stats["violation_count"] += 1
            if len(stats["violations"]) < max_recorded_violations:
                stats["violations"].append(
                    {"state": sorted(state), "claimed": claimed, "truth": best})
        slack = best - claimed
        if stats["worst_slack"] is None or slack < stats["worst_slack"]:
            stats["worst_slack"] = slack
        return best

    try:
        root_truth = truth(v2.root_state(n))
    except TimeoutError:
        stats["outcome"] = "WALL-BUDGET-EXCEEDED"
        stats["seconds"] = round(time.time() - started, 1)
        return stats
    stats["root_truth"] = root_truth
    stats["root_truth_ok"] = (root_truth == A_TRUE[n])
    stats["outcome"] = ("NULL-CONTROL-FAILED" if not stats["root_truth_ok"]
                       else "VIOLATION" if stats["violation_count"] else "CLEAN")
    stats["seconds"] = round(time.time() - started, 1)
    return stats


# ---------------------------------------------------------------- stages B + C: cost + strength

def sample_bench_states(n=6, seed=COST_BENCH_SEED, target=COST_BENCH_STATES):
    """The R2 micro-bench sampler: distinct reachable states via random advance-walks."""
    import random as random_module
    rng = random_module.Random(seed)
    states = set()
    tries = 0
    while len(states) < target and tries < 20_000:
        tries += 1
        state = v2.root_state(n)
        for _ in range(rng.randrange(1, 4 * n)):
            hs = sorted(v2.heads(state))
            if not hs or not state:
                break
            state = v2.advance(state, rng.choice(hs))
        if state:
            states.add(state)
    return sorted(states, key=lambda s: sorted(s))


def cost_and_strength(bound_fn, n=6, reps=COST_BENCH_REPS):
    """Median per-call cost (min-of-reps per state) + strength vs live lb3 on the same states."""
    states = sample_bench_states(n=n)
    reference_fn = v3.lb3

    def time_per_call(fn):
        per_state = []
        for state in states:
            best = None
            for _ in range(reps):
                t0 = time.perf_counter_ns()
                fn(state, n)
                dt = time.perf_counter_ns() - t0
                if best is None or dt < best:
                    best = dt
            per_state.append(best / 1000.0)  # microseconds
        return statistics.median(per_state)

    candidate_median_us = time_per_call(bound_fn)
    lb3_median_us = time_per_call(reference_fn)
    higher = equal = lower = 0
    for state in states:
        cv, rv = bound_fn(state, n), reference_fn(state, n)
        if cv > rv:
            higher += 1
        elif cv == rv:
            equal += 1
        else:
            lower += 1
    return {"states": len(states), "candidate_median_us": round(candidate_median_us, 1),
            "lb3_median_us": round(lb3_median_us, 1),
            "vs_lb3": {"higher": higher, "equal": equal, "lower": lower}}


# ---------------------------------------------------------------- screen (A+B+C), subprocessed

def screen_verdict(stage_a_results, bc):
    for res in stage_a_results:
        if res["outcome"] != "CLEAN":
            return f"DEAD-A-{res['outcome']}-n{res['n']}"
    if bc["vs_lb3"]["higher"] == 0:
        return "DEAD-C-DOMINATED"
    if bc["candidate_median_us"] >= 2000 and bc["vs_lb3"]["higher"] == 0:
        return "DEAD-B-COST"  # unreachable after the C kill above; kept for rule visibility
    if bc["candidate_median_us"] >= 2000:
        return "DEAD-B-COST"
    return "SCREEN-PASS"


def run_screen_worker(cand_path):
    """In-worker body: stages A (n=3,4,5) + B + C. Emits one JSON line."""
    result = {"cand": cand_path}
    try:
        fn, source = load_candidate(cand_path)
        wrapped = make_wrapped(fn)
        result["sha"] = candidate_sha(source)
        stage_a = []
        for n in (3, 4, 5):
            stage_a.append(admissibility_check(wrapped, n, wall_budget=SCREEN_WALL_BUDGET))
            if stage_a[-1]["outcome"] != "CLEAN":
                break
        result["stage_a"] = stage_a
        if all(r["outcome"] == "CLEAN" for r in stage_a) and len(stage_a) == 3:
            result["stage_bc"] = cost_and_strength(wrapped)
            result["verdict"] = screen_verdict(stage_a, result["stage_bc"])
        else:
            result["verdict"] = screen_verdict(stage_a, {"vs_lb3": {"higher": 1},
                                                         "candidate_median_us": 0})
    except (CandidateContractError, Exception) as err:  # noqa: BLE001 — any crash = DEAD
        result["verdict"] = "DEAD-CRASH"
        result["error"] = f"{type(err).__name__}: {err}"
    print("SCREEN-RESULT " + json.dumps(result))


def screen(cand_path):
    """Parent: run the screen in a killable subprocess (a wedged candidate cannot hang us)."""
    proc = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "_screen-worker", "--cand",
         os.path.abspath(cand_path)],
        capture_output=True, text=True, timeout=SCREEN_KILL_BACKSTOP, cwd=REPO_DIR)
    for line in proc.stdout.splitlines():
        if not line.startswith("SCREEN-RESULT "):
            print(line)
    payload = _extract_json(proc.stdout, "SCREEN-RESULT ")
    if payload is None:
        payload = {"cand": cand_path, "verdict": "DEAD-WORKER",
                   "error": (proc.stderr or "no output").strip()[-400:]}
    append_ledger({"kind": "screen", **payload})
    return payload


# ---------------------------------------------------------------- stage D: fitness (prover run)

def run_fitness_worker(cand_path, n, length, node_cap, wall_cap, workdir):
    """In-worker body: patch v3.lb3 with the wrapped candidate (or run gen-0 as deployed when
    cand_path is None), override the memo fingerprint to include the candidate source, run
    prove_no fresh in the scratch cwd. Emits one JSON line after prove_no's own output."""
    os.makedirs(workdir, exist_ok=True)
    os.chdir(workdir)  # memo files land here — fresh per candidate by construction
    original_fingerprint = v3.code_fingerprint_v3()
    label = "gen-0 (lb3 as deployed)"
    if cand_path is not None:
        fn, source = load_candidate(cand_path)
        wrapped = make_wrapped(fn)
        combined = hashlib.sha256((original_fingerprint + source).encode()).hexdigest()
        # ROOT CHECK (row 528, operator's word 2026-11-12): a bound whose value at the rung-n root
        # already exceeds `length` asserts the answer -- prove_no would return PROVED-NO in one node
        # without searching (row 513 INCIDENT-3: a table reading a(6)=28 'proved' (6,27)). The
        # stage-A screen is exhaustive only to n<=5, so it cannot see this at n=6. Such a run is
        # CIRCULAR, never PROVED-NO. Same rule as auto-runtime/engine-cadence/a10_root_check.py
        # (20eaba42), placed HERE so the frozen evaluator applies it to H17 Arm P and Arm E alike.
        # A bound that raises at the root kills the worker -> WORKER-DIED, which never banks.
        # Residual: sees the root only; a bound can read a(n) deeper and stay <= length at the root.
        # Root value == length is NOT refused: that bound must still be searched to prove anything.
        root_value = wrapped(v2.root_state(n), n)
        if root_value > length:
            print(f"[fitness] candidate {candidate_sha(source)}: "
                  f"CIRCULAR -- lb at the n={n} root is {root_value} > length {length}; not searched")
            print("FITNESS-RESULT " + json.dumps(
                {"cand": cand_path, "n": n, "length": length, "outcome": "CIRCULAR",
                 "root_value": root_value, "wall_seconds": 0.0, "node_cap": node_cap,
                 "wall_cap": wall_cap}))
            return
        v3.lb3 = wrapped                      # dfs resolves lb3 via module globals
        v3.code_fingerprint_v3 = lambda: combined
        label = f"candidate {candidate_sha(source)}"
    print(f"[fitness] {label}: prove_no({n},{length}) node_cap={node_cap} wall_cap={wall_cap}s "
          f"cwd={workdir}")
    wall_started = time.time()
    verdict = v3.prove_no(n, length, node_budget=node_cap, wall_budget=wall_cap)
    elapsed = round(time.time() - wall_started, 1)
    outcome = {True: "PROVED-NO", False: "WORD-EXISTS", None: "CAP-EXCEEDED"}[verdict]
    print("FITNESS-RESULT " + json.dumps(
        {"cand": cand_path, "n": n, "length": length, "outcome": outcome,
         "wall_seconds": elapsed, "node_cap": node_cap, "wall_cap": wall_cap}))


def fitness(cand_path, n, length, node_cap, wall_cap, keep_workdir=False):
    """Parent: attended-foreground contract is the CALLER's responsibility (R1: background =
    invalid substrate on the laptop). Runs the worker as a direct child, parses nodes from
    prove_no's own output line, appends the ledger row."""
    tag = "gen0" if cand_path is None else candidate_sha(open(cand_path, encoding="utf-8").read())
    workdir = os.path.join(REPO_DIR, "evolution-runs", f"{tag}-n{n}L{length}-{int(time.time())}")
    cmd = [sys.executable, os.path.abspath(__file__), "_fitness-worker",
           "--n", str(n), "--length", str(length), "--workdir", workdir]
    if cand_path is not None:
        cmd += ["--cand", os.path.abspath(cand_path)]
    if node_cap is not None:
        cmd += ["--node-cap", str(node_cap)]
    if wall_cap is not None:
        cmd += ["--wall-cap", str(wall_cap)]
    outer_timeout = (wall_cap + 600) if wall_cap else None  # backstop only; in-process wall decides
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=outer_timeout,
                          cwd=REPO_DIR)
    for line in proc.stdout.splitlines():
        if not line.startswith("FITNESS-RESULT "):
            print(line)
    payload = _extract_json(proc.stdout, "FITNESS-RESULT ")
    if payload is None:
        payload = {"cand": cand_path, "outcome": "WORKER-DIED",
                   "error": (proc.stderr or "no output").strip()[-400:]}
    nodes_match = re.search(r"\(([\d,]+) nodes, memo ([\d,]+)", proc.stdout)
    if nodes_match:
        payload["nodes"] = int(nodes_match.group(1).replace(",", ""))
        payload["memo_entries"] = int(nodes_match.group(2).replace(",", ""))
    budget_match = re.search(r"BUDGET-EXCEEDED at ([\d,]+) nodes", proc.stdout)
    if budget_match:
        payload["nodes"] = int(budget_match.group(1).replace(",", ""))
    payload["workdir"] = workdir
    if not keep_workdir:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)
        payload["workdir_removed"] = True
    append_ledger({"kind": "fitness", **payload})
    return payload


# ---------------------------------------------------------------- proposer (claude -p)

PROPOSER_PROMPT = """You are evolving an ADMISSIBLE lower-bound function for a shortest-\
supersequence prover (OEIS A062714). State: frozenset of (symbol, rest_bitmask) blocks over n \
symbols; block (s, r) means: some pending suffix starts with symbol s and must then contain \
every symbol in bitmask r (in some order established by deeper blocks). lb_cand(blocks, n) must \
return an int LOWER BOUND on the number of symbols any completion still needs. ADMISSIBILITY IS \
MANDATORY: overclaiming by 1 on any reachable state is instant death (exhaustively checked \
n<=5). Strength: prune more nodes than the champion below at n=6. Cost: you pay wall-clock — \
a bound 10x stronger but 100x slower loses.

Champion source (beat it):
```python
{champion_source}
```

Recent measured attempts (fitness axis = wall seconds, lower is better):
{attempts_feedback}

Recent failures (learn from the counterexamples):
{failure_feedback}

Rules: define exactly `def lb_cand(blocks, n):`. Pure function, curated builtins + math only, \
NO imports, no I/O, no state. Reply with ONE python code block containing only the candidate."""


def build_prompt(champion_source, failure_feedback, attempts_feedback=""):
    return PROPOSER_PROMPT.format(champion_source=champion_source,
                                  failure_feedback=failure_feedback or "(none yet)",
                                  attempts_feedback=attempts_feedback or "(none yet)")


def recent_failures(limit=3):
    lines = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows[::-1]:
            if row.get("kind") == "screen" and row.get("verdict", "").startswith("DEAD"):
                sample = row.get("stage_a", [{}])[-1].get("violations", [])[:1]
                lines.append(f"- {row.get('verdict')}"
                             + (f" counterexample={json.dumps(sample[0])}" if sample else ""))
            if len(lines) >= limit:
                break
    return "\n".join(lines)


def current_champion():
    """Champion selection from the ledger (prereg amendment (5a), 2026-08-14): the banked
    candidate with the lowest wall_seconds that beat gen-0's wall on the same task; falls
    back to lb3 when no candidate has banked. Returns (source_text, label)."""
    gen0_wall, best = None, None
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("kind") != "fitness" or row.get("outcome") != "PROVED-NO":
                    continue
                if row.get("cand") is None:
                    gen0_wall = row.get("wall_seconds")
                elif best is None or row.get("wall_seconds", 1e18) < best.get("wall_seconds", 1e18):
                    best = row
    if best and gen0_wall and best["wall_seconds"] < gen0_wall and os.path.exists(best["cand"]):
        with open(best["cand"], encoding="utf-8") as fh:
            source = fh.read()
        label = os.path.basename(best["cand"])
        header = (f"# current champion {label} — banked PROVED-NO at "
                  f"{best.get('nodes'):,} nodes / {best['wall_seconds']}s "
                  f"(gen-0 was {gen0_wall}s); your candidate replaces it wholesale:\n")
        return header + source, label
    return ("# gen-0 champion is proofmachine_v3.lb3 (+_group_lb, _scs_pair) — "
            "shown for structure; your candidate replaces it wholesale:\n"
            + _source_of(v3._group_lb) + "\n" + _source_of(v3.lb3)), "gen-0 lb3"


def recent_attempts(limit=5):
    """Scored-attempts memory (prereg amendment (5b)): recent fitness rows, newest first,
    so the proposer sees measured selection pressure, not just the champion."""
    lines = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        for row in rows[::-1]:
            if row.get("kind") != "fitness":
                continue
            label = os.path.basename(row["cand"]) if row.get("cand") else "gen-0 (lb3)"
            nodes = row.get("nodes")
            lines.append(f"- {label}: {row.get('outcome')} "
                         f"{nodes:,} nodes / {row.get('wall_seconds')}s wall"
                         if isinstance(nodes, int) else f"- {label}: {row.get('outcome')}")
            if len(lines) >= limit:
                break
    return "\n".join(lines)


def generate(generation, samples, dry_run, hints_file=None, arm=""):
    """claude -p proposer loop. WRITTEN-first; proven only after its first real run.
    hints_file/arm: the gen-2 A/B mechanism (prereg (2)) — ARM H appends the hints file's
    text as an extra prompt section; ARM U runs the base prompt. Candidates are tagged by
    arm in their filenames so Stage D attribution is mechanical."""
    champion_source, champion_label = current_champion()
    print(f"[generate] champion in prompt: {champion_label}" + (f"  arm={arm}" if arm else ""))
    prompt = build_prompt(champion_source, recent_failures(), recent_attempts())
    if hints_file:
        with open(hints_file, encoding="utf-8") as fh:
            prompt += chr(10) + fh.read()
    if dry_run:
        print(prompt)
        return
    gen_dir = os.path.join(REPO_DIR, "candidates", f"gen{generation}")
    os.makedirs(gen_dir, exist_ok=True)
    for i in range(samples):
        print(f"[generate] sampling candidate {i+1}/{samples} via claude -p ...")
        # 2026-08-14 plumbing fix (proposer only; sealed stages/caps untouched):
        # capture_output=True inherits pipes, and on this box concurrent Claude
        # sessions can hold the write handle open forever (documented spawn-handle
        # race, 2026-08-05 f972b5ae) -- observed live: sample 1 returned in ~6 min,
        # sample 2 wedged to the 600s cap on a clean disk. stdout now goes to a
        # real file (no inheritable pipe), stdin is DEVNULL, and one wedged sample
        # no longer aborts the round.
        reply_path = os.path.join(gen_dir, f"reply_{int(time.time())}_{i}.txt")
        try:
            with open(reply_path, "w", encoding="utf-8") as out_fh:
                subprocess.run(["claude", "-p", prompt], stdout=out_fh,
                               stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               text=True, timeout=600)
            with open(reply_path, encoding="utf-8") as in_fh:
                reply_text = in_fh.read()
        except subprocess.TimeoutExpired:
            print(f"  sample {i+1} timed out (600s); continuing with next sample")
            continue
        block = re.search(r"```python\n(.*?)```", reply_text, re.DOTALL)
        if not block:
            print("  no code block in reply; skipped")
            continue
        cand_path = os.path.join(gen_dir, f"cand{('_' + arm) if arm else ''}_{int(time.time())}_{i}.py")
        with open(cand_path, "w", encoding="utf-8") as fh:
            fh.write(block.group(1))
        print(f"  saved {cand_path}; screening ...")
        verdict = screen(cand_path)
        print(f"  -> {verdict.get('verdict')}")


def _source_of(fn):
    import inspect
    return inspect.getsource(fn)


# ---------------------------------------------------------------- plumbing

def _extract_json(stdout, marker):
    for line in stdout.splitlines():
        if line.startswith(marker):
            return json.loads(line[len(marker):])
    return None


def append_ledger(row):
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LEDGER_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("screen");            p.add_argument("--cand", required=True)
    p = sub.add_parser("_screen-worker");    p.add_argument("--cand", required=True)
    p = sub.add_parser("fitness")
    p.add_argument("--cand", required=True); p.add_argument("--n", type=int, default=6)
    p.add_argument("--length", type=int, default=27)
    p.add_argument("--node-cap", type=int, default=None)
    p.add_argument("--wall-cap", type=int, default=None)
    p.add_argument("--keep-workdir", action="store_true")
    p = sub.add_parser("baseline-fitness")
    p.add_argument("--n", type=int, default=6); p.add_argument("--length", type=int, default=27)
    p.add_argument("--node-cap", type=int, default=None)
    p.add_argument("--wall-cap", type=int, default=None)
    p.add_argument("--keep-workdir", action="store_true")
    p = sub.add_parser("_fitness-worker")
    p.add_argument("--cand", default=None); p.add_argument("--n", type=int, required=True)
    p.add_argument("--length", type=int, required=True)
    p.add_argument("--node-cap", type=int, default=None)
    p.add_argument("--wall-cap", type=int, default=None)
    p.add_argument("--workdir", required=True)
    p = sub.add_parser("generate")
    p.add_argument("--gen", type=int, required=True)
    p.add_argument("--samples", type=int, default=4)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--hints-file", default=None)
    p.add_argument("--arm", default="")

    args = parser.parse_args()
    if args.cmd == "screen":
        print(json.dumps(screen(args.cand), indent=2))
    elif args.cmd == "_screen-worker":
        run_screen_worker(args.cand)
    elif args.cmd == "fitness":
        print(json.dumps(fitness(args.cand, args.n, args.length, args.node_cap, args.wall_cap,
                                 args.keep_workdir), indent=2))
    elif args.cmd == "baseline-fitness":
        print(json.dumps(fitness(None, args.n, args.length, args.node_cap, args.wall_cap,
                                 args.keep_workdir), indent=2))
    elif args.cmd == "_fitness-worker":
        run_fitness_worker(args.cand, args.n, args.length, args.node_cap, args.wall_cap,
                           args.workdir)
    elif args.cmd == "generate":
        generate(args.gen, args.samples, args.dry_run, args.hints_file, args.arm)


if __name__ == "__main__":
    main()
