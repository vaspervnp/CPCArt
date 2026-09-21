"""Helpers that turn the building kit into tile grids (used by previews and the mockup)."""


def roof_grid(k, w, h, props=None):
    """9-slice roof w x h tiles. props: {(x, y): name} on interior tiles."""
    r = k['roof']
    g = []
    for y in range(h):
        row = []
        for x in range(w):
            ky = 't' if y == 0 else 'b' if y == h - 1 else 'm'
            kx = 'l' if x == 0 else 'r' if x == w - 1 else 'm'
            key = {'tl': 'tl', 'tm': 't', 'tr': 'tr', 'ml': 'l', 'mm': 'c', 'mr': 'r',
                   'bl': 'bl', 'bm': 'b', 'br': 'br'}[ky + kx]
            row.append(r[key])
        g.append(row)
    for (x, y), name in (props or {}).items():
        v = k['props'][name]
        if isinstance(v, list):
            for j, line in enumerate(v):
                for i, t in enumerate(line):
                    g[y + j][x + i] = t
        else:
            g[y][x] = v
    return g


def front_row(k, w, part, doors=()):
    f = k['front']
    row = []
    for x in range(w):
        if x in doors and 'door' in f:
            row.append(f['door'])
        elif x == 0:
            row.append(f[part + '_l'])
        elif x == w - 1:
            row.append(f[part + '_r'])
        else:
            row.append(f[part])
    return row


def building(kit, style, w, roof_h=2, floors=1, props=None, doors=None):
    """Flat-roof building: roof_h roof rows + (floors-1) upper wall rows + 1 ground row.
    House: 2 pitched roof rows + 1 wall row (roof_h ignored)."""
    k = kit[style]
    if doors is None:
        doors = (w // 2,)
    if style == 'house':
        r = k['roof']
        g = []
        for row in 'tb':
            line = []
            for x in range(w):
                col = 'l' if x == 0 else 'r' if x == w - 1 else 'm'
                line.append(r[row + col])
            g.append(line)
        for (x, y), name in (props or {}).items():
            g[y][x] = k['props'][name]
        g.append(front_row(k, w, 'wall', doors))
        return g
    g = roof_grid(k, w, roof_h, props)
    if style == 'park':
        return g
    if style == 'shed':
        g.append(front_row(k, w, 'wall', doors))
        return g
    for _ in range(floors - 1):
        g.append(front_row(k, w, 'up'))
    g.append(front_row(k, w, 'ground', doors))
    return g
