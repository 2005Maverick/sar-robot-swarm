# Search-and-Rescue Robot Swarm with Reactive Behaviours

A swarm of e-puck robots explores a collapsed-building arena in Webots, finds victims that
carry short-range radio beacons, shares what it found over radio, and returns to the home
base. Each robot runs a layered (subsumption) reactive controller:

| Priority | Behaviour | Trigger | Action |
|---|---|---|---|
| 1 | DONE | all victims known and inside home base | stop |
| 2 | AVOID | proximity sensor > 80 | turn away, then drive straight briefly |
| 3 | HOME | all victims known | steer to home with GPS + IMU yaw |
| 4 | SEEK | beacon of an unknown victim heard | steer to beacon; found at < 0.12 m |
| 5 | CHECKIN | method B, no news for 120 s | drive home to hear the robots parked there |
| 6 | WANDER | otherwise | random curved walk |

Two methods are compared:

* **A — no communication:** every robot must find all victims itself.
* **B — radio sharing:** found victims are broadcast and re-broadcast every second (gossip,
  0.7 m radio range), so robots skip victims the team already knows. A robot that has heard
  nothing new for 120 s drives home to check in, because robots that know everything park
  there and their radio does not reach the rest of the arena.

## Requirements

* Webots R2025a (https://cyberbotics.com). The world loads its robot and object models from
  the Webots GitHub, so the first time you open it you need an internet connection.
* Python 3.11 on `PATH` (Webots runs the controllers with `python`), plus:

```bash
pip install -r requirements.txt
```

## Run the demo

1. Check `run_config.json` is `{"method": "B", "n_robots": 4, "p_loss": 0.0, "seed": 1, "batch": false}`.
2. Open `worlds/sar_arena.wbt` in Webots and press Run. Victims turn green when found; when
   every robot is home the simulation pauses and the console prints the result.

Use `"method": "A"` to show the no-communication swarm (it runs to the 600 s limit), then
Reload World. A demo (`"batch": false`) never writes to `results/`.

## Run the experiments

```bash
python experiments/run_experiments.py --seeds 10
python analysis/plot_results.py
python -m pytest
```

The first command runs 6 configurations × 10 seeds headless (about 30 s per run) and
**appends** to `results/runs.csv`, so delete that file first to start over. `--method B` runs
one method only; `--start-seed 6` adds seeds without rerunning earlier ones; `--webots PATH`
points at Webots if it is not found. The second command writes `report/figures/*.png` and
`report/tables/*.tex`. Runs are deterministic: the same seed gives the same result.

The bundled results come from these commands. The files `results/runs_before_fix.csv` and
`results/trace_B_4_0.0_s9_before_fix.csv` are the method B runs from before the check-in
behaviour was added (see `report/figures/fig_failure.png`).

## Files

| Path | Purpose |
|---|---|
| `worlds/sar_arena.wbt` | 2 m × 2 m arena, walls, rubble, 4 victims, 4 e-pucks, supervisor |
| `controllers/swarm_robot/behaviours.py` | behaviour layers and arbitration (pure Python) |
| `controllers/swarm_robot/comms.py` | `FOUND,id,x,y` message format |
| `controllers/swarm_robot/swarm_robot.py` | e-puck controller: sensors, radio, motors |
| `controllers/victim_beacon/victim_beacon.py` | victim beacon (channel 1, 0.3 m range) |
| `controllers/sar_supervisor/` | run setup, metrics, CSV logging |
| `experiments/run_experiments.py` | batch runner |
| `analysis/plot_results.py` | figures and LaTeX tables |
| `results/` | `runs.csv` (one row per run) and robot paths `trace_*.csv` |
| `run_config.json` | which method, robots, loss and seed the world runs |
| `tests/` | unit tests for behaviours, messages and metrics |
| `report/` | LaTeX report (Overleaf template) |

## Scope

This is a Webots simulation. The Python test suite exercises the reactive controller without Webots.

## Arena layout and configuration

The simulation uses a 2 m by 2 m search-and-rescue arena.
Walls and rubble create obstacles that the robots must navigate around.
Four victims are placed in the arena, each with a short-range radio beacon.
Four e-puck robots explore the environment and search for these victims.
The home base is centred at (-0.8, -0.8) metres.
A robot counts as home when it is within 0.2 metres of that centre.
The run_config.json file selects method A or B and the number of robots.
It also sets radio packet loss, the random seed, and whether the run uses batch mode.
