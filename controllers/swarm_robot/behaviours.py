"""Reactive behaviour layer for one rescue robot (subsumption-style arbitration).

Layers are checked from highest to lowest priority and the first one that
wants control wins:

    DONE    - at home after every victim is known: stop
    AVOID   - an obstacle is close: turn away (keeps one turn direction)
    HOME    - every victim is known: drive to the home base
    SEEK    - a beacon of an unknown victim is heard: drive to it
    CHECKIN - no news for a while: drive home to hear the robots parked there
    WANDER  - otherwise explore with a slowly changing random curve

This module has no Webots imports so it can be unit-tested on its own.
"""
import math

MAX_SPEED = 6.28          # e-puck wheel limit (rad/s)
PS_THRESHOLD = 80.0       # proximity value meaning "obstacle within ~6.5 cm"
HOME = (-0.8, -0.8)       # home base centre (m)
HOME_RADIUS = 0.2         # robot counts as home inside this radius (m)
ESCAPE_STEPS = 12         # steps of straight driving after an avoid turn
TURN_GAIN = 4.0           # P gain from heading error (rad) to wheel speed difference

RIGHT_SENSORS = (0, 1, 2)
LEFT_SENSORS = (5, 6, 7)


def _clip(v):
    return max(-MAX_SPEED, min(MAX_SPEED, v))


def wrap_angle(a):
    return math.atan2(math.sin(a), math.cos(a))


def steer(bearing):
    """Wheel speeds that drive forward while turning toward `bearing` (rad, + = left)."""
    base = 0.0 if abs(bearing) > math.pi / 2 else 0.8 * MAX_SPEED
    turn = TURN_GAIN * bearing
    return _clip(base - turn), _clip(base + turn)


def _avoid(ps, state):
    right = max(ps[i] for i in RIGHT_SENSORS)
    left = max(ps[i] for i in LEFT_SENSORS)
    if max(left, right) < PS_THRESHOLD:
        state.pop("avoid_dir", None)
        return None
    if "avoid_dir" not in state:
        state["avoid_dir"] = 1 if right >= left else -1   # +1 = turn left
    state["escape"] = ESCAPE_STEPS
    d = state["avoid_dir"]
    return -0.5 * MAX_SPEED * d, 0.5 * MAX_SPEED * d


def _wander(rng, state):
    if state.get("wander_left", 0) <= 0:
        state["wander_bias"] = rng.uniform(-0.3, 0.3) * MAX_SPEED
        state["wander_left"] = rng.randint(40, 120)
    state["wander_left"] -= 1
    base, bias = 0.7 * MAX_SPEED, state["wander_bias"]
    return _clip(base - bias), _clip(base + bias)


def decide(ps, victim, all_known, pose, rng, state, check_in=False):
    """Pick the active behaviour and wheel speeds for one control step.

    ps        -- 8 proximity readings (ps0..ps7)
    victim    -- (bearing_rad, distance_m) of the nearest unknown beacon, or None
    all_known -- True when this robot believes every victim has been found
    pose      -- (x, y, yaw) from GPS and inertial unit
    rng       -- random.Random owned by this robot
    state     -- dict kept between calls by the caller
    check_in  -- True when the caller wants the robot to visit home for news
    """
    x, y, yaw = pose
    to_home = math.hypot(HOME[0] - x, HOME[1] - y)
    if all_known and to_home < HOME_RADIUS:
        return "DONE", 0.0, 0.0

    speeds = _avoid(ps, state)
    if speeds:
        return ("AVOID",) + speeds
    if state.get("escape", 0) > 0:
        state["escape"] -= 1
        return "AVOID", 0.7 * MAX_SPEED, 0.7 * MAX_SPEED

    home_bearing = wrap_angle(math.atan2(HOME[1] - y, HOME[0] - x) - yaw)
    if all_known:
        return ("HOME",) + steer(home_bearing)
    if victim is not None:
        return ("SEEK",) + steer(victim[0])
    if check_in:
        return ("CHECKIN",) + steer(home_bearing)
    return ("WANDER",) + _wander(rng, state)
