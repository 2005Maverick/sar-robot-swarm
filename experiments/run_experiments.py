"""Run every experiment configuration headless in Webots and collect results/runs.csv.

Usage:  python experiments/run_experiments.py [--seeds 5] [--start-seed 1] [--method A|B] [--webots PATH]
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "run_config.json")
RESULTS = os.path.join(ROOT, "results", "runs.csv")
WORLD = os.path.join(ROOT, "worlds", "sar_arena.wbt")
WIN_EXE = os.path.join("msys64", "mingw64", "bin", "webots.exe")
# usual Webots locations: WEBOTS_HOME, per-user and all-users Windows installs, then PATH
CANDIDATES = [os.path.join(os.environ.get("WEBOTS_HOME", ""), WIN_EXE),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Webots", WIN_EXE),
              os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Webots", WIN_EXE)]


def find_webots():
    for path in CANDIDATES:
        if os.path.isfile(path):
            return path
    return shutil.which("webots")

# (method, n_robots, p_loss): A = no communication, B = radio sharing
CONFIGS = [("A", 2, 0.0), ("A", 4, 0.0), ("B", 2, 0.0), ("B", 4, 0.0), ("B", 4, 0.3), ("B", 4, 0.6)]


def count_rows():
    if not os.path.exists(RESULTS):
        return 0
    with open(RESULTS) as f:
        return sum(1 for _ in csv.DictReader(f))


def run_one(webots, method, n, p_loss, seed):
    with open(CONFIG, "w") as f:
        json.dump({"method": method, "n_robots": n, "p_loss": p_loss, "seed": seed, "batch": True}, f)
    before = count_rows()
    cmd = [webots, "--batch", "--mode=fast", "--no-rendering", "--minimize", "--stdout", WORLD]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    except subprocess.TimeoutExpired:
        print("  webots timed out")
    return count_rows() > before


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5, help="last seed to run")
    ap.add_argument("--start-seed", type=int, default=1, help="first seed (to add runs to runs.csv)")
    ap.add_argument("--method", choices=["A", "B"], help="run only this method")
    ap.add_argument("--webots", default=find_webots(), help="path to the webots executable")
    args = ap.parse_args()
    if not args.webots:
        ap.error("Webots not found: install Webots R2025a or pass --webots PATH")
    try:
        for method, n, p_loss in CONFIGS:
            if args.method and method != args.method:
                continue
            for seed in range(args.start_seed, args.seeds + 1):
                t0 = time.time()
                ok = run_one(args.webots, method, n, p_loss, seed)
                print(f"{method} n={n} loss={p_loss} seed={seed}: {'ok' if ok else 'NO ROW'} "
                      f"({time.time() - t0:.0f}s)", flush=True)
    finally:   # leave the GUI demo config behind
        with open(CONFIG, "w") as f:
            json.dump({"method": "B", "n_robots": 4, "p_loss": 0.0, "seed": 1, "batch": False}, f)


if __name__ == "__main__":
    main()
