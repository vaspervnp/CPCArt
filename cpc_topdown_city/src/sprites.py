"""Top-down cars and pedestrians (CPC Mode 0), drawn from simple geometry per heading.

Sprites use pen 0 as transparent (mask), like the cpc_heroine pack, so the darkest visible
pen is 1 (dark blue). Headings: N NE E SE S SW W NW (clockwise from north). SW, W and NW are
exact horizontal mirrors of SE, E and NE, so an engine can store 5 headings and flip.
Light comes from the top-left, as on the tiles.
"""
import math
from cpcgfx import PEN, TileBank

DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
MIRROR = {'SW': 'SE', 'W': 'E', 'NW': 'NE'}
LIGHT = (-math.sqrt(0.5), -math.sqrt(0.5))       # towards the light (top-left)


def heading(d):
    phi = math.radians(45 * DIRS.index(d))
    f = (math.sin(phi), -math.cos(phi))           # forward, screen coords (v grows down)
    r = (math.cos(phi), math.sin(phi))            # right of the driver
    return f, r


def mirror(frame):
    return [row[::-1] for row in frame]


def render(w_px, h_rows, cx, cy, fn):
    """fn(u, v) -> letter or None, u/v visual units relative to (cx, cy)."""
    out = []
    for row in range(h_rows):
        line = []
        for px in range(w_px):
            c = fn(2 * px + 1 - cx, row + 0.5 - cy)
            line.append(PEN[c] if c else 0)
        out.append(line)
    return out


# ---------------------------------------------------------------- cars

CAR_W, CAR_H = 8, 16            # frame: one tile
HALF_L, HALF_W = 7.0, 4.0       # car is 14 x 8 visual units (lanes are ~10)

CARS = {
    # body, lit side, shaded side, glass, glass glint, sections along the car (front -> back)
    'sedan':  dict(body='R', lit='i', dark='r', glass='b', glint='s', lights=('c', 'n'),
                   parts=[(4.0, 'hood'), (1.5, 'wind'), (-2.5, 'roof'), (-4.5, 'rear'), (-9, 'trunk')]),
    'taxi':   dict(body='y', lit='c', dark='o', glass='b', glint='s', lights=('w', 'R'),
                   parts=[(4.0, 'hood'), (1.5, 'wind'), (-2.5, 'roof'), (-4.5, 'rear'), (-9, 'trunk')],
                   sign=True),
    'police': dict(body='w', lit='w', dark='p', glass='b', glint='s', lights=('c', 'R'),
                   parts=[(4.0, 'hood2'), (1.5, 'wind'), (-2.5, 'roof'), (-4.5, 'rear'), (-9, 'trunk2')],
                   bar=True),
    'sports': dict(body='l', lit='c', dark='v', glass='b', glint='s', lights=('c', 'R'),
                   parts=[(2.0, 'hood'), (-0.5, 'wind'), (-3.0, 'roof'), (-9, 'deck')], stripe='w'),
    'van':    dict(body='c', lit='w', dark='o', glass='b', glint='s', lights=('w', 'R'),
                   parts=[(4.5, 'hood'), (3.0, 'wind'), (-9, 'box')]),
    'wreck':  dict(body='b', lit='g', dark='b', glass='b', glint='b', lights=('b', 'b'),
                   parts=[(4.0, 'hood'), (1.5, 'wind'), (-2.5, 'roof'), (-4.5, 'rear'), (-9, 'trunk')],
                   burnt=True),
}


def car_frame(model, d, phase=0):
    m = CARS[model]
    f, r = heading(d)
    cx = 7 if d in ('E', 'W') else 8              # 7 px long when horizontal, 4 px wide when vertical

    def fn(x, y):
        a = x * f[0] + y * f[1]                   # along the car, + = front
        b = x * r[0] + y * r[1]                   # across, + = driver's right
        if abs(a) > HALF_L or abs(b) > HALF_W:
            return None
        rr = 1.6                                  # rounded corners
        ca, cb = abs(a) - (HALF_L - rr), abs(b) - (HALF_W - rr)
        if ca > 0 and cb > 0 and math.hypot(ca, cb) > rr:
            return None
        # outward normal of the nearest edge, in screen space -> lit / shaded rim
        if HALF_L - abs(a) < HALF_W - abs(b):
            n = (f[0] * math.copysign(1, a), f[1] * math.copysign(1, a))
            edge = HALF_L - abs(a)
        else:
            n = (r[0] * math.copysign(1, b), r[1] * math.copysign(1, b))
            edge = HALF_W - abs(b)
        facing = n[0] * LIGHT[0] + n[1] * LIGHT[1]
        rim = edge < 1.3
        # lamps at the very front and back
        if a > HALF_L - 1.2 and 1.2 < abs(b) < 3.4:
            return m['lights'][0]
        if a < -HALF_L + 1.2 and 1.2 < abs(b) < 3.4:
            return m['lights'][1]
        part = next(p for lim, p in m['parts'] if a >= lim)
        inner = abs(b) < HALF_W - 1.0
        if m.get('burnt') and (int(a * 1.7 + b * 2.3 + 40) % 5 == 0):
            return 'o'
        if part in ('wind', 'rear') and inner:
            return m['glint'] if b < -0.5 and part == 'wind' else m['glass']
        if m.get('bar') and -1.0 <= a < 0.6 and inner:
            left = b < 0
            return ('R' if left else 's') if phase == 0 else ('s' if left else 'R')
        if m.get('sign') and -1.4 <= a < 0.2 and abs(b) < 1.6:
            return 'w'
        if m.get('stripe') and abs(b) < 1.0 and part in ('hood', 'roof', 'deck'):
            return m['stripe']
        if part in ('hood2', 'trunk2'):
            return 'b' if not rim else ('g' if facing > 0.3 else 'b')
        if part == 'box' and inner and int(a + 20) % 3 == 0:
            return m['dark']                      # roof ribs on the van
        if rim:
            if facing > 0.3:
                return m['lit']
            if facing < -0.3:
                return m['dark']
        if part == 'roof':
            return m['lit'] if m['lit'] != m['body'] and a > -1.0 and b < -1.5 else m['body']
        return m['body']
    return render(CAR_W, CAR_H, cx, 8, fn)


def car_frames(model, phase=0):
    out = {}
    for d in DIRS:
        out[d] = mirror(out[MIRROR[d]]) if d in MIRROR else car_frame(model, d, phase)
    return out


# ---------------------------------------------------------------- pedestrians

PED_W, PED_H = 4, 8             # frame: 8 x 8 visual units

PEDS = {
    # hair, skin, shirt, trousers, shoes
    'suit':    dict(H='o', F='i', S='b', P='b', B='b', tie='w'),
    'dress':   dict(H='n', F='i', S='R', P='R', B='r'),
    'tourist': dict(H='c', F='i', S='y', P='s', B='b'),
    'punk':    dict(H='l', F='i', S='b', P='t', B='b'),
    'cop':     dict(H='s', F='i', S='s', P='b', B='b'),
}


def _capsule(pa, pb, pc, rad):
    """distance test for a segment pb->pc (points in (a, b) space)."""
    (a, b), (a1, b1), (a2, b2) = pa, pb, pc
    da, db = a2 - a1, b2 - b1
    L = da * da + db * db
    t = 0 if L == 0 else max(0, min(1, ((a - a1) * da + (b - b1) * db) / L))
    return math.hypot(a - (a1 + t * da), b - (b1 + t * db)) < rad


def ped_frame(kind, d, step):
    """step: -1, 0, +1 (left foot forward / standing / right foot forward) or 'down'."""
    c = PEDS[kind]
    f, r = heading(d)
    swing = 2.2 * step if step != 'down' else 0

    def fn(x, y):
        a = x * f[0] + y * f[1]
        b = x * r[0] + y * r[1]
        if step == 'down':                        # lying on its back, head forward
            if math.hypot(a - 2.6, b) < 1.6:
                return c['H']
            if abs(b) < 2.4 and -1.6 < a < 1.4:
                return c['S']
            if abs(b) < 1.8 and -3.8 < a <= -1.6:
                return c['P']
            if abs(abs(b) - 3.0) < 0.9 and -0.5 < a < 1.6:
                return c['F']
            return None
        # head (hair, with a sliver of face at the front)
        hd = math.hypot(a - 0.4, b)
        if hd < 1.9:
            return c['F'] if a > 1.5 else c['H']
        # arms swing opposite to the legs
        for side in (-1, 1):
            hand = (-swing * side * 0.8, 3.1 * side)
            if _capsule((a, b), (0, 2.8 * side), hand, 0.95):
                return c['F'] if math.hypot(a - hand[0], b - hand[1]) < 0.9 and step else c['S']
        # shoulders
        if (a / 1.7) ** 2 + (b / 3.4) ** 2 < 1:
            if c.get('tie') and abs(b) < 0.7 and a > 0.3:
                return c['tie']
            return c['S']
        # legs and shoes
        for side in (-1, 1):
            foot = (swing * side, 1.3 * side)
            if step and math.hypot(a - foot[0], b - foot[1]) < 1.0:
                return c['B']
            if step and _capsule((a, b), (0, 1.1 * side), foot, 0.8):
                return c['P']
        return None
    return render(PED_W, PED_H, 4, 4, fn)


def ped_frames(kind):
    """{dir: [left-forward, stand, right-forward]} and 'down'."""
    out = {}
    for d in DIRS:
        if d in MIRROR:
            out[d] = [mirror(fr) for fr in out[MIRROR[d]]]
        else:
            out[d] = [ped_frame(kind, d, s) for s in (-1, 0, 1)]
    return out, ped_frame(kind, 'S', 'down')
