# About this repository

This is a snapshot of the `a10-supersequence/` folder of a private research monorepo, taken on
2026-11-17 at its commit `dd8eb53`. The files are unchanged, apart from this notice. One unsent
draft letter was left out.

**The question.** OEIS A062714 asks for the shortest word over n symbols that contains all n!
orderings as subsequences. The data ends at a(9) = 66. The open cell is a(10): an 83-symbol
word is known, and the question is whether an 82 exists. Start with `README.md`. The full,
append-only record is in `CAMPAIGN-a10.md`.

**What to check first** (needs nothing but Python 3):
- `the66.json` is the published a(9) word. `calibrate_n9_result.json` is a second, different
  complete 66-word that this campaign found on its own, as a calibration run.
- `test_evolve_bounds.py` is the instrument's own test battery. It ran ALL GREEN in this exact
  standalone copy before it was published.
- `exhaustive_lb_check.py` checks every pruning bound against brute force on every reachable
  state through n = 5.

**References you cannot follow.** The logs name "PCLA", courier rows, session tokens such as
`d9d555c1`, and `D:\...` paths. These are the private lab and the machines the runs were done on.
They are kept as recorded so that the history stays intact, and they are not needed to rerun
anything here.

**Negative results** are written as what they are: a capped search that finds nothing shows only
that nothing turned up within its budget. Nothing here claims a(10) = 83.
