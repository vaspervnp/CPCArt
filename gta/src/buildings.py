"""Top-down buildings (GTA1 style roofs) for a CPC Mode 0 city.

Every building is a roof (9-slice: any size >= 2x2 tiles, or a 2-row pitched roof) plus a
front wall row on its south side (3/4 view, like the camera sits a little to the south).
Light comes from the top-left: top/left parapets are lit, bottom/right in shade.
"""
import math
from cpcgfx import PEN, parse_art, blank, TileBank, TW, TH


def p(ch):
    return PEN[ch]


# ---------------------------------------------------------------- flat roofs

class FlatRoof:
    TOP = [(1, 'out'), (3, 'hi'), (5, 'shadow')]
    LEFT = [(2, 'out'), (4, 'hi'), (6, 'shadow')]
    RIGHT = [(2, 'out'), (4, 'lo')]
    BOTTOM = [(1, 'out'), (3, 'lo')]

    def __init__(self, name, out, hi, lo, shadow, fill, tex=None):
        self.name = name
        self.pens = {'out': p(out), 'hi': p(hi), 'lo': p(lo), 'shadow': p(shadow)}
        self.fill = p(fill)
        self.tex = tex or {}        # {(px,row): letter} texture inside the roof (tile periodic)

    def tile(self, top, left, right, bottom):
        img = blank(TW, TH)
        for row in range(TH):
            v = row + 0.5
            for px in range(TW):
                u = 2 * px + 1
                img[row][px] = self.pixel(px, row, u, v, top, left, right, bottom)
        return img

    def pixel(self, px, row, u, v, top, left, right, bottom):
        edges = []
        if top:
            edges.append((v, self.TOP))
        if left:
            edges.append((u, self.LEFT))
        if right:
            edges.append((16 - u, self.RIGHT))
        if bottom:
            edges.append((16 - v, self.BOTTOM))
        for d, prof in edges:
            if d < prof[0][0]:
                return self.pens['out']
        if edges:
            d, prof = min(edges, key=lambda e: e[0])
            for end, band in prof:
                if d < end:
                    return self.pens[band]
        ch = self.tex.get((px, row))
        return p(ch) if ch else self.fill

    def nine(self):
        """{'tl': img, 't': ..., 'c': ...}"""
        out = {}
        for rk, (top, bottom) in (('t', (1, 0)), ('m', (0, 0)), ('b', (0, 1))):
            for ck, (left, right) in (('l', (1, 0)), ('m', (0, 0)), ('r', (0, 1))):
                key = {'tl': 'tl', 'tm': 't', 'tr': 'tr', 'ml': 'l', 'mm': 'c', 'mr': 'r',
                       'bl': 'bl', 'bm': 'b', 'br': 'br'}[rk + ck]
                out[key] = self.tile(top, left, right, bottom)
        return out


def tex(art):
    """Texture from ASCII art ('.' = keep fill)."""
    d = {}
    for row, line in enumerate(art.strip('\n').splitlines()):
        for px, ch in enumerate(line.strip()):
            if ch != '.':
                d[(px, row)] = ch
    return d


GRAVEL = tex("""
........
....p...
........
.b......
........
......p.
........
..p.....
........
.....b..
........
p.......
........
...p....
......b.
........
""")

TAR = tex("""
........
...k....
........
......k.
........
.k......
........
....k...
........
........
k.......
.....k..
........
..k.....
........
.......k
""")

SAND = tex("""
.......o
..o....o
.......o
......oo
.......o
.......o
.o.....o
.......o
.......o
.....o.o
.......o
..o....o
.......o
.......o
o......o
oooooooo
""")

GRASS = tex("""
........
.l......
.....l..
........
..l.....
......l.
........
l.......
....l...
........
.l......
......l.
........
...l....
........
.......l
""")

# corrugated metal: ribs running N-S (lit rib, flat, shaded rib, flat)
RIBS = {(px, row): ('s' if px % 4 == 1 else 'b' if px % 4 == 3 else 't')
        for px in range(8) for row in range(16)}

OFFICE = FlatRoof('office', 'k', 'w', 'b', 'b', 'g', GRAVEL)
BRICK = FlatRoof('brick', 'k', 'R', 'r', 'k', 'b', TAR)
TOWER = FlatRoof('tower', 'k', 'w', 'o', 'o', 'c', SAND)
SHED = FlatRoof('shed', 'k', 'p', 'b', 'b', 't', RIBS)
PARK = FlatRoof('park', 'k', 'l', 'v', 'k', 'v', GRASS)
ROOFS = [OFFICE, BRICK, TOWER, SHED, PARK]


# ---------------------------------------------------------------- pitched roof (houses)

def pitched_tile(col, row, chimney=False):
    """House roof, ridge running E-W, 2 tiles tall. col in l/m/r, row in t/b.
    Tones: north slope n (lit), west hip R, south slope r, east hip r/k (shade)."""
    img = blank(TW, TH)
    for j in range(TH):
        V = j + 0.5 + (16 if row == 'b' else 0)          # 0..32 across the roof
        for px in range(TW):
            u = 2 * px + 1
            U = u if col != 'r' else 16 - u               # distance from the near end
            end = col in 'lr'
            dist_ns = min(V, 32 - V)                      # distance to eave (N or S)
            if V < 1 or V > 31 or (end and U < 2):
                c = 'k'
            elif end and U < dist_ns - 1:                 # hip triangle at the end
                if col == 'l':
                    c = 'r' if px % 4 == 3 else 'R'
                else:
                    c = 'k' if px % 4 == 0 else 'r'
            elif end and U < dist_ns + 1:                 # hip ridge
                c = 'n' if (col == 'l' or V < 16) else 'k'
            elif 15 <= V < 16:
                c = 'c'                                   # main ridge highlight
            elif V < 16:                                  # north slope, lit
                c = 'R' if int(V) % 4 == 2 else 'n'
            elif V < 17:
                c = 'k'
            else:                                         # south slope, shade
                c = 'k' if int(V) % 4 == 0 else 'r'
            img[j][px] = p(c)
    if chimney and row == 't':
        art = parse_art("""
        .kkkk.
        kwwwwk
        kgkkgb
        kggggb
        kggggb
        .bbbb.
        """)
        _stamp(img, art, 2, 5)
    return img


# ---------------------------------------------------------------- facades (ASCII)
# Each facade is authored as a middle tile; left/right ends get an outline column and a
# lit / shaded pilaster, so the middle tile can repeat any number of times.

FACADES = {
    # office: grey concrete, two floors of wide windows per tile
    'office_up': """
gggggggg
ggkkkkgg
ggpsssgg
ggspssgg
ggssssgg
ggwwwwgg
gggggggg
bbbbbbbb
gggggggg
ggkkkkgg
ggpsssgg
ggspssgg
ggssssgg
ggwwwwgg
gggggggg
bbbbbbbb
""",
    'office_ground': """
gggggggg
wwwwwwww
bbbbbbbb
kkkkkkkk
kpsskpss
kspskssp
kssskssp
ksspksss
ksssksps
kssskssp
kssskpss
kssskssp
ksssksss
kkkkkkkk
bbbbbbbb
kkkkkkkk
""",
    'office_door': """
gggggggg
wwwwwwww
bbbbbbbb
kkkkkkkk
kbwwwwbk
kbpsspbk
kbspsbbk
kbsssbbk
kbsspbbk
kbsssbbk
kbssybbk
kbsssbbk
kbsssbbk
kbsssbbk
kbbbbbbk
kkkkkkkk
""",
    # brick: red brick, white window frames
    'brick_up': """
rrrrrrrr
rRrrrrRr
rrwwwwrr
rrwppwrr
rrwsswrr
rrwsswrr
rrwwwwrr
rrkkkkRr
rRrrrrrr
rrwwwwrr
rrwppwrr
rrwsswrr
rrwsswrr
rrwwwwrr
rrkkkkrr
rrrrrRrr
""",
    'brick_ground': """
rrrrrrrr
iwiwiwiw
iwiwiwiw
kkkkkkkk
rkkkkkkr
rkpssskr
rkspsskr
rksssskr
rksssskr
rkssspkr
rksssskr
rkkkkkkr
rrrrrrrr
rRrrrRrr
rrrrrrrr
kkkkkkkk
""",
    'brick_door': """
rrrrrrrr
iwiwiwiw
iwiwiwiw
kkkkkkkk
rrkkkkrr
rkoooork
rkonnnok
rkonnnok
rkonnnok
rkonnyok
rkonnnok
rkonnnok
rkonnnok
rkoooork
rrggggrr
kkkkkkkk
""",
    # tower: glass curtain wall
    'tower_up': """
kkkkkkkk
bpssbpss
bspsbsps
bsssbsss
bsssbsss
kkkkkkkk
bsssbsss
bpssbpss
bspsbsps
bsssbsss
kkkkkkkk
bsssbsss
bsssbsss
bpssbpss
bspsbsps
bsssbsss
""",
    'tower_ground': """
cccccccc
wwwwwwww
oooooooo
kkkkkkkk
kpsskpss
kspskssp
kssskssp
ksspksss
ksssksps
kssskssp
kssskpss
kssskssp
ksssksss
kkkkkkkk
oooooooo
kkkkkkkk
""",
    'tower_door': """
cccccccc
wwwwwwww
oooooooo
kkkkkkkk
kowwwwok
kopsspok
kospsook
kossspok
kosspsok
kossspok
kosswsok
kossspok
kosssook
kosssook
kooooook
kkkkkkkk
""",
    # house: cream render, window with green shutters
    'house_wall': """
oooooooo
cccccccc
cccccccc
cvwwwwvc
cvwpswvc
cvwsswvc
cvwwwwvc
cvwspwvc
cvwsbwvc
cvwwwwvc
ccoooocc
cRiRyRcc
cvvvvvvc
cccccccc
oooooooo
kkkkkkkk
""",
    'house_door': """
oooooooo
cccccccc
ccnnnncc
cnoooonc
cnonnonc
cnonnonc
cnoooonc
cnonnonc
cnonnonc
cnonnyoc
cnonnonc
cnonnonc
cnoooonc
cggggggc
oggggggo
kkkkkkkk
""",
    # shed / warehouse: corrugated wall and roller door
    'shed_wall': """
tttttttt
bbbbbbbb
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
tsbttsbt
bbbbbbbb
kkkkkkkk
""",
    'shed_door': """
tttttttt
bbbbbbbb
ykykykyk
kkkkkkkk
kppppppk
kbbbbbbk
kggggggk
kbbbbbbk
kggggggk
kbbbbbbk
kggggggk
kbbbbbbk
kggggggk
kbbbbbbk
kggggggk
kkkkkkkk
""",
}


def facade_set(key):
    m = parse_art(FACADES[key])
    assert len(m) == TH and all(len(r) == TW for r in m), key
    counts = {}
    for row in m:
        for pen in row:
            counts[pen] = counts.get(pen, 0) + 1
    wall = max(counts, key=counts.get)
    lft = [row[:] for row in m]
    rgt = [row[:] for row in m]
    for j in range(TH):
        lft[j][0] = p('k')
        rgt[j][TW - 1] = p('k')
        if m[j][1] == wall:
            lft[j][1] = _lighter(wall)
        if m[j][TW - 2] == wall:
            rgt[j][TW - 2] = _darker(wall)
    return m, lft, rgt


_LIGHT = {'g': 'p', 'r': 'R', 'R': 'n', 'c': 'w', 'b': 's', 's': 'p', 't': 's', 'o': 'c',
          'v': 'l', 'w': 'w', 'p': 'w', 'n': 'c', 'i': 'w'}
_DARK = {'g': 'b', 'r': 'k', 'R': 'r', 'c': 'o', 'b': 'k', 's': 'b', 't': 'b', 'o': 'k',
         'v': 'k', 'w': 'p', 'p': 'b', 'n': 'o', 'i': 'R', 'y': 'o'}
_LET = {v: k for k, v in PEN.items()}


def _lighter(pen):
    return p(_LIGHT.get(_LET[pen], _LET[pen]))


def _darker(pen):
    return p(_DARK.get(_LET[pen], _LET[pen]))


def _stamp(img, art, x, y):
    for j, row in enumerate(art):
        for i, pen in enumerate(row):
            if pen is not None and 0 <= y + j < len(img) and 0 <= x + i < len(img[0]):
                img[y + j][x + i] = pen


# ---------------------------------------------------------------- roof props (on roof centre)

PROPS = {
    'office_hatch': """
........
........
.kkkkkk.
.kwwwwkb
.kwppgkb
.kwppgkb
.kggggkb
.kkkkkkb
.kbbbbkb
.kbkkbkb
.kbkkbkb
.kkkkkkb
..bbbbbb
........
........
........
""",
    'office_skylight': """
........
..kkkk..
.kwpssk.
.kpssbk.
.kssbsk.
.kkkkkk.
.kwpssk.
.kpssbk.
.kssbsk.
.kkkkkk.
.kwpssk.
.kpssbk.
.kssbsk.
.kkkkkkb
..bbbbbb
........
""",
    'brick_tank': """
..kkkk..
.koccok.
kocnnnok
knnnnnok
kononook
knnnnnok
knoooonk
.knnnnkb
.kkkkkkb
.k.kk.kb
.k.kk.kb
.kkkkkkb
..bbbbbb
........
........
........
""",
    'brick_chimney': """
........
........
........
..kkkk..
.kRRRnk.
.krkkRk.
.krkkRk.
.krrrrkk
.kkkkkkk
..kkkkk.
........
........
........
........
........
........
""",
    'brick_skylight': """
........
........
.kkkkkk.
.kpwppk.
.kpssbk.
.kkkkkk.
.kpwppk.
.kpssbk.
.kkkkkkk
..kkkkkk
........
........
........
........
........
........
""",
    'shed_skylight': """
..kkkk..
..kppk..
..kpsk..
..kssk..
..kspk..
..kssk..
..kpsk..
..kssk..
..kspk..
..kssk..
..kpsk..
..kssk..
..kspk..
..kssk..
..kpsk..
..kssk..
""",
    'shed_vent': """
........
........
...kk...
..kwwk..
.kwppbk.
.kpbbbk.
.kpbkbk.
..kbbkk.
...kkkk.
....kk..
........
........
........
........
........
........
""",
}


def circle_prop(fill_img, cx, cy, r_out, shade):
    """Draw a round object on an image using visual units; shade(u,v,dist)->letter or None."""
    h, w = len(fill_img), len(fill_img[0])
    for j in range(h):
        v = j + 0.5
        for i in range(w):
            u = 2 * i + 1
            d = math.hypot(u - cx, v - cy)
            c = shade(u - cx, v - cy, d)
            if c:
                fill_img[j][i] = p(c)


def ac_unit(base, top, side):
    """Rooftop AC box seen from above: light lid, round fan grille, drop shadow."""
    img = [row[:] for row in base]
    for j in range(TH):
        v = j + 0.5
        for i in range(TW):
            u = 2 * i + 1
            if 4 <= u < 16 and 3 <= v < 15 and not (2 <= u < 14 and 2 <= v < 13):
                img[j][i] = p(side)                       # shadow, bottom-right
            if 2 <= u < 14 and 2 <= v < 13:
                edge = u < 4 or u >= 12 or v < 3 or v >= 12
                img[j][i] = p('k') if edge else p(top)
    def fan(dx, dy, d):
        if d < 1.3:
            return 'w'
        if d < 3.3:
            a = math.atan2(dy, dx)
            return 'g' if int((a + math.pi) / (math.pi / 2) + 0.25) % 2 else 'b'
        if d < 4.4:
            return 'k'
        return None
    circle_prop(img, 8, 7.5, 4.4, fan)
    return img


def dish(base):
    """Satellite dish seen from above, pointing south-east."""
    img = [row[:] for row in base]
    circle_prop(img, 9, 9, 5.5, lambda dx, dy, d: 'o' if d < 5.5 else None)      # shadow
    def bowl(dx, dy, d):
        if d >= 5.5:
            return None
        if d >= 4.5:
            return 'k'
        if d < 1.2:
            return 'k'                     # feed horn
        return 'w' if dx + dy < -2 else 'p' if dx + dy < 2 else 'b'
    circle_prop(img, 7, 7, 5.5, bowl)
    return img


def tree_tile(base):
    img = [row[:] for row in base]

    def shadow(dx, dy, d):
        return 'k' if math.hypot(dx - 2, dy - 2) < 7 else None

    def canopy(dx, dy, d):
        if d >= 7:
            return None
        if d >= 6:
            return 'k'
        light = -dx - dy                   # lit from top-left
        blob = (int(dx + 20) // 4 + int(dy + 20) // 3) % 2
        if light > 5:
            return 'l'
        if light > 0:
            return 'l' if blob else 'v'
        if light > -5:
            return 'v'
        return 'v' if blob else 'k'
    circle_prop(img, 8, 8, 7, shadow)
    circle_prop(img, 8, 8, 7, canopy)
    return img


def fountain_tile(base):
    img = [row[:] for row in base]

    def rim(dx, dy, d):
        if d < 5.5:
            return 's' if (int(d * 2) % 3) else 'p'
        if d < 7:
            return 'w' if dx + dy < 0 else 'g'
        if d < 8:
            return 'k'
        return None
    circle_prop(img, 8, 8, 8, rim)
    _stamp(img, parse_art("""
    .ww.
    wppw
    .ww.
    """), 2, 6)
    return img


def helipad(base_c):
    """2x2 tiles: yellow ring, white H on a dark pad."""
    img = blank(2 * TW, 2 * TH)
    for j in range(2 * TH):
        for i in range(2 * TW):
            img[j][i] = base_c[j % TH][i % TW]

    def pad(dx, dy, d):
        if d < 11:
            return 'b'
        if d < 12.5:
            return 'y'
        if d < 14:
            return 'g'
        if d < 15:
            return 'k'
        return None
    circle_prop(img, 16, 16, 15, pad)
    h = parse_art("""
    w..w
    w..w
    w..w
    wwww
    w..w
    w..w
    w..w
    """)
    _stamp(img, h, 6, 12)
    return img


PATH_H = """
kkkkkkkk
cccccccc
cocccocc
cccccccc
ccocccco
cccccccc
occcccoc
cccccccc
cccocccc
ccccccoc
cccccccc
cocccccc
cccccocc
cccccccc
occcccco
kkkkkkkk
"""


def park_path(kind, base):
    """kind: h, v or x (crossing). Sand path 1 tile wide across grass."""
    img = [row[:] for row in base]
    for j in range(TH):
        for i in range(TW):
            u, v = 2 * i + 1, j + 0.5
            in_h = 3 <= v < 13
            in_v = 3 <= u < 13
            on = (kind == 'h' and in_h) or (kind == 'v' and in_v) or (kind == 'x' and (in_h or in_v))
            edge_h = (kind in 'hx') and (2 <= v < 3 or 13 <= v < 14) and not (kind == 'x' and in_v)
            edge_v = (kind in 'vx') and (1 <= u < 3 or 13 <= u < 15) and not (kind == 'x' and in_h)
            if on:
                img[j][i] = p('o') if (i * 5 + j * 3) % 11 == 0 else p('c')
            elif edge_h or edge_v:
                img[j][i] = p('o')
    return img


def flowers(base):
    img = [row[:] for row in base]
    art = parse_art("""
    ........
    .R...y..
    ..v.R.v.
    .y.v..i.
    ...R.v..
    .iv..y..
    ...v.R.v
    .R..i...
    ..y..v..
    .v.R...y
    ..i..v..
    .R..y.R.
    ..v...v.
    .y.i.R..
    ........
    ........
    """)
    _stamp(img, art, 0, 0)
    return img


# ---------------------------------------------------------------- building list

def build(bank=None):
    """Adds building tiles to the bank; returns the bank and a kit description:
    kit[style] = {'roof': {key: idx}, 'props': {name: idx or 2D}, 'front': {...}}"""
    bank = bank or TileBank()
    kit = {}

    def add(img, name, tag):
        g = bank.add_image(img, name, tag)
        return g[0][0] if len(g) == 1 and len(g[0]) == 1 else g

    for roof in ROOFS:
        tag = 'bld_' + roof.name
        k = {'roof': {}, 'props': {}, 'front': {}}
        nine = roof.nine()
        for key in ('tl', 't', 'tr', 'l', 'c', 'r', 'bl', 'b', 'br'):
            k['roof'][key] = add(nine[key], '%s_roof_%s' % (roof.name, key), tag)
        for pname, art in PROPS.items():
            if pname.startswith(roof.name + '_'):
                img = [row[:] for row in nine['c']]
                _stamp(img, parse_art(art), 0, 0)
                k['props'][pname[len(roof.name) + 1:]] = add(img, '%s_roof_%s' % (roof.name, pname.split('_', 1)[1]), tag)
        if roof in (OFFICE, TOWER):
            k['props']['ac'] = add(ac_unit(nine['c'], 'p' if roof is OFFICE else 'w', 'b' if roof is OFFICE else 'o'),
                                   '%s_roof_ac' % roof.name, tag)
        if roof is TOWER:
            k['props']['dish'] = add(dish(nine['c']), 'tower_roof_dish', tag)
            k['props']['helipad'] = add(helipad(nine['c']), 'tower_helipad', tag)
        if roof is PARK:
            k['props']['tree'] = add(tree_tile(nine['c']), 'park_tree', tag)
            k['props']['flowers'] = add(flowers(nine['c']), 'park_flowers', tag)
            k['props']['fountain'] = add(fountain_tile(nine['c']), 'park_fountain', tag)
            for kind in 'hvx':
                k['props']['path_' + kind] = add(park_path(kind, nine['c']), 'park_path_' + kind, tag)
        for fkey in FACADES:
            if not fkey.startswith(roof.name + '_'):
                continue
            part = fkey.split('_', 1)[1]
            m, lft, rgt = facade_set(fkey)
            if part.endswith('door'):
                k['front'][part] = add(m, '%s_front_%s' % (roof.name, part), tag)
            else:
                k['front'][part + '_l'] = add(lft, '%s_front_%s_l' % (roof.name, part), tag)
                k['front'][part] = add(m, '%s_front_%s' % (roof.name, part), tag)
                k['front'][part + '_r'] = add(rgt, '%s_front_%s_r' % (roof.name, part), tag)
        kit[roof.name] = k

    # houses: pitched roof 2 rows + front wall
    tag = 'bld_house'
    k = {'roof': {}, 'props': {}, 'front': {}}
    for row in 'tb':
        for col in 'lmr':
            k['roof'][row + col] = add(pitched_tile(col, row), 'house_roof_%s%s' % (row, col), tag)
    k['props']['chimney'] = add(pitched_tile('m', 't', chimney=True), 'house_roof_chimney', tag)
    m, lft, rgt = facade_set('house_wall')
    k['front']['wall_l'] = add(lft, 'house_front_wall_l', tag)
    k['front']['wall'] = add(m, 'house_front_wall', tag)
    k['front']['wall_r'] = add(rgt, 'house_front_wall_r', tag)
    k['front']['door'] = add(parse_art(FACADES['house_door']), 'house_front_door', tag)
    kit['house'] = k

    # open ground inside blocks: plaza paving and a parking lot
    tag = 'ground'
    k = {}
    plaza = blank(TW, TH, p('g'))
    for j in range(TH):
        for i in range(TW):
            if i % 4 == 0 or j % 8 == 0:
                plaza[j][i] = p('p')
    k['plaza'] = add(plaza, 'plaza', tag)
    lot = blank(TW, TH, p('k'))
    for (i, j) in ASPH_TEX:
        lot[j][i] = p('b')
    k['lot'] = add(lot, 'lot', tag)
    for name, rows in (('lot_bay_n', range(3, 16)), ('lot_bay_s', range(0, 13))):
        img = [r[:] for r in lot]
        for j in rows:
            img[j][0] = p('w')
        k[name] = add(img, name, tag)
    kit['ground'] = k
    return bank, kit


ASPH_TEX = {(2, 1), (6, 3), (1, 6), (4, 8), (7, 10), (0, 12), (5, 13), (3, 15)}   # = roads.ASPH_TEX
