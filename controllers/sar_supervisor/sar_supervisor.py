"""Supervisor: applies the run config, colours found victims, logs metrics, ends the run.

It only observes and records; the rescue robots never read anything from it.
"""
import csv
import json
import math
import os
import random

from controller import Supervisor

from metrics import FIELDS, Metrics

N_ROBOTS_MAX = 4
N_VICTIMS = 4
TIME_LIMIT = 600.0
FOUND_COLOUR = [0.1, 0.8, 0.1]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def main():
    sup = Supervisor()
    ts = int(sup.getBasicTimeStep())
    with open(os.path.join(ROOT, "run_config.json")) as f:
        cfg = json.load(f)

    robots = [sup.getFromDef(f"R{i}") for i in range(N_ROBOTS_MAX)]
    for r in robots[cfg["n_robots"]:]:
        r.remove()
    robots = robots[:cfg["n_robots"]]
    rng = random.Random(cfg["seed"])
    for r in robots:   # random start heading per seed
        r.getField("rotation").setSFRotation([0, 0, 1, rng.uniform(-math.pi, math.pi)])
    victim_colours = [sup.getFromDef(f"V{i}_COLOUR").getField("baseColor") for i in range(N_VICTIMS)]

    metrics = Metrics(N_VICTIMS)
    coloured = set()
    # only batch (experiment) runs write files, so a GUI demo never changes the results
    batch = cfg.get("batch", False)
    # robot paths of seed 1 are saved for the trajectory figures; {"trace": true} saves any seed
    trace = None
    if batch and (cfg["seed"] == 1 or cfg.get("trace")):
        os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
        name = f"trace_{cfg['method']}_{cfg['n_robots']}_{cfg['p_loss']}"
        name += ".csv" if cfg["seed"] == 1 else f"_s{cfg['seed']}.csv"
        trace = open(os.path.join(ROOT, "results", name), "w", newline="")
        trace.write("t,robot,x,y,state,known\n")
    print(f"run: {cfg}")
    step = 0
    while sup.step(ts) != -1:
        t = sup.getTime()
        step += 1
        data = [json.loads(r.getField("customData").getSFString() or "{}") for r in robots]
        found = {i: set(d.get("found", [])) for i, d in enumerate(data)}
        xy = [tuple(r.getPosition()[:2]) for r in robots]
        metrics.update(t, xy, found)
        # optional screenshots for the report: {"snapshots": [seconds, ...]}
        for s in cfg.get("snapshots", []):
            if abs(t - s) < ts / 2000:
                sup.exportImage(os.path.join(ROOT, "report", "figures", f"webots_t{int(s)}.png"), 95)
        if trace and step % 10 == 0:
            for i, (x, y) in enumerate(xy):
                trace.write(f"{t:.2f},{i},{x:.3f},{y:.3f},{data[i].get('state', '')},{data[i].get('known', 0)}\n")
        for vid in set(metrics.first_found) - coloured:
            victim_colours[vid].setSFColor(FOUND_COLOUR)
            coloured.add(vid)
            print(f"t={t:6.1f}s victim V{vid} found")

        all_home = bool(data) and all(d.get("state") == "DONE" for d in data)
        if all_home or t >= TIME_LIMIT:
            row = metrics.row(cfg, t, all_home)
            print("result:", row)
            if trace:
                trace.close()
            if batch:
                path = os.path.join(ROOT, "results", "runs.csv")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                new = not os.path.exists(path)
                with open(path, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=FIELDS)
                    if new:
                        w.writeheader()
                    w.writerow(row)
                sup.simulationQuit(0)
            else:
                sup.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
            break


main()
