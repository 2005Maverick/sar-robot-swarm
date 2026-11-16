"""Turn results/runs.csv and results/trace_*.csv into report figures and a LaTeX table.

Usage:  python analysis/plot_results.py
"""
import csv
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "report", "figures")
TAB = os.path.join(ROOT, "report", "tables")
TIME_LIMIT = 600.0
COL = {"A": "#d95f02", "B": "#1b9e77"}
LABEL = {"A": "A: no communication", "B": "B: radio sharing"}

WALLS = [(0.0, -0.1, 0.02, 1.0), (-0.725, 0.3, 0.55, 0.02), (0.725, -0.2, 0.55, 0.02), (0.35, 0.45, 0.02, 0.4)]
BOXES = [(-0.35, 0.65), (0.6, 0.25), (-0.4, -0.35), (0.5, -0.55), (0.7, 0.6), (-0.75, 0.0)]
VICTIMS = [(-0.7, 0.75), (0.8, 0.85), (0.75, -0.75), (0.3, 0.0)]


def load_runs(path=os.path.join(RES, "runs.csv")):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["n_robots"] = int(r["n_robots"])
        r["p_loss"] = float(r["p_loss"])
        r["t_mission"] = float(r["t_mission"])
        r["completed"] = int(r["completed"])
        r["victims_found"] = int(r["victims_found"])
        r["coverage_pct"] = float(r["coverage_pct"])
        r["near_collisions"] = int(r["near_collisions"])
        # a run that never found every victim is scored at the time limit
        r["t_all_found"] = float(r["t_all_found"]) if r["t_all_found"] else TIME_LIMIT
        r["found_times"] = [float(t) for t in r["found_times"].split(";") if t]
    return rows


def group(rows, method, n, p_loss=0.0):
    return [r for r in rows if r["method"] == method and r["n_robots"] == n and r["p_loss"] == p_loss]


def mean_sd(vals):
    return st.mean(vals), (st.stdev(vals) if len(vals) > 1 else 0.0)


def fig_times(rows):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, key, title in zip(axes, ["t_all_found", "t_mission"],
                              ["Time until all victims found", "Mission time (all robots home)"]):
        for k, method in enumerate("AB"):
            xs, ms, sds = [], [], []
            for j, n in enumerate([2, 4]):
                m, sd = mean_sd([r[key] for r in group(rows, method, n)])
                xs.append(j + (k - 0.5) * 0.36)
                ms.append(m)
                sds.append(sd)
            ax.bar(xs, ms, 0.34, yerr=sds, capsize=4, color=COL[method], label=LABEL[method])
        ax.axhline(TIME_LIMIT, ls="--", c="grey", lw=1)
        ax.set_xticks([0, 1], ["2 robots", "4 robots"])
        ax.set_ylabel("simulated time (s)")
        ax.set_title(title, fontsize=10)
    axes[0].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_times.png"), dpi=200)


def fig_found_curve(rows):
    fig, ax = plt.subplots(figsize=(6, 3.6))
    grid = range(0, int(TIME_LIMIT) + 1, 5)
    for method, n, ls in [("A", 4, "-"), ("B", 4, "-"), ("A", 2, "--"), ("B", 2, "--")]:
        runs = group(rows, method, n)
        curve = [st.mean(sum(1 for ft in r["found_times"] if ft <= t) for r in runs) for t in grid]
        ax.plot(list(grid), curve, ls, color=COL[method], label=f"{method}, {n} robots")
    ax.set_xlabel("simulated time (s)")
    ax.set_ylabel(f"victims found (mean of {len(group(rows, 'B', 4))} runs)")
    ax.set_ylim(0, 4.2)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_found_curve.png"), dpi=200)


def fig_loss(rows):
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    losses = [0.0, 0.3, 0.6]
    stats = [mean_sd([r["t_mission"] for r in group(rows, "B", 4, p)]) for p in losses]
    ax.bar([f"{int(p * 100)}%" for p in losses], [s[0] for s in stats], yerr=[s[1] for s in stats],
           capsize=4, color=COL["B"])
    ref = st.mean(r["t_mission"] for r in group(rows, "A", 4))
    ax.axhline(ref, ls="--", c=COL["A"], label="A (no communication), 4 robots")
    ax.set_xlabel("radio message loss")
    ax.set_ylabel("mission time (s)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_loss.png"), dpi=200)


def draw_map(ax):
    ax.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False, lw=1.5))
    ax.add_patch(plt.Rectangle((-1, -1), 0.4, 0.4, color="#9ecae1", alpha=0.6))
    for x, y, sx, sy in WALLS:
        ax.add_patch(plt.Rectangle((x - sx / 2, y - sy / 2), sx, sy, color="#6b5d4f"))
    for x, y in BOXES:
        ax.add_patch(plt.Rectangle((x - 0.05, y - 0.05), 0.1, 0.1, color="#b08850"))
    for i, (x, y) in enumerate(VICTIMS):
        ax.add_patch(plt.Circle((x, y), 0.3, color="red", alpha=0.08))
        ax.plot(x, y, "o", color="red", ms=6)
        ax.text(x + 0.05, y + 0.05, f"V{i}", fontsize=7)
    ax.set_xlim(-1.02, 1.02)
    ax.set_ylim(-1.02, 1.02)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def fig_traces():
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.4))
    for ax, method in zip(axes, "AB"):
        draw_map(ax)
        path = os.path.join(RES, f"trace_{method}_4_0.0.csv")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            pts = list(csv.DictReader(f))
        for i, c in enumerate(["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]):
            p = [(float(q["x"]), float(q["y"])) for q in pts if q["robot"] == str(i)]
            ax.plot([a for a, _ in p], [b for _, b in p], lw=0.7, color=c, label=f"R{i}")
        ax.set_title(f"{LABEL[method]} (4 robots, seed 1)", fontsize=10)
    axes[1].legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_traces.png"), dpi=200)


def fig_failure():
    """B, 4 robots, seed 9 before and after the check-in fix: the news of the last victim
    stayed with the robots parked at home until the others came to ask."""
    panels = [("trace_B_4_0.0_s9_before_fix.csv", 419.68, "before fix: t = 420 s to 600 s"),
              ("trace_B_4_0.0_s9.csv", 200.0, "with check-in: t = 200 s to end")]
    if not all(os.path.exists(os.path.join(RES, p)) for p, _, _ in panels):
        return
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.6))
    for ax, (name, t0, title) in zip(axes, panels):
        with open(os.path.join(RES, name)) as f:
            pts = [q for q in csv.DictReader(f) if float(q["t"]) >= t0]
        draw_map(ax)
        ax.add_patch(plt.Circle((-0.63, -0.74), 0.7, fill=False, ls="--", color="#1b9e77", lw=1.2,
                                label="0.7 m radio range around home"))
        for i, c in enumerate(["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]):
            p = [(float(q["x"]), float(q["y"])) for q in pts if q["robot"] == str(i)]
            informed = any(q["known"] == "4" for q in pts if q["robot"] == str(i))
            ax.plot([a for a, _ in p], [b for _, b in p], lw=0.8, color=c, ls="-" if informed else ":",
                    label=f"R{i} " + ("told, went home" if informed else "never told"))
            ax.plot(*p[-1], "o", color=c, ms=5)
        ax.set_title(f"B, 4 robots, seed 9, {title}", fontsize=10)
        ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_failure.png"), dpi=200)


def fix_table():
    """Method B before and after the check-in fix (results/runs_before_fix.csv vs runs.csv)."""
    old_path = os.path.join(RES, "runs_before_fix.csv")
    if not os.path.exists(old_path):
        return
    old = [r for r in load_runs(old_path) if r["method"] == "B"]
    new = [r for r in load_runs() if r["method"] == "B"]
    lines = [r"\begin{tabular}{|l|c|c|c|c|}", r"\hline",
             r"\textbf{Config.} & \multicolumn{2}{c|}{\textbf{Mission (s)}} & "
             r"\multicolumn{2}{c|}{\textbf{Completed}} \\",
             r" & before & after & before & after \\ \hline"]
    for n, p in [(2, 0.0), (4, 0.0), (4, 0.3), (4, 0.6)]:
        a = [r for r in old if r["n_robots"] == n and r["p_loss"] == p]
        b = [r for r in new if r["n_robots"] == n and r["p_loss"] == p]
        if not a or not b:
            continue
        f = lambda g: "%.0f $\\pm$ %.0f" % mean_sd([r["t_mission"] for r in g])
        name = f"B, {n} robots" + (f", {int(p * 100)}\\% loss" if p else "")
        lines.append(f"{name} & {f(a)} & {f(b)} & {sum(r['completed'] for r in a)}/{len(a)} & "
                     f"{sum(r['completed'] for r in b)}/{len(b)} \\\\ \\hline")
    lines.append(r"\end{tabular}")
    with open(os.path.join(TAB, "checkin_fix.tex"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def fig_map():
    fig, ax = plt.subplots(figsize=(4.4, 4.4))
    draw_map(ax)
    for x, y in [(-0.88, -0.62), (-0.68, -0.62), (-0.62, -0.88), (-0.62, -0.72)]:
        ax.plot(x, y, "s", color="black", ms=4)
    ax.text(-0.98, -0.97, "home", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_map.png"), dpi=200)


def table(rows):
    lines = [r"\begin{tabular}{|l|c|c|c|c|c|c|}", r"\hline",
             r"\textbf{Config.} & \textbf{All found (s)} & \textbf{Mission (s)} & \textbf{Completed} & "
             r"\textbf{Victims} & \textbf{Coverage (\%)} & \textbf{Near coll.} \\ \hline"]
    for method, n, p in [("A", 2, 0.0), ("B", 2, 0.0), ("A", 4, 0.0), ("B", 4, 0.0), ("B", 4, 0.3), ("B", 4, 0.6)]:
        g = group(rows, method, n, p)
        if not g:
            continue
        f = lambda k: "%.0f $\\pm$ %.0f" % mean_sd([r[k] for r in g])
        name = f"{method}, {n} robots" + (f", {int(p * 100)}\\% loss" if p else "")
        lines.append(f"{name} & {f('t_all_found')} & {f('t_mission')} & "
                     f"{sum(r['completed'] for r in g)}/{len(g)} & "
                     f"{st.mean(r['victims_found'] for r in g):.1f} & "
                     f"{st.mean(r['coverage_pct'] for r in g):.0f} & "
                     f"{st.mean(r['near_collisions'] for r in g):.1f} \\\\ \\hline")
    lines.append(r"\end{tabular}")
    with open(os.path.join(TAB, "results.tex"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(TAB, exist_ok=True)
    fig_map()
    rows = load_runs()
    fig_times(rows)
    fig_found_curve(rows)
    fig_loss(rows)
    fig_traces()
    fig_failure()
    table(rows)
    fix_table()


if __name__ == "__main__":
    main()
