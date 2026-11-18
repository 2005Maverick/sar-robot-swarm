"""Victim beacon: a static robot that keeps sending its ID on a short-range radio."""
from controller import Robot

robot = Robot()
ts = int(robot.getBasicTimeStep())
beacon = robot.getDevice("beacon")
vid = robot.getName()[1:]          # victims are named V0..V3

while robot.step(ts) != -1:
    beacon.send(vid)
