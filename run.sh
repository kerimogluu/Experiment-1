#!/usr/bin/env bash
# Compiles and runs the full experiment.
# Usage (from the repository folder):  bash run.sh
# Before running: close other applications and connect the charger.
set -euo pipefail
cd "$(dirname "$0")"

if command -v javac >/dev/null 2>&1; then
  rm -rf build
  javac --release 11 -d build src/exp01/*.java
fi

mkdir -p data
# Record the machine, OS, power state and effective JVM flags (incl. garbage collector).
{
  echo "## date"; date -u
  if [ "$(uname)" = "Darwin" ]; then
    echo "## macOS"; sw_vers
    echo "## model"; sysctl -n hw.model
    echo "## CPU"; sysctl -n machdep.cpu.brand_string
    echo "## cores (performance, efficiency)"; sysctl -n hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu 2>/dev/null || sysctl -n hw.physicalcpu
    echo "## memory (bytes)"; sysctl -n hw.memsize
    echo "## power"; pmset -g batt | head -1
  else
    echo "## /etc/os-release"; cat /etc/os-release
    echo "## uname -a"; uname -a
    echo "## CPU"; lscpu
    echo "## memory"; free -h
  fi
  echo "## Java"; java -version 2>&1
  echo "## JVM flags"; java -Xms1g -Xmx1g -XX:+PrintCommandLineFlags -version 2>&1 | head -1
} > data/system_info.txt

# caffeinate keeps the Mac awake during the run (macOS only).
KEEP_AWAKE=""
if command -v caffeinate >/dev/null 2>&1; then KEEP_AWAKE="caffeinate -i"; fi

# Fixed heap size so that heap resizing does not interfere with timings.
$KEEP_AWAKE java -Xms1g -Xmx1g -cp build exp01.Benchmark \
  --reps=30 --warmup=10 --sizes=1000,5000,10000 --seed=42 \
  --out=data/results.csv --env=data/environment.txt

echo "Done. Results in data/results.csv"
