# Experiment 1 – The Bubble Algorithm Library

Experimentation & Evaluation 2026 (USI) – Assignment 1.

Measures the execution time of three Bubble Sort variants
(`BubbleSortPassPerItem`, `BubbleSortUntilNoChange`, `BubbleSortWhileNeeded`)
to recommend one of them to Bubble Inc. The report itself is submitted on iCorsi.

## Hypotheses

- **H1:** For every input type and array size, WhileNeeded has a lower median
  execution time than PassPerItem and UntilNoChange, because it never makes
  more comparisons than them.
- **H2:** On sorted input, UntilNoChange and WhileNeeded have a lower median
  execution time than PassPerItem for every array size.

Decision rule (fixed before the measurements): "A has a lower median execution time
than B" means `Q3(A) < Q1(B)`, i.e. the middle halves (IQRs) of the 30 runs do not overlap.

## Design

| | |
|---|---|
| Independent variables | algorithm (3 levels), input type (sorted, reversed, random), array size (1,000, 5,000, 10,000) |
| Dependent variable | wall-clock time of one `sort()` call, `System.nanoTime()`, reported in ms (µs for sorted input) |
| Control variables | element type `Integer` (distinct values 0..n-1); fixed seeds (random input: a different permutation per repetition, the same for all three algorithms); same machine and JVM; heap fixed (`-Xms1g -Xmx1g`); other applications closed; on AC power |
| Repetitions | 10 discarded warm-up rounds, then 30 measured runs per condition (27 conditions, 810 measurements) |

Measurement protocol (see `src/exp01/Benchmark.java`):
1. All inputs are generated before measuring, from fixed seeds.
2. Warm-up: every condition is run 10 times and the times are discarded.
3. All 810 measured runs are executed in one seeded random order.
4. Before each run a fresh copy of the input is made and `System.gc()` is requested (not timed).
5. Each result is checked to be sorted (not timed).

## Repository layout

```
src/exp01/                the three provided algorithms (unchanged), Sorter, Benchmark.java
build/                    compiled classes (Java 11 bytecode), used if javac is not available
run.sh                    compiles (if javac exists), records the system, runs the experiment
data/results.csv          raw measurements of the reported run (one row per sort call)
data/environment.txt      JVM properties and run parameters of that run
data/system_info.txt      macOS version, model, CPU, cores, memory, power state, Java version, JVM flags (G1 GC)
data/vm_pilot/            earlier pilot run (see below); not used in the report
analysis/analyze.py       descriptive statistics, box plots, hypothesis check
analysis/design_figure.py draws the design figure of the report
results/                  summary.csv, hypotheses.txt, boxplots.png, design.png
```

## Reproduce

Requirements: Java 11 or newer, Python 3.9 or newer with `pandas` and `matplotlib`.

```bash
bash run.sh                        # < 1 min on an Apple M3 Pro; OVERWRITES data/results.csv
python3 analysis/analyze.py        # writes results/summary.csv, hypotheses.txt, boxplots.png
python3 analysis/design_figure.py  # writes results/design.png
```

To keep the reported data, copy `data/` before running `run.sh` again.

## Measurement environment of the reported data

MacBook Pro (Mac15,6), Apple M3 Pro (5 performance + 6 efficiency cores), 18 GB RAM,
macOS 26.5.2, on AC power; Eclipse Temurin OpenJDK 25.0.2 (G1 GC).
Details in `data/environment.txt` and `data/system_info.txt`.

`data/vm_pilot/` holds a pilot run made with an earlier version of the harness
(Linux VM on the same laptop, Java 11, sizes 100/1,000/10,000, one random permutation
per size, 5 warm-up rounds). That version of the harness is not in this repository,
so the pilot cannot be reproduced exactly; it is kept only for transparency.

## Use of generative AI

`Benchmark.java`, `run.sh`, `analyze.py`, `design_figure.py` and this README were written
by an AI assistant (Claude by Anthropic). The hypotheses were formulated by the author,
who also ran the experiment on his laptop. The statistics and figures were computed by the
AI with `analyze.py` from the author's `data/results.csv`. Details are in Appendix C of the
report submitted on iCorsi.
