"""Top-down cars and pedestrians (CPC Mode 0), hand-drawn templates recoloured per model.

Sprites use pen 0 as transparent (mask), like the cpc_heroine pack, so the darkest visible
pen is 1 (dark blue). Headings: N NE E SE S SW W NW (clockwise from north). SW, W and NW are
exact horizontal mirrors of SE, E and NE, so an engine can keep 5 headings and flip.
Light comes from the top-left, as on the tiles.

Template letters (cars): L lit side, D shaded side, B body, O hood/trunk, W glass,
w glass glint, H headlight, T tail light, X/Y roof item (left/right half), Z stripe.
Pedestrians (slight 3/4 view, 4 headings): H hair, F skin, S shirt, A arm/sleeve,
P trousers/skirt, G lower legs (rows 5-6), B shoes, r blood.
"""
from cpcgfx import PEN

DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
MIRROR = {'SW': 'SE', 'W': 'E', 'NW': 'NE'}


def grid(text):
    rows = [line.strip() for line in text.strip('\n').splitlines()]
    assert len({len(r) for r in rows}) == 1, rows
    return rows


def hflip(rows):
    return [r[::-1] for r in rows]


def vflip(rows):
    return rows[::-1]


def swap(rows, pairs):
    table = {}
    for a, b in pairs:
        table[a], table[b] = b, a
    return [''.join(table.get(c, c) for c in r) for r in rows]


# ---------------------------------------------------------------- cars
# 8 x 16 frames (one tile). The car is 14 x 8 visual units: 4 px x 14 rows facing N/S,
# 7 px x 8 rows facing E/W, and fills the frame diagonally.

CAR_W, CAR_H = 8, 16
_E = '........'

SHAPES = {
    'sedan': {
        'N': """
........
...LB...
..HOOH..
..LOOD..
..LOOD..
..LwWD..
..LWWD..
..LBBD..
..LXYD..
..LBBD..
..LWWD..
..LOOD..
..LOOD..
..TOOT..
...DD...
........""",
        'NE': """
........
....LH..
....LO..
...LOOO.
...LwOO.
..LBWOOH
..LBBWOD
.LBXBWD.
.LBBYBD.
LOWBBD..
TOWBBD..
.OOWD...
.OOWD...
..OD....
..TD....
........""",
        'E': """
........
........
........
........
.LLLLL..
TOBBBOH.
OOWXwOO.
OOWXWOO.
OOWYWOO.
OOWYWOO.
TOBBBOH.
.DDDDD..
........
........
........
........""",
    },
    'sports': {
        'N': """
........
...LB...
..HZZH..
..LZZD..
..LZZD..
..LBBD..
..LwWD..
..LWWD..
..LZZD..
..LZZD..
..LBBD..
..LZZD..
..LZZD..
..TBBT..
...DD...
........""",
        'NE': """
........
....LH..
....LB..
...LBBZ.
...LBZB.
..LBBZBH
..LwZBBD
.LBWWBD.
.LBZWBD.
LBBZBD..
TBZBBD..
.BZBD...
.ZBBD...
..BD....
..TD....
........""",
        'E': """
........
........
........
........
.LLLLL..
TBBBBBH.
BBBwBBB.
ZZZWZZZ.
ZZZWZZZ.
BBBWBBB.
TBBBBBH.
.DDDDD..
........
........
........
........""",
    },
    'van': {
        'N': """
........
...LB...
..HBBH..
..LBBD..
..LwWD..
..LWWD..
..LBBD..
..LDDD..
..LBBD..
..LBBD..
..LDDD..
..LBBD..
..LBBD..
..TBBT..
...DD...
........""",
        'NE': """
........
....LH..
....LB..
...LwBB.
...LWBB.
..LBBWBH
..LDBWBD
.LBDBBD.
.LBBDBD.
LBDBBD..
TBDBBD..
.BBDD...
.BBBD...
..BD....
..TD....
........""",
        'E': """
........
........
........
........
.LLLLL..
TBBBBBH.
BDBDBwB.
BDBDBWB.
BDBDBWB.
BDBDBWB.
TBBBBBH.
.DDDDD..
........
........
........
........""",
    },
}


def car_shape(shape):
    """All 8 headings of a template shape (letters)."""
    t = {k: grid(v) for k, v in SHAPES[shape].items()}
    n, ne, e = t['N'], t['NE'], t['E']
    # S: turn N around (rear on top), keep the lit side left and lit top rim
    s = vflip(n)
    s[1], s[14] = n[1], n[14]
    s = [r.replace('w', 'W') for r in s]
    s[10] = s[10][:3] + 'w' + s[10][4:] if s[10][3] == 'W' else s[10]
    # SE: mirror NE top-to-bottom, then relight (upper edges lit, lower edges shaded)
    se = swap(vflip(ne), [('L', 'D')])
    out = {'N': n, 'NE': ne, 'E': e, 'SE': se, 'S': s}
    for d, src in MIRROR.items():
        out[d] = hflip(out[src])
    return out


CARS = {
    # model: shape, colours per template letter
    'sedan':  ('sedan',  dict(B='R', L='i', D='r', O='R', W='b', w='s', H='c', T='n', X='R', Y='R')),
    'taxi':   ('sedan',  dict(B='y', L='c', D='o', O='y', W='b', w='s', H='w', T='R', X='w', Y='w')),
    'police': ('sedan',  dict(B='w', L='w', D='p', O='b', W='b', w='s', H='c', T='R', X='R', Y='s')),
    'sports': ('sports', dict(B='l', L='c', D='v', Z='w', W='b', w='s', H='c', T='R')),
    'van':    ('van',    dict(B='c', L='w', D='o', W='b', w='s', H='w', T='R')),
    'wreck':  ('sedan',  dict(B='b', L='g', D='b', O='b', W='b', w='b', H='b', T='b', X='o', Y='r')),
}


def colour(rows, pal, rust=False):
    out = []
    for j, r in enumerate(rows):
        line = []
        for i, c in enumerate(r):
            if c == '.':
                line.append(0)
                continue
            ch = pal[c]
            if rust and c in 'BO' and (i * 3 + j * 5) % 7 == 0:
                ch = 'o'                                # scorched paint on the wreck
            line.append(PEN[ch])
        out.append(line)
    return out


def car_frames(model, flash=False):
    """{heading: frame}. flash=True swaps the police light bar colours."""
    shape, pal = CARS[model]
    pal = dict(pal)
    if flash:
        pal['X'], pal['Y'] = pal['Y'], pal['X']
    frames = car_shape(shape)
    return {d: colour(frames[d], pal, rust=(model == 'wreck')) for d in DIRS}


# ---------------------------------------------------------------- pedestrians
# 4 x 8 frames (8 x 8 visual units, a little under a car's width). Straight top-down people
# are unreadable blobs at this size, so pedestrians are drawn in the same slight 3/4 view as
# the building fronts: head on top, feet at the bottom (anchor = feet). 4 headings, W is the
# mirror of E; diagonal movement uses the E/W frames. Walk cycle per heading:
# [step, stand, other step], played ping-pong.

PED_W, PED_H = 4, 8
PED_DIRS = ['N', 'E', 'S', 'W']

PED_ART = {
    'S': ["""
.HH.
.FF.
ASSA
ASSA
FPPF
.PP.
.PB.
.B..""", """
.HH.
.FF.
ASSA
ASSA
FPPF
.PP.
.PP.
.BB.""", None],
    'N': ["""
.HH.
.HH.
ASSA
ASSA
FPPF
.PP.
.PB.
.B..""", """
.HH.
.HH.
ASSA
ASSA
FPPF
.PP.
.PP.
.BB.""", None],
    'E': ["""
.HH.
.HF.
.SS.
.SA.
.PPF
.PP.
P..P
B..B""", """
.HH.
.HF.
.SS.
.AS.
.FP.
.PP.
.PP.
.BB.""", """
.HH.
.HF.
.SS.
ASS.
FPP.
.PP.
P..P
B..B"""],
}

DOWN = grid("""
....
....
....
....
..r.
HSSP
FASB
rrr.""")

PEDS = {
    # hair, skin, shirt, arms, trousers (or skirt), lower legs, shoes
    'suit':    dict(H='o', F='i', S='b', A='b', P='b', G='b', B='b'),
    'dress':   dict(H='n', F='i', S='R', A='i', P='R', G='i', B='r'),
    'tourist': dict(H='c', F='i', S='y', A='i', P='s', G='i', B='b'),
    'punk':    dict(H='l', F='i', S='b', A='b', P='t', G='t', B='b'),
    'cop':     dict(H='b', F='i', S='s', A='s', P='b', G='b', B='b'),
}


def ped_shape():
    """{heading: [step, stand, other step]} as letters."""
    out = {}
    for d in ('N', 'S', 'E'):
        a, s_, b = PED_ART[d]
        a, s_ = grid(a), grid(s_)
        b = grid(b) if b else hflip(a)            # front/back views: other step = mirror
        out[d] = [[r.replace('P', 'G') if j in (5, 6) else r for j, r in enumerate(f)]
                  for f in (a, s_, b)]
    out['W'] = [hflip(f) for f in out['E']]
    return out


def ped_frames(kind):
    pal = dict(PEDS[kind], r='r')
    shapes = ped_shape()
    walk = {d: [colour(f, pal) for f in shapes[d]] for d in PED_DIRS}
    return walk, colour(DOWN, pal)


# ---------------------------------------------------------------- sheets

class Sheet:
    """Frames of one size, grouped by tags (exported one row per tag)."""

    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.frames, self.names, self.durations, self.tags = [], [], [], []

    def add(self, tag, frames, names, ms, direction='forward'):
        a = len(self.frames)
        self.frames += frames
        self.names += names
        self.durations += [ms] * len(frames)
        self.tags.append((tag, a, len(self.frames) - 1, direction))

    def tag(self, name):
        for t, a, b, _ in self.tags:
            if t == name:
                return self.frames[a:b + 1]
        raise KeyError(name)


def car_sheet():
    sh = Sheet('cars_cpc_mode0', CAR_W, CAR_H)
    for model in CARS:
        for tag, flash in ((model, False), ('police_flash', True)) if model == 'police' else ((model, False),):
            f = car_frames(model, flash)
            sh.add(tag, [f[d] for d in DIRS], ['%s_%s' % (tag, d) for d in DIRS], 120)
    return sh


def ped_sheet():
    sh = Sheet('peds_cpc_mode0', PED_W, PED_H)
    for kind in PEDS:
        walk, down = ped_frames(kind)
        for d in PED_DIRS:
            sh.add('%s_%s' % (kind, d), walk[d], ['%s_%s_%d' % (kind, d, i) for i in range(3)],
                   160, 'pingpong')
        sh.add(kind + '_down', [down], [kind + '_down'], 160)
    return sh
