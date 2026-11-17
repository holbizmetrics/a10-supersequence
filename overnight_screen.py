#!/usr/bin/env python3
"""Unattended overnight screen loop for the a10 evolution lane (engine lane #1, phase 1).

RETIRED AS RUNNER 2026-08-17 (operator ruling, termux, after bus 3f3a0e5b).
Two unattended runners were built for this lane the same night, unaware of each
other — this one and PCLA/auto-runtime/engine-cadence/nightly_generation.py
(54b74b8). The operator picked ONE: engine-cadence keeps the lane (it carries the
cadence contract, battery, and arm/disarm gating). This file is retired-with-pointer,
NOT deleted: its a10-specific screen logic (stages A+B+C, B-kill provisional
semantics, selftest planted negatives) is the source for the lane-specific core to
be folded into engine-cadence on the windows box for gen-3. Do not arm this script
as a second live path into the lane.

FOLD-IN COMPLETE 2026-08-17 (windows session f73a8b4b, PCLA commit 66d4d64). The screen logic
named above now lives at PCLA `auto-runtime/engine-cadence/a10_screen_core.py`: classify() with
the DEAD-B-COST provisional semantics, the survivor-queue write, and the >=6-screened/zero-kills
lane falsifier (report flag + HIGH courier row + exit 3). Two things were ADDED in the port, not
inherited: an UNKNOWN verdict is now surfaced instead of falling through to "kill stands", and
the battery plants a mutant per new check. This file is now HISTORY ONLY -- nothing further is
owed from it, and it remains un-armable by ruling.

Two-phase cadence (generator-engine repo, lanes/01-a10-unattended.md):
  UNATTENDED (this script): generate -> screen (stages A+B+C) at volume; survivors queue.
  ATTENDED   (operator session): Stage D fitness on queued survivors ONLY. R1/R4 stands:
             unattended Stage D wall-clock is INVALID substrate; this script never runs D.

Kill semantics under unattended substrate:
  DEAD-A-* and DEAD-C-DOMINATED are timing-independent -> kills stand as-is.
  DEAD-B-COST is a microsecond-median call -> PROVISIONAL under unattended noise; the
  candidate is queued with requeue_reason for an attended re-screen, not silently dropped.

Usage:
  python overnight_screen.py run --gen 3 --rounds 4 --samples 3 [--max-hours 6]
                                 [--arm U] [--hints-file F]
  python overnight_screen.py selftest        # planted negatives (birth-defect rule)
"""
import argparse
import json
import os
import socket
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

import evolve_bounds as eb  # noqa: E402

QUEUE_PATH = os.path.join(REPO, "survivor-queue.jsonl")

# Falsifier (generator-engine SPEC.md): an evaluator that never says NO across a real run
# is presumed vacuous. Threshold: at least this many screened with zero kills -> halt signal.
FALSIFIER_MIN_SCREENED = 6


def ledger_size():
    try:
        return os.path.getsize(eb.LEDGER_PATH)
    except OSError:
        return 0


def rows_since(offset):
    if not os.path.exists(eb.LEDGER_PATH):
        return []
    rows = []
    with open(eb.LEDGER_PATH, "r", encoding="utf-8") as fh:
        fh.seek(offset)
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                # reason preserved, never swallowed: a corrupt ledger line is itself a finding
                rows.append({"kind": "ledger-parse-error", "error": repr(e), "raw": line[:200]})
    return rows


def append_queue(row, queue_path=QUEUE_PATH):
    row = dict(row)
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(queue_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def classify(row, substrate, gen, rnd):
    """Map one screen-ledger row to a queue action (or None: kill stands, ledger has it)."""
    if row.get("kind") != "screen":
        return None
    verdict = row.get("verdict", "")
    base = {"cand": row.get("cand"), "verdict": verdict, "gen": gen, "round": rnd,
            "substrate": substrate}
    if verdict == "SCREEN-PASS":
        return {"kind": "survivor", "stage_d": "PENDING-ATTENDED", **base}
    if verdict == "DEAD-B-COST":
        return {"kind": "provisional-b-kill",
                "requeue_reason": "B is a us-median under unattended timing noise; "
                                  "attended re-screen required before the kill is final", **base}
    return None  # DEAD-A-* / DEAD-C-DOMINATED / DEAD-WORKER: timing-independent, kill stands


def run(gen, rounds, samples, max_hours, arm, hints_file):
    substrate = f"unattended@{socket.gethostname()}"
    t0 = time.time()
    screened = kills = queued = 0
    for rnd in range(1, rounds + 1):
        if max_hours and (time.time() - t0) > max_hours * 3600:
            print(f"[run] max-hours reached after round {rnd - 1}; stopping")
            break
        offset = ledger_size()
        print(f"[run] round {rnd}/{rounds} gen={gen} samples={samples} substrate={substrate}")
        try:
            eb.generate(gen, samples, dry_run=False, hints_file=hints_file, arm=arm)
        except Exception as e:  # crash-safe per round; the reason is queued, not discarded
            append_queue({"kind": "round-error", "round": rnd, "error": repr(e)[:400],
                          "substrate": substrate})
            print(f"[run] round {rnd} errored ({type(e).__name__}); next round is independent")
            continue
        for row in rows_since(offset):
            if row.get("kind") == "screen":
                screened += 1
                if row.get("verdict") != "SCREEN-PASS":
                    kills += 1
            action = classify(row, substrate, gen, rnd)
            if action:
                append_queue(action)
                queued += 1
    print(f"[run] done: screened={screened} kills={kills} queued={queued} "
          f"(queue: {QUEUE_PATH})")
    if screened >= FALSIFIER_MIN_SCREENED and kills == 0:
        print("[run] LANE-FALSIFIER: evaluator returned zero NOs across a real run — "
              "presumed vacuous-or-timid; halt for operator review (SPEC.md falsifier)")
        return 3
    return 0


# ---------------------------------------------------------------- selftest (birth-defect rule)

OVERCLAIM_SRC = "def lb_cand(blocks, n):\n    return 999\n"          # must die at stage A
WEAK_SRC = "def lb_cand(blocks, n):\n    return 1 if blocks else 0\n"  # must die at stage C


def selftest():
    """Planted negatives: prove the loop can KILL and can QUEUE, before any real run."""
    import tempfile
    failures = []
    with tempfile.TemporaryDirectory(prefix="overnight-selftest-") as tmp:
        real_ledger = eb.LEDGER_PATH
        eb.LEDGER_PATH = os.path.join(tmp, "ledger.jsonl")  # keep selftest out of the real ledger
        try:
            for name, src, want_prefix in (("overclaim", OVERCLAIM_SRC, "DEAD-A-"),
                                           ("weak", WEAK_SRC, "DEAD-C-")):
                path = os.path.join(tmp, f"{name}.py")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(src)
                verdict = eb.screen(path).get("verdict", "")
                ok = verdict.startswith(want_prefix)
                print(f"{'PASS' if ok else 'FAIL'} planted {name}: verdict={verdict} "
                      f"(want {want_prefix}*)")
                if not ok:
                    failures.append(name)
            # classification + queue path: planted rows through classify() into a temp queue
            qpath = os.path.join(tmp, "queue.jsonl")
            cases = [({"kind": "screen", "cand": "x.py", "verdict": "SCREEN-PASS"}, "survivor"),
                     ({"kind": "screen", "cand": "y.py", "verdict": "DEAD-B-COST"},
                      "provisional-b-kill"),
                     ({"kind": "screen", "cand": "z.py", "verdict": "DEAD-C-DOMINATED"}, None),
                     ({"kind": "screen", "cand": "w.py", "verdict": "DEAD-A-VIOLATION-n4"}, None)]
            for row, want_kind in cases:
                action = classify(row, "selftest", 0, 0)
                got = action["kind"] if action else None
                ok = got == want_kind
                print(f"{'PASS' if ok else 'FAIL'} classify {row['verdict']}: -> {got} "
                      f"(want {want_kind})")
                if not ok:
                    failures.append(f"classify-{row['verdict']}")
                if action:
                    append_queue(action, qpath)
            queued = sum(1 for _ in open(qpath, encoding="utf-8"))
            ok = queued == 2
            print(f"{'PASS' if ok else 'FAIL'} queue write: {queued} rows (want 2)")
            if not ok:
                failures.append("queue-write")
            # rows_since offset parser on the selftest ledger (screen() appended 2 rows)
            n = sum(1 for r in rows_since(0) if r.get("kind") == "screen")
            ok = n == 2
            print(f"{'PASS' if ok else 'FAIL'} rows_since parser: {n} screen rows (want 2)")
            if not ok:
                failures.append("rows-since")
        finally:
            eb.LEDGER_PATH = real_ledger
    print(f"[selftest] {'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--gen", type=int, required=True)
    r.add_argument("--rounds", type=int, default=1)
    r.add_argument("--samples", type=int, default=3)
    r.add_argument("--max-hours", type=float, default=None)
    r.add_argument("--arm", default="")
    r.add_argument("--hints-file", default=None)
    sub.add_parser("selftest")
    a = p.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    sys.exit(run(a.gen, a.rounds, a.samples, a.max_hours, a.arm, a.hints_file))


if __name__ == "__main__":
    main()
