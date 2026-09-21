"""Mockup city built only from the road pieces and building kit, with the car and pedestrian
sprites on top. Shadows are baked in by make_all.py."""
from assemble import building, roof_grid
from cpcgfx import Canvas, TW, TH
from sprites import DIRS

MAP_W, MAP_H = 52, 40


class CityMap:
    def __init__(self, rbank, pieces, bbank, kit):
        self.P = {p['name']: p for p in pieces}
        self.R = len(rbank.tiles)
        self.tiles = rbank.tiles + bbank.tiles
        self.kit = kit
        self.c = [[None] * MAP_W for _ in range(MAP_H)]

    def put(self, grid, x, y, off=0):
        for j, row in enumerate(grid):
            for i, t in enumerate(row):
                if t is not None and 0 <= x + i < MAP_W and 0 <= y + j < MAP_H:
                    self.c[y + j][x + i] = t + off

    def road(self, name, x, y):
        self.put(self.P[name]['tiles'], x, y)

    def run_h(self, name, x0, x1, y):
        for x in range(x0, x1 + 1):
            self.road(name, x, y)

    def run_v(self, name, x, y0, y1):
        for y in range(y0, y1 + 1):
            self.road(name, x, y)

    def bld(self, x, y, style, w, roof_h=2, floors=1, props=None, doors=None):
        g = building(self.kit, style, w, roof_h, floors, props, doors)
        for j, row in enumerate(g):
            for i, _ in enumerate(row):
                assert self.c[y + j][x + i] is None, ('overlap', style, x + i, y + j)
        self.put(g, x, y, self.R)

    def park(self, x, y, w, h, props):
        self.put(roof_grid(self.kit['park'], w, h, props), x, y, self.R)

    def ground(self, x0, y0, x1, y1, name):
        t = self.kit['ground'][name] + self.R
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.c[y][x] is None:
                    self.c[y][x] = t

    def image(self):
        img = [[0] * (MAP_W * TW) for _ in range(MAP_H * TH)]
        for ty in range(MAP_H):
            for tx in range(MAP_W):
                idx = self.c[ty][tx]
                if idx is None:
                    continue
                t = self.tiles[idx]
                for j in range(TH):
                    img[ty * TH + j][tx * TW:(tx + 1) * TW] = list(t[j])
        return img


def layout(m):
    # ---------------- roads
    m.run_h('avenue_EW', 0, 51, 18)
    m.run_v('avenue_NS', 28, 0, 39)
    m.road('avenue_NESW', 28, 18)
    m.road('avenue_EW_zebra', 27, 18)
    m.road('avenue_EW_zebra', 32, 18)
    m.road('avenue_NS_zebra', 28, 17)
    m.road('avenue_NS_zebra', 28, 22)

    m.run_h('street_EW', 0, 51, 6)
    m.run_v('street_NS', 10, 0, 39)
    m.road('street_NESW', 10, 6)
    m.road('avenue_EW+street_NS', 10, 18)
    m.road('avenue_EW_zebra', 9, 18)
    m.road('avenue_EW_zebra', 12, 18)
    m.road('avenue_NS+street_EW', 28, 6)

    m.run_h('street_EW', 0, 43, 32)
    m.road('street_NESW', 10, 32)
    m.road('avenue_NS+street_EW', 28, 32)
    m.road('street_NW', 44, 32)
    m.run_v('street_NS', 44, 22, 31)
    m.road('avenue_EW+street_S', 44, 18)

    m.road('street_NEW', 40, 6)                  # short dead-end street going north
    m.run_v('street_NS', 40, 2, 5)
    m.road('street_S', 40, 0)

    m.run_v('alley_NS', 20, 8, 17)               # alleys in the NW block
    m.road('street_EW+alley_S', 20, 6)
    m.road('avenue_EW+alley_N', 20, 18)
    m.run_h('alley_EW', 12, 27, 12)
    m.road('street_NS+alley_E', 10, 12)
    m.road('alley_NESW', 20, 12)
    m.road('avenue_NS+alley_W', 28, 12)

    m.road('avenue_NS+street_E', 28, 25)         # cul-de-sac
    m.run_h('street_EW', 32, 35, 25)
    m.road('street_W', 36, 25)

    m.road('avenue_EW+alley_S', 40, 18)          # alley with a bend and a dead end
    m.run_v('alley_NS', 40, 22, 27)
    m.road('alley_NE', 40, 28)
    m.road('alley_EW', 41, 28)
    m.road('alley_W', 42, 28)

    # ---------------- manholes and drains
    for name, spots in (
            ('avenue_EW_manhole', [(4, 18), (38, 18)]), ('avenue_EW_drain', [(16, 18), (48, 18)]),
            ('avenue_NS_manhole', [(28, 3), (28, 29)]), ('avenue_NS_drain', [(28, 10), (28, 36)]),
            ('street_EW_manhole', [(3, 6), (36, 6), (18, 32)]), ('street_EW_drain', [(15, 6), (46, 6), (5, 32), (38, 32)]),
            ('street_NS_manhole', [(10, 15), (10, 36)]), ('street_NS_drain', [(10, 2), (10, 26)]),
            ('alley_NS_manhole', [(20, 9)]), ('alley_NS_drain', [(20, 15), (40, 24)]),
            ('alley_EW_drain', [(14, 12)]), ('alley_EW_manhole', [(25, 12)]),
            ('asphalt_manhole', [(30, 19)])):
        for x, y in spots:
            m.road(name, x, y)

    # ---------------- buildings (x, y, style, w, roof rows, floors, props)
    b = m.bld
    # north strip, fronts on the north street
    b(0, 0, 'office', 6, 4, 2, {(1, 1): 'ac', (3, 2): 'hatch', (4, 1): 'ac'})
    b(6, 0, 'brick', 4, 4, 2, {(1, 1): 'tank', (2, 2): 'chimney'})
    b(12, 0, 'tower', 6, 3, 3, {(1, 1): 'ac', (3, 1): 'dish', (4, 1): 'ac'})
    b(18, 0, 'house', 4, doors=(1,))
    b(18, 3, 'house', 4, props={(2, 0): 'chimney'}, doors=(2,))
    b(22, 0, 'brick', 6, 3, 3, {(1, 1): 'skylight', (3, 1): 'tank'})
    b(32, 0, 'shed', 8, 5, 1, {(1, 1): 'skylight', (3, 1): 'skylight', (5, 1): 'skylight',
                               (1, 3): 'skylight', (3, 3): 'skylight', (5, 3): 'skylight', (6, 2): 'vent'})
    b(42, 0, 'office', 5, 4, 2, {(1, 1): 'skylight', (1, 2): 'skylight', (3, 2): 'ac'})
    b(47, 0, 'house', 5, props={(2, 0): 'chimney'}, doors=(3,))
    b(47, 3, 'house', 5, doors=(1,))
    # west strip
    b(0, 8, 'brick', 5, 5, 2, {(1, 1): 'tank', (3, 2): 'chimney', (2, 3): 'skylight'})
    b(0, 15, 'house', 5, props={(1, 0): 'chimney'}, doors=(2,))
    b(5, 8, 'office', 5, 8, 2, {(1, 1): 'ac', (3, 1): 'ac', (2, 3): 'hatch', (1, 5): 'skylight', (3, 5): 'skylight'})
    m.park(0, 22, 10, 5, {(1, 1): 'tree', (3, 1): 'tree', (5, 2): 'flowers', (7, 1): 'tree',
                          (2, 3): 'flowers', (8, 3): 'tree', (6, 3): 'tree'})
    b(0, 27, 'house', 5, doors=(1,))
    b(5, 27, 'house', 5, props={(3, 0): 'chimney'}, doors=(3,))
    m.ground(0, 30, 9, 30, 'lot_bay_n')
    m.ground(0, 31, 9, 31, 'lot')
    b(0, 34, 'house', 5, doors=(2,))
    b(5, 34, 'house', 5, doors=(2,))
    b(0, 37, 'house', 5, props={(1, 0): 'chimney'}, doors=(3,))
    b(5, 37, 'house', 5, doors=(1,))
    # NW block (between the alleys)
    b(12, 8, 'brick', 4, 3, 1, {(1, 1): 'tank'})
    b(16, 8, 'office', 4, 3, 1, {(2, 1): 'ac'})
    b(21, 8, 'shed', 7, 3, 1, {(1, 1): 'skylight', (3, 1): 'skylight', (5, 1): 'vent'})
    b(12, 13, 'brick', 8, 3, 2, {(2, 1): 'tank', (5, 1): 'skylight'})
    b(21, 13, 'office', 7, 4, 1, {(1, 1): 'ac', (2, 1): 'ac', (4, 2): 'hatch', (5, 1): 'skylight'})
    # NE block: tower with helipad + park
    b(32, 8, 'tower', 8, 5, 3, {(1, 1): 'helipad', (4, 1): 'ac', (5, 1): 'ac', (5, 3): 'dish'})
    m.ground(32, 16, 39, 17, 'plaza')
    park = {(1, 1): 'tree', (3, 1): 'tree', (8, 1): 'tree', (10, 1): 'tree',
            (2, 2): 'flowers', (9, 2): 'flowers', (2, 6): 'flowers', (9, 6): 'flowers',
            (1, 7): 'tree', (3, 7): 'tree', (8, 7): 'tree', (10, 8): 'tree', (4, 8): 'tree'}
    for yy in range(1, 9):
        park[(6, yy)] = 'path_v'
    for xx in range(1, 11):
        park[(xx, 4)] = 'path_h'
    park[(6, 4)] = 'fountain'
    m.park(40, 8, 12, 10, park)
    # SW block: houses and two small blocks
    for yy in (22, 25):
        for xx, door in ((12, 1), (16, 2), (20, 1), (24, 2)):
            props = {(2, 0): 'chimney'} if (xx + yy) % 3 == 0 else None
            b(xx, yy, 'house', 4, props=props, doors=(door,))
    b(12, 28, 'brick', 8, 2, 2)
    b(20, 28, 'office', 8, 2, 2)
    # SE block around the cul-de-sac and the bent alley
    b(32, 22, 'house', 4, doors=(1,))
    b(36, 22, 'house', 4, props={(1, 0): 'chimney'}, doors=(2,))
    m.ground(38, 25, 39, 26, 'plaza')
    b(32, 27, 'shed', 8, 4, 1, {(1, 1): 'skylight', (3, 1): 'skylight', (5, 1): 'skylight', (6, 2): 'vent'})
    b(41, 22, 'office', 3, 4, 2, {(1, 1): 'ac'})
    b(41, 29, 'house', 3, doors=(1,))
    m.ground(43, 28, 43, 28, 'plaza')
    # east strip
    b(46, 22, 'brick', 6, 6, 2, {(1, 1): 'tank', (4, 1): 'tank', (2, 3): 'skylight', (4, 4): 'chimney'})
    m.ground(46, 30, 51, 30, 'lot_bay_n')
    m.ground(46, 31, 51, 33, 'lot')
    # south strip
    b(12, 34, 'office', 6, 4, 2, {(1, 1): 'hatch', (3, 1): 'ac', (4, 2): 'ac'})
    for xx, door in ((18, 2), (23, 1)):
        b(xx, 34, 'house', 5, doors=(door,))
        b(xx, 37, 'house', 5, props={(2, 0): 'chimney'}, doors=(door + 1,))
    b(32, 34, 'shed', 10, 5, 1, {(1, 1): 'skylight', (3, 1): 'skylight', (5, 1): 'skylight',
                                 (7, 1): 'skylight', (8, 3): 'vent', (2, 3): 'vent'})
    b(42, 34, 'tower', 10, 3, 3, {(1, 1): 'ac', (2, 1): 'ac', (4, 1): 'dish', (7, 1): 'ac'})
    m.ground(0, 0, MAP_W - 1, MAP_H - 1, 'plaza')


# sprites on top of the map: (sheet, tag, frame in tag, x px, y row) of the frame's top-left.
# Right-hand traffic. Lane rows/columns come from the road cross-sections (see roads.py).
CARS = [
    # on the CPC screen
    ('taxi', 'E', 176, 321),                  # avenue, eastbound
    ('police_flash', 'W', 270, 291),          # avenue, westbound, stopped at the zebra
    ('sedan', 'S', 232, 200),                 # avenue, southbound
    ('sports', 'N', 247, 362),                # avenue, northbound
    ('van', 'SW', 226, 292),                  # turning right into the avenue
    ('wreck', 'S', 320, 364),                 # burnt out in the bent alley
    # rest of the city
    ('sedan', 'E', 120, 109), ('taxi', 'W', 330, 98), ('police', 'N', 87, 420),
    ('van', 'S', 81, 150), ('sports', 'E', 300, 526), ('sedan', 'W', 275, 402),
    ('taxi', 'N', 240, 40), ('van', 'SE', 354, 335), ('sedan', 'N', 368, 481), ('taxi', 'N', 392, 481),
    ('van', 'N', 16, 481),
]
PEDS = [
    # on the CPC screen
    ('tourist_N', 0, 258, 303),               # crossing in front of the police car
    ('suit_S', 2, 218, 325),                  # crossing the west zebra
    ('suit_E', 0, 190, 285), ('dress_W', 1, 300, 285),          # north sidewalk
    ('tourist_E', 2, 180, 343), ('punk_W', 0, 290, 343),        # south sidewalk
    ('suit_down', 0, 206, 343),
    ('dress_S', 0, 223, 220), ('cop_N', 1, 252, 240),           # avenue sidewalks
    ('tourist_S', 1, 280, 262), ('dress_W', 2, 294, 270), ('punk_E', 0, 304, 258),  # plaza
    ('cop_S', 1, 321, 348),                   # looking at the wreck
    # rest of the city
    ('punk_S', 2, 162, 160), ('suit_N', 1, 370, 232), ('tourist_E', 0, 340, 196),
    ('dress_E', 1, 30, 93), ('suit_W', 2, 60, 119), ('cop_E', 0, 140, 509),
    ('tourist_W', 1, 400, 285), ('dress_N', 0, 79, 250),
]


def blit(img, frame, x, y):
    """Draw a sprite frame; pen 0 is transparent."""
    for j, row in enumerate(frame):
        for i, pen in enumerate(row):
            if pen and 0 <= y + j < len(img) and 0 <= x + i < len(img[0]):
                img[y + j][x + i] = pen


def render(img, path, x0, y0, w, h, scale):
    cv = Canvas(w * 2 * scale, h * scale)
    cv.blit_pens([row[x0:x0 + w] for row in img[y0:y0 + h]], 0, 0, 2 * scale, scale)
    cv.save(path)


def build(rbank, pieces, bbank, kit):
    m = CityMap(rbank, pieces, bbank, kit)
    layout(m)
    return m


def render_all(m, out_dir, cars, peds):
    """cars, peds: sprites.Sheet objects."""
    img = m.image()
    for tag, heading, x, y in CARS:
        blit(img, cars.tag(tag)[DIRS.index(heading)], x, y)
    for tag, i, x, y in PEDS:
        blit(img, peds.tag(tag)[i], x, y)
    render(img, out_dir + '/mockup_city.png', 0, 0, MAP_W * TW, MAP_H * TH, 2)
    # one CPC screen: 160x200 Mode 0 pixels = 20 x 12.5 tiles
    render(img, out_dir + '/mockup_screen.png', 21 * TW, 11 * TH + 8, 160, 200, 3)
    return m
