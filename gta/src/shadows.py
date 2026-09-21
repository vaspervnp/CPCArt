"""Building drop shadows, baked into copies of the ground tiles they fall on.

Light comes from the top-left, so a building's shadow is its footprint (roof + front wall)
swept DX units right and DY units down: a strip along the east side that starts with a 45
degree cut at the top, a strip under the front wall, and a square at the south-east corner.
Only ground cells receive shadows (roads, plaza, parking, park); other buildings don't.

A shadowed tile = the base tile with every pixel inside the shadow mask replaced by a darker
pen (REMAP). The shadow sheet holds a fixed set for the common cases (straights and open
ground) plus whatever the maps passed to add() need.
"""
from cpcgfx import PALETTE, PEN, TW, TH, TileBank

DX, DY = 6, 6          # shadow length in visual units = sidewalk width, so it never
                       # reaches the asphalt of streets and avenues (black stays black anyway)

# pen -> pen in shadow (roughly half the brightness, CPC colours only)
_DARK = {'k': 'k', 'b': 'k', 'g': 'b', 'w': 'g', 'y': 'o', 'o': 'k', 'r': 'k', 'R': 'r',
         'n': 'r', 'v': 'k', 'l': 'v', 's': 'b', 'p': 'g', 'c': 'o', 't': 'b', 'i': 'R'}
REMAP = [PEN[_DARK[p[0]]] for p in PALETTE]


def cell_masks(casts, dx=DX, dy=DY):
    """casts: rows of bools (True = building cell). Returns {(cx, cy): mask} for every
    non-building cell a shadow touches; mask = 16 row bitmasks, bit n = pixel n."""
    H, W = len(casts), len(casts[0])

    def building(U, V):
        cx, cy = int(U // 16), int(V // 16)
        return 0 <= cx < W and 0 <= cy < H and casts[cy][cx]

    out = {}
    for cy in range(H):
        for cx in range(W):
            if casts[cy][cx]:
                continue
            if not any(0 <= cx - ox < W and 0 <= cy - oy < H and casts[cy - oy][cx - ox]
                       for ox, oy in ((1, 0), (0, 1), (1, 1))):
                continue
            rows, hit = [], False
            for row in range(TH):
                bits = 0
                for px in range(TW):
                    U, V = 16 * cx + 2 * px + 1, 16 * cy + row + 0.5
                    for s in range(1, 17):
                        t = s / 16.0
                        if building(U - t * dx, V - t * dy):
                            bits |= 1 << px
                            hit = True
                            break
                rows.append(bits)
            if hit:
                out[(cx, cy)] = tuple(rows)
    return out


def canonical_masks():
    """Named masks from a lone 3x3 building."""
    casts = [[1 <= x <= 3 and 1 <= y <= 3 for x in range(6)] for y in range(6)]
    m = cell_masks(casts)
    return {'E_top': m[(4, 1)], 'E': m[(4, 2)], 'SE': m[(4, 4)],
            'S_left': m[(1, 4)], 'S': m[(2, 4)]}


def apply(tile, mask):
    return tuple(tuple(REMAP[p] if mask[j] >> i & 1 else p for i, p in enumerate(row))
                 for j, row in enumerate(tile))


def mask_name(mask, named):
    for n, m in named.items():
        if m == mask:
            return n
    parts = [n for n, m in named.items() if all((a | b) == a for a, b in zip(mask, m)) and any(m)]
    return '+'.join(sorted(parts)) if parts else 'custom'


def canonical_requests(pieces, kit, R):
    """(base global index, mask name) pairs every city needs: shadows on the sidewalks of
    straight roads and on open ground."""
    P = {p['name']: p['tiles'] for p in pieces}
    ns_left = [P['street_NS'][0][0], P['avenue_NS'][0][0], P['alley_NS'][0][0]]
    ew_top = [P['street_EW'][0][0], P['avenue_EW'][0][0], P['alley_EW'][0][0]]
    g = kit['ground']
    ground = [g['plaza'] + R, g['lot'] + R]
    req = []
    for t in ns_left + ground + [g['lot_bay_n'] + R]:
        req += [(t, 'E_top'), (t, 'E')]
    for t in ew_top + ground:
        req += [(t, 'S_left'), (t, 'S')]
    for t in ew_top + ground:
        req.append((t, 'SE'))
    return req


class ShadowSet:
    def __init__(self, base_tiles, base_names, R):
        self.base_tiles, self.base_names, self.R = base_tiles, base_names, R
        self.named = canonical_masks()
        self.masks = dict(self.named)             # name -> mask (grows with mixes)
        self.bank = TileBank()
        self.table = []                           # rows for shadow_table.json
        self.lookup = {}                          # (base global, mask name) -> shadow index
        self.unchanged = set()

    def add(self, requests, tag):
        """Append shadow tiles for (base global, mask name) requests under one tag.
        Earlier tiles never move, so adding maps later keeps existing indices."""
        for base, mname in requests:
            key = (base, mname)
            if key in self.lookup or key in self.unchanged:
                continue
            tile = apply(self.base_tiles[base], self.masks[mname])
            if tile == self.base_tiles[base]:
                self.unchanged.add(key)           # shadow only fell on black: keep base tile
                continue
            name = '%s_sh_%s' % (self.base_names[base], mname.replace('+', '_'))
            idx = self.bank.add(tile, name, tag)
            self.lookup[key] = idx
            self.table.append({'index': idx, 'base_global': base, 'mask': mname})
        return self

    def map_requests(self, grid, casts):
        """Requests for one map (rows of global base indices)."""
        out = []
        for (cx, cy), mask in cell_masks(casts).items():
            name = mask_name(mask, self.named)
            if name not in self.masks or self.masks[name] != mask:
                name = name if name not in self.masks else name + '_%d' % len(self.masks)
                self.masks[name] = mask
            out.append((grid[cy][cx], name, (cx, cy)))
        return out

    def apply_map(self, grid, reqs, first_global):
        """Swap shadowed cells to shadow tiles (global = first_global + index)."""
        for base, name, (cx, cy) in reqs:
            if (base, name) in self.lookup:
                grid[cy][cx] = first_global + self.lookup[(base, name)]
