from comms import encode_found, parse
from metrics import Metrics

CFG = {"method": "B", "n_robots": 4, "p_loss": 0.0, "seed": 1}


def test_round_trip():
    assert parse(encode_found(3, 0.25, -0.5)) == (3, 0.25, -0.5)


def test_parse_rejects_garbage():
    for bad in ["junk", "", "FOUND,x,1,2", "FOUND,1,2", "HELLO,1,2,3"]:
        assert parse(bad) is None


def test_first_found_time_kept():
    m = Metrics(n_victims=2)
    m.update(1.0, [(0, 0)], {0: {1}})
    m.update(2.0, [(0, 0)], {0: {1}, 1: {1}})
    assert m.first_found[1] == 1.0


def test_t_all_found():
    m = Metrics(n_victims=2)
    m.update(1.0, [(0, 0)], {0: {0}})
    m.update(5.0, [(0, 0)], {0: {0, 1}})
    row = m.row(CFG, 9.0, True)
    assert row["t_all_found"] == 5.0 and row["found_times"] == "1.00;5.00"


def test_coverage_counts_distinct_cells():
    m = Metrics(n_victims=1, grid=20, size=2.0)
    m.update(0.0, [(0.01, 0.01), (0.02, 0.02)], {})   # same cell
    m.update(0.1, [(-0.95, -0.95)], {})               # another cell
    assert m.row(CFG, 1.0, False)["coverage_pct"] == 2 / 400 * 100


def test_near_collision_counted_once_per_encounter():
    m = Metrics(n_victims=1)
    for t in range(5):
        m.update(t, [(0, 0), (0.05, 0)], {})          # stays close: one event
    m.update(5, [(0, 0), (0.5, 0)], {})               # separate
    m.update(6, [(0, 0), (0.05, 0)], {})              # close again: second event
    assert m.row(CFG, 7, False)["near_collisions"] == 2


def test_row_on_timeout():
    m = Metrics(n_victims=4)
    row = m.row(CFG, 600.0, False)
    assert row["completed"] == 0 and row["t_mission"] == 600.0
    assert row["t_all_found"] == "" and row["victims_found"] == 0
