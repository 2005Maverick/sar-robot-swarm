import math
import random

from behaviours import HOME, MAX_SPEED, decide

CLEAR = [60.0] * 8
FAR_POSE = (0.5, 0.5, 0.0)


def run(ps=CLEAR, victim=None, all_known=False, pose=FAR_POSE, state=None, check_in=False):
    return decide(ps, victim, all_known, pose, random.Random(1), {} if state is None else state,
                  check_in=check_in)


def test_front_obstacle_triggers_avoid():
    ps = CLEAR.copy()
    ps[0] = ps[7] = 300.0
    name, _, _ = run(ps=ps)
    assert name == "AVOID"


def test_avoid_turns_consistently():
    state = {}
    ps = CLEAR.copy()
    ps[0] = 300.0  # obstacle front-right
    _, l1, r1 = run(ps=ps, state=state)
    ps = CLEAR.copy()
    ps[7] = 400.0  # now front-left reads higher, but we keep turning the same way
    _, l2, r2 = run(ps=ps, state=state)
    assert (r1 - l1) > 0 and (r2 - l2) > 0


def test_avoid_beats_seek():
    ps = CLEAR.copy()
    ps[1] = 300.0
    name, _, _ = run(ps=ps, victim=(0.0, 0.3))
    assert name == "AVOID"


def test_beacon_ahead_seeks_straight():
    name, l, r = run(victim=(0.0, 0.3))
    assert name == "SEEK"
    assert abs(l - r) < 1e-6 and l > 0


def test_beacon_left_turns_left():
    name, l, r = run(victim=(math.radians(40), 0.3))
    assert name == "SEEK" and r > l


def test_all_known_goes_home():
    name, _, _ = run(all_known=True)
    assert name == "HOME"


def test_home_reached_stops():
    pose = (HOME[0] + 0.05, HOME[1], 1.0)
    ps = CLEAR.copy()
    ps[0] = 500.0  # a neighbour parked next to us must not wake us up
    assert run(ps=ps, all_known=True, pose=pose) == ("DONE", 0.0, 0.0)


def test_check_in_drives_home():
    name, _, _ = run(check_in=True)
    assert name == "CHECKIN"


def test_seek_beats_check_in():
    name, _, _ = run(victim=(0.0, 0.3), check_in=True)
    assert name == "SEEK"


def test_all_known_beats_check_in():
    name, _, _ = run(all_known=True, check_in=True)
    assert name == "HOME"


def test_check_in_at_home_does_not_stop():
    pose = (HOME[0] + 0.05, HOME[1], 1.0)
    name, _, _ = run(pose=pose, check_in=True)
    assert name != "DONE"


def test_wander_speeds_in_range():
    state = {}
    rng = random.Random(3)
    for _ in range(300):
        name, l, r = decide(CLEAR, None, False, FAR_POSE, rng, state)
        assert name == "WANDER"
        assert -MAX_SPEED <= l <= MAX_SPEED and -MAX_SPEED <= r <= MAX_SPEED
