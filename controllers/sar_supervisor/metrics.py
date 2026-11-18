"""Mission metrics collected by the supervisor (no Webots imports, unit-tested)."""
import itertools
import math

NEAR_DIST = 0.08   # robot centres closer than this count as a near collision (m)

FIELDS = ["method", "n_robots", "p_loss", "seed", "victims_found", "t_all_found",
          "t_mission", "completed", "coverage_pct", "near_collisions", "found_times"]


class Metrics:
    def __init__(self, n_victims, grid=20, size=2.0):
        self.n_victims = n_victims
        self.grid = grid
        self.size = size
        self.first_found = {}      # victim id -> first time any robot found it
        self.cells = set()
        self.close_pairs = set()
        self.near_collisions = 0

    def _cell(self, x, y):
        k = lambda v: min(self.grid - 1, max(0, int((v + self.size / 2) / self.size * self.grid)))
        return k(x), k(y)

    def update(self, t, robot_xy, found):
        """robot_xy: list of (x, y); found: robot index -> set of victim ids it knows it found."""
        for ids in found.values():
            for vid in ids:
                self.first_found.setdefault(vid, t)
        for x, y in robot_xy:
            self.cells.add(self._cell(x, y))
        for i, j in itertools.combinations(range(len(robot_xy)), 2):
            close = math.dist(robot_xy[i], robot_xy[j]) < NEAR_DIST
            if close and (i, j) not in self.close_pairs:
                self.near_collisions += 1
                self.close_pairs.add((i, j))
            elif not close:
                self.close_pairs.discard((i, j))

    def row(self, config, t_end, all_home):
        all_found = len(self.first_found) == self.n_victims
        return {
            "method": config["method"],
            "n_robots": config["n_robots"],
            "p_loss": config["p_loss"],
            "seed": config["seed"],
            "victims_found": len(self.first_found),
            "t_all_found": round(max(self.first_found.values()), 2) if all_found else "",
            "t_mission": round(t_end, 2),
            "completed": int(all_home),
            "coverage_pct": round(len(self.cells) / self.grid ** 2 * 100, 2),
            "near_collisions": self.near_collisions,
            "found_times": ";".join(f"{t:.2f}" for t in sorted(self.first_found.values())),
        }
