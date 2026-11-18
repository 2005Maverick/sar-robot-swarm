"""Rescue robot controller (e-puck): sensors -> behaviours.decide -> wheels, plus radio."""
import json
import math
import os
import random

from controller import Robot

from behaviours import HOME, decide
from comms import encode_found, parse

N_VICTIMS = 4
FOUND_DIST = 0.12        # a victim is "found" when its beacon is closer than this (m)
GOSSIP_PERIOD = 1.0      # seconds between re-broadcasts of everything this robot knows
CHECKIN_PERIOD = 120.0   # method B: with no news for this long, visit home to hear the robots there
CHECKIN_RADIUS = 0.3     # a check-in is done this close to home (well inside the 0.7 m radio range)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def load_config():
    with open(os.path.join(ROOT, "run_config.json")) as f:
        return json.load(f)


def read_string(rx):
    try:
        return rx.getString()
    except AttributeError:   # older Webots API
        return rx.getData().decode()


def main():
    robot = Robot()
    ts = int(robot.getBasicTimeStep())
    cfg = load_config()
    index = int(robot.getName()[1:])           # robots are named R0..R3
    rng = random.Random(cfg["seed"] * 100 + index)
    comm_on = cfg["method"] == "B"

    ps = [robot.getDevice(f"ps{i}") for i in range(8)]
    for s in ps:
        s.enable(ts)
    gps = robot.getDevice("gps")
    imu = robot.getDevice("imu")
    victim_rx = robot.getDevice("victim_rx")
    swarm_rx = robot.getDevice("swarm_rx")
    swarm_tx = robot.getDevice("swarm_tx")
    for d in (gps, imu, victim_rx, swarm_rx):
        d.enable(ts)
    left = robot.getDevice("left wheel motor")
    right = robot.getDevice("right wheel motor")
    for m in (left, right):
        m.setPosition(float("inf"))
        m.setVelocity(0.0)

    own_found = {}      # victim id -> (x, y) found by this robot
    known = set()       # every victim id this robot knows is found
    state = {}
    last_gossip = 0.0
    last_news = 0.0     # last time `known` grew, or the last check-in

    while robot.step(ts) != -1:
        t = robot.getTime()
        x, y = gps.getValues()[:2]
        yaw = imu.getRollPitchYaw()[2]
        n_known = len(known)

        # victim beacons: keep the strongest one we do not already know about
        victim = None
        while victim_rx.getQueueLength() > 0:
            vid = int(read_string(victim_rx))
            dist = 1.0 / math.sqrt(victim_rx.getSignalStrength())
            d = victim_rx.getEmitterDirection()
            victim_rx.nextPacket()
            if vid in known:
                continue
            if dist < FOUND_DIST:
                own_found[vid] = (x, y)
                known.add(vid)
                if comm_on:
                    swarm_tx.send(encode_found(vid, x, y))
            elif victim is None or dist < victim[1]:
                victim = (math.atan2(d[1], d[0]), dist)

        # team radio (each message may be lost with probability p_loss)
        while swarm_rx.getQueueLength() > 0:
            msg = parse(read_string(swarm_rx))
            swarm_rx.nextPacket()
            if comm_on and msg and rng.random() >= cfg["p_loss"]:
                known.add(msg[0])

        if comm_on and known and t - last_gossip >= GOSSIP_PERIOD:
            for vid in known:
                swarm_tx.send(encode_found(vid, x, y))
            last_gossip = t

        if len(known) > n_known:
            last_news = t
        if math.hypot(HOME[0] - x, HOME[1] - y) < CHECKIN_RADIUS:
            last_news = t
        check_in = comm_on and t - last_news > CHECKIN_PERIOD
        name, l, r = decide([s.getValue() for s in ps], victim,
                            len(known) == N_VICTIMS, (x, y, yaw), rng, state, check_in)
        left.setVelocity(l)
        right.setVelocity(r)
        robot.setCustomData(json.dumps({"found": sorted(own_found), "known": len(known),
                                        "state": name}))


main()
