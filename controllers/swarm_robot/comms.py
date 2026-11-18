"""Radio message format shared by the rescue robots: FOUND,<victim_id>,<x>,<y>."""


def encode_found(vid, x, y):
    return f"FOUND,{vid},{x:.3f},{y:.3f}"


def parse(msg):
    """Return (victim_id, x, y) for a valid FOUND message, else None."""
    parts = msg.split(",")
    if len(parts) != 4 or parts[0] != "FOUND":
        return None
    try:
        return int(parts[1]), float(parts[2]), float(parts[3])
    except ValueError:
        return None
