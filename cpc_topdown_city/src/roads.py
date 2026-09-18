"""Top-down road pieces for a GTA1-style CPC Mode 0 city.

Every piece is rendered from geometry (bands, arms, rounded kerbs) at Mode 0 resolution,
sampling each pixel at its centre in square "visual units" (a Mode 0 pixel = 2x1 units,
a tile = 16x16 units). Pieces are then cut into 8x16 tiles and de-duplicated, so a piece
is just a small grid of tile indices (a metatile).

Road types (width across the road):
  alley   1 tile  = 16u : 2u footway | 12u cobbles | 2u footway, no markings
  street  2 tiles = 32u : 4u paving, 2u kerb | 2 lanes (centre dashes) | kerb, paving
  avenue  4 tiles = 64u : paving, kerb | 2 lanes | double yellow | 2 lanes | kerb, paving
"""
import math
from cpcgfx import K, B, G, W, Y, P, TileBank, blank, TW, TH

# ---------------------------------------------------------------- look

ASPH_BASE, ASPH_DOT = K, B
PAVE, JOINT, KERB = G, B, P
EDGE = G               # alley edge: narrow footway along the walls
DASH, YELLOW, ZEBRA = W, Y, W

ALLEY_STYLE = 'cobble'
_ALLEY_ART = {
    'asphalt': [[B if (i, j) in {(2, 1), (6, 3), (1, 6), (4, 8), (7, 10), (0, 12), (5, 13), (3, 15)} else K
                 for i in range(8)] for j in range(16)],
    # dark blue setts with black joints, rows offset by half a stone
    'cobble': [[K if (j % 4 == 3 or (i + (2 if (j // 4) % 2 else 0)) % 4 == 3) else B
                for i in range(8)] for j in range(16)],
}
ALLEY_TEX = _ALLEY_ART[ALLEY_STYLE]

# sparse speckle, identical in every tile so the pattern stays seamless
ASPH_TEX = {(2, 1), (6, 3), (1, 6), (4, 8), (7, 10), (0, 12), (5, 13), (3, 15)}


class RoadType:
    def __init__(self, name, rank, tiles, side, kerb, marks, r_corner, r_inner):
        self.name, self.rank, self.tiles = name, rank, tiles
        self.side = side            # width of the sidewalk / edge band in visual units
        self.kerb = kerb            # True: paving + kerb, False: alley edge
        self.marks = marks          # [(from, to, kind)] across the road, kind: dash|yellow
        self.r_corner = r_corner    # outer kerb radius on a bend
        self.r_inner = r_inner      # radius of sidewalk corners at junctions


ALLEY = RoadType('alley', 0, 1, 2, False, [], 6, 0)
STREET = RoadType('street', 1, 2, 6, True, [(15, 17, 'dash')], 10, 4)
AVENUE = RoadType('avenue', 2, 4, 6, True,
                  [(16, 18, 'dash'), (28, 30, 'yellow'), (34, 36, 'yellow'), (46, 48, 'dash')],
                  16, 4)
TYPES = [ALLEY, STREET, AVENUE]


class Block:
    """A rectangular road piece. H = road running E-W (its arms are E/W), V = road running
    N-S (arms N/S). Either may be None for a plain straight."""

    def __init__(self, H, V, mask, bw, bh, zebra=False, decor=()):
        self.H, self.V, self.mask, self.zebra = H, V, mask, zebra
        self.decor = decor          # functions (u, v) -> pen or None, drawn on top
        self.Bw, self.Bh = 16 * bw, 16 * bh
        self.aH = H.side if H else 0
        self.aV = V.side if V else 0
        self.has = {d: d in mask for d in 'NESW'}
        roads = [t for t in (H, V) if t]
        self.major = max(roads, key=lambda t: t.rank)
        n_arms = len(mask)
        cw, ch = self.Bw - 2 * self.aV, self.Bh - 2 * self.aH
        if n_arms == 1:
            self.rc = min(cw, ch) / 2.0          # dead end: full half-circle
        else:
            self.rc = min(self.major.r_corner, min(cw, ch) / 2.0)
        self.ri = min([t.r_inner for t in roads] + [self.aH or 99, self.aV or 99])
        aV, aH, Bw, Bh = self.aV, self.aH, self.Bw, self.Bh
        # core corner points: (x, y, dir into core x, dir into core y, side a, side b)
        self.corners = [(aV, aH, 1, 1, 'N', 'W'), (Bw - aV, aH, -1, 1, 'N', 'E'),
                        (aV, Bh - aH, 1, -1, 'S', 'W'), (Bw - aV, Bh - aH, -1, -1, 'S', 'E')]
        # which markings run through this block
        e, w_, n, s = self.has['E'], self.has['W'], self.has['N'], self.has['S']
        # a road keeps its markings through a block when it passes straight through and
        # only a lower-rank road joins it; dead ends keep them up to the turning circle
        self.h_marks = bool(H and H.marks and ((e and w_ and (not V or V.rank < H.rank))
                                              or (n_arms == 1 and (e or w_))))
        self.v_marks = bool(V and V.marks and ((n and s and (not H or H.rank < V.rank))
                                              or (n_arms == 1 and (n or s))))

    # -- geometry -------------------------------------------------------
    def in_h(self, v):
        return self.aH <= v < self.Bh - self.aH

    def in_v(self, u):
        return self.aV <= u < self.Bw - self.aV

    def asphalt(self, u, v):
        inH, inV = self.in_h(v), self.in_v(u)
        if inH and inV:                      # core, maybe with rounded outer corners
            for cx, cy, sx, sy, a, b in self.corners:
                if self.has[a] or self.has[b]:
                    continue
                R = self.rc
                if (u - cx) * sx < R and (v - cy) * sy < R:
                    if math.hypot(u - (cx + sx * R), v - (cy + sy * R)) > R:
                        return False
            return True
        if inH:
            return self.has['W'] if u < self.aV else self.has['E']
        if inV:
            return self.has['N'] if v < self.aH else self.has['S']
        # corner square: sidewalk, rounded where two arms meet
        for cx, cy, sx, sy, a, b in self.corners:
            if not (self.has[a] and self.has[b]):
                continue
            dx, dy = (u - cx) * -sx, (v - cy) * -sy
            if dx >= 0 and dy >= 0 and dx < self.ri and dy < self.ri:
                if math.hypot(u - (cx - sx * self.ri), v - (cy - sy * self.ri)) > self.ri:
                    return True
        return False

    def owner(self, u, v):
        inH, inV = self.in_h(v), self.in_v(u)
        if inV and not inH:
            return self.H or self.major, 'h'
        if inH and not inV:
            return self.V or self.major, 'v'
        return self.major, None

    # -- rendering ------------------------------------------------------
    def render(self):
        img = blank(self.Bw // 2, self.Bh)
        for row in range(self.Bh):
            v = row + 0.5
            for px in range(self.Bw // 2):
                u = 2 * px + 1
                pen = self.pixel(px, row, u, v)
                for d in self.decor:
                    c = d(u, v)
                    if c is not None:
                        pen = c
                img[row][px] = pen
        return img

    def pixel(self, px, row, u, v):
        if self.asphalt(u, v):
            return self.road_pixel(px, row, u, v)
        road, strip = self.owner(u, v)
        if not road.kerb:
            return EDGE
        for dx, dy in ((-2, 0), (2, 0), (0, -1), (0, 1), (0, -2), (0, 2)):
            if self.asphalt(u + dx, v + dy):
                return KERB
        if strip == 'h' and u % 8 < 2:
            return JOINT
        if strip == 'v' and int(v) % 8 < 2:
            return JOINT
        return PAVE

    def road_pixel(self, px, row, u, v):
        H, V = self.H, self.V
        if self.zebra:
            if H:   # E-W road: stripes run E-W, stacked N-S
                lo, hi = self.aH + 1, self.Bh - self.aH - 1
                if 2 <= u < 14 and lo <= v < hi and int(v - lo) % 4 < 2:
                    return ZEBRA
            else:
                lo, hi = self.aV + 1, self.Bw - self.aV - 1
                if 2 <= v < 14 and lo <= u < hi and int(u - lo) % 4 < 2:
                    return ZEBRA
        else:
            if self.h_marks and self.in_h(v):
                half_ok = (not (self.has['E'] ^ self.has['W'])) or \
                          (self.has['E'] and u >= self.Bw / 2) or (self.has['W'] and u < self.Bw / 2)
                if half_ok:
                    for d0, d1, kind in H.marks:
                        if d0 <= v < d1:
                            if kind == 'yellow' or 4 <= u % 16 < 12:
                                return YELLOW if kind == 'yellow' else DASH
            if self.v_marks and self.in_v(u):
                half_ok = (not (self.has['N'] ^ self.has['S'])) or \
                          (self.has['S'] and v >= self.Bh / 2) or (self.has['N'] and v < self.Bh / 2)
                if half_ok:
                    for d0, d1, kind in V.marks:
                        if d0 <= u < d1:
                            if kind == 'yellow' or 4 <= v % 16 < 12:
                                return YELLOW if kind == 'yellow' else DASH
        if self.surface_owner(u, v).kerb is False:
            return ALLEY_TEX[row % TH][px % TW]
        return ASPH_DOT if (px % TW, row % TH) in ASPH_TEX else ASPH_BASE

    def surface_owner(self, u, v):
        inH, inV = self.in_h(v), self.in_v(u)
        if inH and inV:
            return self.major
        if inH:
            return self.H or self.major
        return self.V or self.major


# ---------------------------------------------------------------- street furniture
# Coordinates in visual units inside the piece. Centres sit on even u / whole v so the
# round shapes stay symmetric on 2:1 pixels.

def manhole(cx, cy, r=3.4):
    """Round cast-iron cover: grey rim with a lit top-left edge, dark lid, grey boss."""
    def f(u, v):
        dx, dy = u - cx, v - cy
        d = math.hypot(dx, dy)
        if d >= r:
            return None
        if d >= r - 1.1:
            return P if dx + dy < -2.0 else G
        return G if d < 1.0 else B
    return f


def grate_h(u0, v0):
    """Kerb inlet along an E-W kerb: 8u x 4 rows, slots across the kerb."""
    def f(u, v):
        if not (u0 <= u < u0 + 8 and v0 <= v < v0 + 4):
            return None
        inner = 1 <= v - v0 < 3
        return K if inner and int(u - u0) // 2 % 2 == 1 else G
    return f


def grate_v(u0, v0):
    """Kerb inlet along a N-S kerb: 4u x 8 rows, slots across the kerb."""
    def f(u, v):
        if not (u0 <= u < u0 + 4 and v0 <= v < v0 + 8):
            return None
        return K if 0 < v - v0 < 7 and int(v - v0) % 2 == 1 else G
    return f


def grate_c(cx, cy):
    """Square gully grate in the middle of an alley: 8u x 8 rows."""
    def f(u, v):
        if not (cx - 4 <= u < cx + 4 and cy - 4 <= v < cy + 4):
            return None
        edge = u < cx - 2 or u >= cx + 2 or v < cy - 3 or v >= cy + 3
        return G if edge or int(v - cy) % 2 == 0 else K
    return f


# ---------------------------------------------------------------- piece list

def piece_list():
    """(group, name, Block) in sheet order. Masks are written in N E S W order and list
    the sides the piece connects to."""
    out = []
    for t in TYPES:
        n = t.tiles
        out.append((t.name, '%s_EW' % t.name, Block(t, None, 'EW', 1, n)))
        out.append((t.name, '%s_NS' % t.name, Block(None, t, 'NS', n, 1)))
        for m in ('NE', 'ES', 'SW', 'NW'):                   # bends
            out.append((t.name, '%s_%s' % (t.name, m), Block(t, t, m, n, n)))
        for m in ('ESW', 'NSW', 'NEW', 'NES'):               # T junctions
            out.append((t.name, '%s_%s' % (t.name, m), Block(t, t, m, n, n)))
        out.append((t.name, '%s_NESW' % t.name, Block(t, t, 'NESW', n, n)))
        for m in ('N', 'E', 'S', 'W'):                       # dead ends (open side)
            out.append((t.name, '%s_%s' % (t.name, m), Block(t, t, m, n, n)))
    for t in (STREET, AVENUE):
        out.append(('zebra', '%s_EW_zebra' % t.name, Block(t, None, 'EW', 1, t.tiles, zebra=True)))
        out.append(('zebra', '%s_NS_zebra' % t.name, Block(None, t, 'NS', t.tiles, 1, zebra=True)))
    for M in (STREET, AVENUE):
        for m in (ALLEY, STREET):
            if m.rank >= M.rank:
                continue
            for mask, tag in (('NEW', 'N'), ('ESW', 'S'), ('NESW', 'NS')):
                out.append(('junction', '%s_EW+%s_%s' % (M.name, m.name, tag),
                            Block(M, m, mask, m.tiles, M.tiles)))
            for mask, tag in (('NES', 'E'), ('NSW', 'W'), ('NESW', 'EW')):
                out.append(('junction', '%s_NS+%s_%s' % (M.name, m.name, tag),
                            Block(m, M, mask, M.tiles, m.tiles)))
    # manholes and kerb drains: drop-in replacements for straights
    A, St, Av = ALLEY, STREET, AVENUE
    out += [
        ('decor', 'alley_EW_manhole', Block(A, None, 'EW', 1, 1, decor=[manhole(8, 8)])),
        ('decor', 'alley_NS_manhole', Block(None, A, 'NS', 1, 1, decor=[manhole(8, 8)])),
        ('decor', 'alley_EW_drain', Block(A, None, 'EW', 1, 1, decor=[grate_c(8, 8)])),
        ('decor', 'alley_NS_drain', Block(None, A, 'NS', 1, 1, decor=[grate_c(8, 8)])),
        # streets/avenues: furniture on the south / east side, which building shadows
        # (cast to the south-east) never reach, so these tiles need no shadow copies
        ('decor', 'street_EW_manhole', Block(St, None, 'EW', 1, 2, decor=[manhole(8, 21.5)])),
        ('decor', 'street_NS_manhole', Block(None, St, 'NS', 2, 1, decor=[manhole(22, 8)])),
        ('decor', 'street_EW_drain', Block(St, None, 'EW', 1, 2, decor=[grate_h(4, 22)])),
        ('decor', 'street_NS_drain', Block(None, St, 'NS', 2, 1, decor=[grate_v(22, 4)])),
        ('decor', 'avenue_EW_manhole', Block(Av, None, 'EW', 1, 4, decor=[manhole(4, 23), manhole(12, 41)])),
        ('decor', 'avenue_NS_manhole', Block(None, Av, 'NS', 4, 1, decor=[manhole(24, 4), manhole(40, 12)])),
        ('decor', 'avenue_EW_drain', Block(Av, None, 'EW', 1, 4, decor=[grate_h(4, 54)])),
        ('decor', 'avenue_NS_drain', Block(None, Av, 'NS', 4, 1, decor=[grate_v(54, 4)])),
        # plain asphalt with a manhole: any junction core (cut from an avenue crossing)
        ('decor', 'asphalt_manhole', Block(Av, Av, 'NESW', 4, 4, decor=[manhole(24, 24)]), (1, 1)),
    ]
    return out


def build(bank=None):
    bank = bank or TileBank()
    pieces = []
    for group, name, blk, *cut in piece_list():
        img = blk.render()
        if cut:                                   # keep a single tile of the block
            (tx, ty), = cut
            img = [row[tx * TW:(tx + 1) * TW] for row in img[ty * TH:(ty + 1) * TH]]
        grid = bank.add_image(img, name, 'road_' + group)
        pieces.append({'name': name, 'group': group, 'w': len(grid[0]), 'h': len(grid),
                       'connects': blk.mask, 'tiles': grid})
    return bank, pieces
