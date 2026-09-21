"""Tiles εδάφους — ο κόσμος πάνω στον οποίο πατάνε όλα τα υπόλοιπα.

Το tile είναι 4 bytes x 16 γραμμές = 8 px x 16 γραμμές = **16x16 οπτικά**, δηλαδή
τετράγωνο στην οθόνη. Αυτό το μέγεθος κάνει τους θόλους ακριβώς 4x4, 6x6 και 8x8
tiles, τις εξωτερικές δομές 1x1 έως 4x4, και το βήμα της διαγωνίου ένα tile.

Όλα αδιαφανή (64 bytes) εκτός από το ore_overlay, που έχει μάσκα και μπαίνει
ΠΑΝΩ σε tile βουνού.

ΧΡΩΜΑΤΑ: μόνο τα 4 pens του εδάφους (7 βάση, 11 σκούρο, 12 φωτεινό, 14 νερό),
συν το 1 για το σώμα του νερού και τα 4/5 για τα θεμέλια, που είναι κατασκευή
και δεν αλλάζει με τον πλανήτη.

DITHER: στο Mode 0 το pixel είναι διπλάσιο σε πλάτος, οπότε σκακιέρα 1x1
διαβάζεται σαν ΚΑΘΕΤΕΣ ΡΙΓΕΣ. Κάθε ψηφίδα dither εδώ είναι 1 px x 2 γραμμές,
που βγαίνει οπτικά τετράγωνη.
"""

from palette import (PEN_OUTSIDE, PEN_SHADOW, PEN_CORR_FLOOR, PEN_CORR_EDGE,
                     PEN_TERRAIN, PEN_TER_DARK, PEN_TER_HIGH, PEN_WATER)

TILE_W, TILE_H = 8, 16          # pixels, γραμμές
DITHER_H = 2                    # γραμμές ανά ψηφίδα dither

# Αυτόματη επιλογή παραλλαγής από τους 4 ορθογώνιους γείτονες.
# ΤΟ BIT ΕΙΝΑΙ ΑΝΑΜΜΕΝΟ ΟΤΑΝ Ο ΓΕΙΤΟΝΑΣ ΕΙΝΑΙ ΙΔΙΑΣ ΚΛΑΣΗΣ.
N, E, S, W = 1, 2, 4, 8
AUTOTILE = 16

# Οι κλάσεις εδάφους, με τη σειρά του πίνακα tile_base.
CLASSES = [
    ("ground",     4,  False, "ομαλό χώμα, χτίσιμο επιτρεπτό"),
    ("dust",       4,  False, "σκόνη και άμμος, χτίσιμο επιτρεπτό"),
    ("rock",       4,  False, "σπασμένο έδαφος, δεν χτίζεται"),
    ("mountain",  16,  True,  "αδιάβατο ύψωμα"),
    ("water",     16,  True,  "ρηχό νερό — εκεί πάνε οι αντλίες"),
    ("deepwater",  4,  False, "μόνο στο εσωτερικό μιας μάζας νερού"),
    ("crater",     2,  False, "κρατήρας από πρόσκρουση"),
    ("foundation", 2,  False, "ισοπεδωμένη πλατφόρμα"),
]


def _rng(seed):
    """Μικρός ντετερμινιστικός γεννήτορας — ίδιο build, ίδια tiles."""
    state = (seed * 2654435761 + 12345) & 0xFFFFFFFF

    def nxt(n):
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return (state >> 8) % n
    return nxt


def _blank(pen):
    return [[pen] * TILE_W for _ in range(TILE_H)]


def _dither(pens, pen, seed, chance, skip=None):
    """Ψηφίδες 1 px x 2 γραμμές — οπτικά τετράγωνες."""
    rnd = _rng(seed)
    for y in range(0, TILE_H, DITHER_H):
        for x in range(TILE_W):
            if rnd(100) < chance and (skip is None or not skip(x, y)):
                for dy in range(DITHER_H):
                    pens[y + dy][x] = pen
    return pens


def _speckle(pens, pen, seed, count, w=1, h=DITHER_H):
    """Λίγες μεγαλύτερες κηλίδες, για σπασμένο έδαφος."""
    rnd = _rng(seed)
    for _ in range(count):
        x, y = rnd(TILE_W), rnd(TILE_H // h) * h
        for dy in range(h):
            for dx in range(w):
                if x + dx < TILE_W and y + dy < TILE_H:
                    pens[y + dy][x + dx] = pen
    return pens


# --------------------------------------------------------------------------
# Απλές παραλλαγές
# --------------------------------------------------------------------------

def ground(v):
    p = _blank(PEN_TERRAIN)
    _dither(p, PEN_TER_DARK, 100 + v, 6)
    _dither(p, PEN_TER_HIGH, 200 + v, 4)
    return p


def dust(v):
    p = _blank(PEN_TERRAIN)
    _dither(p, PEN_TER_HIGH, 300 + v, 20)
    _dither(p, PEN_TER_DARK, 400 + v, 6)
    return p


def rock(v):
    p = _blank(PEN_TERRAIN)
    _speckle(p, PEN_TER_DARK, 500 + v, 5, w=2, h=4)
    _speckle(p, PEN_TER_HIGH, 600 + v, 3, w=2, h=2)
    _dither(p, PEN_TER_DARK, 700 + v, 12)
    return p


def deepwater(v):
    p = _blank(PEN_SHADOW)
    _dither(p, PEN_OUTSIDE, 800 + v, 30)        # μαύρο = βάθος
    _speckle(p, PEN_WATER, 900 + v, 2)          # ελάχιστη λάμψη στα βαθιά
    return p


def crater(v):
    p = _blank(PEN_TERRAIN)
    cx, cy = (TILE_W - 1) / 2, (TILE_H - 1) / 2
    rx, ry = 2.2 + v * 0.4, 4.4 + v * 0.8
    for y in range(TILE_H):
        for x in range(TILE_W):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0:
                p[y][x] = PEN_TER_DARK
            elif d <= 1.35:
                p[y][x] = PEN_TER_HIGH if y < cy else PEN_TER_DARK
    _dither(p, PEN_TER_DARK, 1000 + v, 10,
            skip=lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.35)
    return p


def foundation(v):
    """Κατασκευή, όχι φυσικό έδαφος — γι' αυτό σε pens δομής που δεν αλλάζουν."""
    p = _blank(PEN_CORR_FLOOR)
    for x in range(TILE_W):
        p[0][x] = PEN_CORR_EDGE
    for y in range(TILE_H):
        p[y][0] = PEN_CORR_EDGE
    for x in range(TILE_W):
        p[TILE_H - 1][x] = PEN_SHADOW
    for y in range(TILE_H):
        p[y][TILE_W - 1] = PEN_SHADOW
    for (rx, ry) in (((2, 3), (5, 11)) if v == 0 else ((5, 3), (2, 11))):
        p[ry][rx] = PEN_CORR_EDGE
        p[ry + 1][rx] = PEN_CORR_EDGE
    return p


# --------------------------------------------------------------------------
# Autotiles
# --------------------------------------------------------------------------

def mountain(mask):
    """Γεμίζει πάντα το κελί του· η παραλλαγή αλλάζει μόνο τη σκίαση των άκρων.

    Όπου ο γείτονας ΔΕΝ είναι βουνό, μπαίνει σκοτεινή λωρίδα — η όψη του γκρεμού.
    mask 15 (παντού βουνό) δεν έχει καμία, και είναι το γέμισμα του εσωτερικού.
    """
    p = _blank(PEN_TER_HIGH)
    _dither(p, PEN_TER_DARK, 1100 + mask, 22)
    _speckle(p, PEN_TER_DARK, 1200 + mask, 2, w=2, h=2)

    def band(cells):
        for x, y in cells:
            p[y][x] = PEN_TER_DARK

    if not mask & N:
        band([(x, y) for x in range(TILE_W) for y in range(2)])
    if not mask & S:
        band([(x, y) for x in range(TILE_W) for y in range(TILE_H - 2, TILE_H)])
    if not mask & W:
        band([(0, y) for y in range(TILE_H)])
    if not mask & E:
        band([(TILE_W - 1, y) for y in range(TILE_H)])
    return p


def water(mask):
    """Σώμα νερού από pen 1, με το pen 14 ΜΟΝΟ ως λάμψη.

    Η μηχανή κυκλώνει το pen 14 σε χρονιστή για να τρεμοπαίζει το νερό. Αν ήταν
    ολόκληρη η επιφάνεια, θα στρόβιζε η λίμνη — γι' αυτό είναι σπίθες.
    Όπου ο γείτονας ΔΕΝ είναι νερό, μπαίνει ακτή. ΠΡΟΣΟΧΗ: το βαθύ νερό μετράει
    ΩΣ ΝΕΡΟ για αυτόν τον έλεγχο — αλλιώς κάθε λίμνη αποκτά ακτή γύρω από το
    βαθύ της κομμάτι, στη μέση του νερού.
    """
    p = _blank(PEN_SHADOW)
    _dither(p, PEN_OUTSIDE, 1300 + mask, 22)    # μαύρο = βάθος
    _speckle(p, PEN_WATER, 1400 + mask, 4)

    def shore(cells):
        for x, y in cells:
            p[y][x] = PEN_TERRAIN

    if not mask & N:
        shore([(x, y) for x in range(TILE_W) for y in range(2)])
    if not mask & S:
        shore([(x, y) for x in range(TILE_W) for y in range(TILE_H - 2, TILE_H)])
    if not mask & W:
        shore([(0, y) for y in range(TILE_H)])
    if not mask & E:
        shore([(TILE_W - 1, y) for y in range(TILE_H)])
    return p


def ore_overlay(v):
    """Φλέβα μεταλλεύματος, ΜΕ ΜΑΣΚΑ, πάνω από tile βουνού.

    Σε pens εικονιδίων, όχι εδάφους: το μετάλλευμα δείχνει το ίδιο σε κάθε πλανήτη.
    """
    # Όχι pen 13: στον Desert είναι το ίδιο FW με το σκούρο του εδάφους
    # και η φλέβα εξαφανιζόταν πάνω στο βουνό.
    PEN_ORE, PEN_GLINT = 8, 15
    p = _blank(PEN_OUTSIDE)
    rnd = _rng(1500 + v)
    x, y = 1 + v * 3, 1
    while y < TILE_H - 1:
        for dx in range(2):
            if 0 <= x + dx < TILE_W:
                p[y][x + dx] = PEN_ORE
                p[y + 1][x + dx] = PEN_ORE
        if rnd(100) < 40 and 0 <= x < TILE_W:
            p[y][x] = PEN_GLINT
        x = max(0, min(TILE_W - 2, x + rnd(3) - 1))
        y += 2
    return p


BUILDERS = {"ground": ground, "dust": dust, "rock": rock, "mountain": mountain,
            "water": water, "deepwater": deepwater, "crater": crater,
            "foundation": foundation}


def build_class(name):
    count = next(c for n, c, _, _ in CLASSES if n == name)
    return [(f"tile_{name}_{i}", BUILDERS[name](i)) for i in range(count)]


def build_ore():
    return [(f"ore_overlay_{i}", ore_overlay(i)) for i in range(2)]
