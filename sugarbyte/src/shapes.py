"""Τα σχήματα των candies: σιλουέτα + φωτοσκίαση, υπολογισμένα, όχι ASCII art.

Κάθε σχήμα είναι μια συνάρτηση d(u, v): μέσα όταν d <= 1. Τα u, v είναι
κανονικοποιημένα στο *κουτί του σώματος* του κελιού, που είναι τετράγωνο στην
οθόνη — άρα u και v μετριούνται στις ίδιες «μονάδες» και τα σχήματα δεν
παραμορφώνονται από την αναλογία 2:1 του Mode 0.

Το φως έρχεται πάνω-αριστερά: σκιά όπου u + v > SHADE_AT.
"""
import math

from cpcgfx import PEN_HI, PEN_GREY, PEN_LINE, blank

SHADE_AT = 0.30             # η γραμμή σκιάς του σφαιρικού φωτισμού
HI_C     = (-0.40, -0.44)   # κέντρο ανταύγειας
HI_R     = (0.30, 0.28)     # ακτίνες ανταύγειας


# ------------------------------------------------------------- οι σιλουέτες

def circle(u, v):
    """ΚΟΚΚΙΝΟ — γλυκό μπαλάκι."""
    return math.hypot(u, v)


def hexagon(u, v):
    """ΠΟΡΤΟΚΑΛΙ — εξάγωνη καραμέλα, μύτες αριστερά-δεξιά."""
    return max(abs(v), abs(u) + 0.5 * abs(v))


def rounded(u, v):
    """ΚΙΤΡΙΝΟ — τετράγωνο ζαχαρωτό με στρογγυλεμένες γωνίες."""
    n = 5.0
    return (abs(u) ** n + abs(v) ** n) ** (1.0 / n)


def diamond(u, v):
    """ΠΡΑΣΙΝΟ — ρόμβος."""
    return abs(u) + abs(v)


def drop(u, v):
    """ΜΠΛΕ — δάκρυ: κώνος με φαρδιούς ώμους πάνω, φουσκωτός πάτος."""
    if v <= 0.10:
        r = 0.78 * (max(0.0, v + 1.0) / 1.10) ** 0.70
    else:
        t = (v - 0.10) / 0.90
        r = 0.78 * math.sqrt(max(0.0, 1.0 - t * t)) ** 0.62
    return 9.9 if r <= 0.04 else abs(u) / r


def wrapped(u, v):
    """Το περιτύλιγμα — ίδιο για όλα τα χρώματα, όπως στο Candy Crush.

    Φαρδύ μαξιλάρι με δύο στριφτές άκρες. Οι άκρες πάνε στον *κάθετο* άξονα
    επειδή το Mode 0 έχει διπλή ανάλυση εκεί: ίδιο μέγεθος στην οθόνη, αλλά
    διπλάσια pixels για να φανεί το χωνί.
    """
    av = abs(v)
    if av <= 0.52:
        n = 6.0
        return (abs(u / 0.95) ** n + abs(v / 0.52) ** n) ** (1.0 / n)
    if av <= 0.97:
        t = (av - 0.52) / 0.45
        return abs(u) / (0.22 + 0.68 * t)
    return 9.9


# Η καρδιά είναι το ένα σχήμα που ο υπολογισμός δεν το βγάζει καθαρό στα
# 10x20: με implicit καμπύλη οι δύο καμπούρες έρχονται 1 pixel η κάθε μία.
# Ζωγραφισμένη με το χέρι, αλλά περνάει από τον ίδιο ζωγράφο.
HEART_ART = """
------------
------------
--XX----XX--
-XXXX--XXXX-
-XXXXXXXXXX-
-XXXXXXXXXX-
-XXXXXXXXXX-
-XXXXXXXXXX-
-XXXXXXXXXX-
-XXXXXXXXXX-
--XXXXXXXX--
--XXXXXXXX--
---XXXXXX---
---XXXXXX---
---XXXXXX---
----XXXX----
----XXXX----
----XXXX----
-----XX-----
-----XX-----
------------
------------
------------
"""


def mask_from_art(art, transparent='-'):
    """ASCII μάσκα -> συνάρτηση σχήματος, για ό,τι ζωγραφίζεται με το χέρι.

    Το Box είναι γραμμικός μετασχηματισμός, άρα αντιστρέφεται και η μάσκα
    μπαίνει στον ίδιο ζωγράφο με τα υπολογισμένα σχήματα — ίδια φωτοσκίαση,
    ίδιο περίγραμμα, ίδιες ρίγες.
    """
    rows = [ln.strip() for ln in art.strip('\n').splitlines() if ln.strip()]
    h, w = len(rows), len(rows[0])
    assert all(len(r) == w for r in rows), 'η μάσκα δεν είναι ορθογώνια'
    grid = [[ch != transparent for ch in r] for r in rows]

    def dist(u, v):
        x = int(math.floor(u * ((w - 2) / 2.0) + w / 2.0))
        y = int(math.floor(v * ((h - 4) / 2.0) + h / 2.0))
        if 0 <= x < w and 0 <= y < h and grid[y][x]:
            return 0.0
        return 9.9
    return dist


heart = mask_from_art(HEART_ART)

# Η σειρά ΕΙΝΑΙ ο κωδικός χρώματος: κόκκινο, πορτοκαλί, κίτρινο, πράσινο,
# μπλε, μωβ — ίδια σειρά με το CANDY_PENS.
SILHOUETTES = [circle, hexagon, rounded, diamond, drop, heart]
SHAPE_NAMES = ['μπαλάκι', 'εξάγωνο', 'τετράγωνο', 'ρόμβος', 'δάκρυ', 'καρδιά']


# ------------------------------------------------------------- ο ζωγράφος

class Box:
    """Το κουτί του σώματος μέσα στο κελί: μετατρέπει pixel <-> u, v."""

    def __init__(self, w, h, inset_x=1, inset_y=2):
        self.w, self.h = w, h
        self.cx, self.cy = w / 2.0, h / 2.0
        self.rx = (w - 2 * inset_x) / 2.0
        self.ry = (h - 2 * inset_y) / 2.0

    def uv(self, x, y):
        return (x + 0.5 - self.cx) / self.rx, (y + 0.5 - self.cy) / self.ry


def render(dist, base, shade, w=12, h=24, inset=(1, 2), scale=1.0,
           line=None, highlight=True, over=None, outline=True):
    """Σιλουέτα -> εικόνα pens. Σειρά: γέμισμα, ανταύγεια, over, περίγραμμα.

    over(x, y, u, v, pen, base, shade) -> pen ή None· εκεί μπαίνουν οι ρίγες.

    line=None σημαίνει «περίγραμμα στη σκιά του candy». Με μπλε περίγραμμα
    (PEN_LINE) η ακραία γραμμή κάθε σχήματος γινόταν ολόκληρη περίγραμμα και
    πάνω στο μαύρο ταμπλό εξαφανιζόταν — το candy έδειχνε δύο μονάδες μικρότερο.
    """
    if line is None:
        line = shade
    box = Box(w, h, *inset)
    inside = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            u, v = box.uv(x, y)
            inside[y][x] = dist(u / scale, v / scale) <= 1.0

    img = blank(w, h)
    for y in range(h):
        for x in range(w):
            if not inside[y][x]:
                continue
            u, v = box.uv(x, y)
            pen = shade if (u + v) > SHADE_AT else base
            if highlight and ((u - HI_C[0]) / HI_R[0]) ** 2 + \
                             ((v - HI_C[1]) / HI_R[1]) ** 2 <= 1.0:
                pen = PEN_HI
            if over is not None:
                alt = over(x, y, u, v, pen, base, shade)
                if alt is not None:
                    pen = alt
            img[y][x] = pen

    if outline:
        for y in range(h):
            for x in range(w):
                if not inside[y][x]:
                    continue
                if (x == 0 or not inside[y][x - 1]) or \
                   (x == w - 1 or not inside[y][x + 1]) or \
                   (y == 0 or not inside[y - 1][x]) or \
                   (y == h - 1 or not inside[y + 1][x]):
                    img[y][x] = line
    return img


# ----------------------------------------------------------- οι παραλλαγές

# Οι ρίγες: 4 ζώνες 2 γραμμών οριζόντια, 3 ρίγες 1 pixel κάθετα. Και οι δύο
# δίνουν «2 μονάδες αναμμένες» στην οθόνη — η αναλογία 2:1 το κανονίζει.
# Τα ριγέ ζωγραφίζονται ΧΩΡΙΣ ανταύγεια: η λευκή βούλα θα κολλούσε στις ρίγες
# και θα γινόταν μπάλωμα.
STRIPE_ROWS = (4, 5, 9, 10, 14, 15, 19, 20)
STRIPE_COLS = (2, 5, 8)


def _stripe_pen(u, v):
    """Η ρίγα παίρνει κι αυτή φως: λευκή στο φωτεινό μισό, γκρι στο σκιερό."""
    return PEN_HI if (u + v) <= SHADE_AT else PEN_GREY


def stripes_h(x, y, u, v, pen, base, shade):
    """Ριγέ που καθαρίζει γραμμή — οριζόντιες ζώνες."""
    return _stripe_pen(u, v) if y in STRIPE_ROWS else None


def stripes_v(x, y, u, v, pen, base, shade):
    """Ριγέ που καθαρίζει κολόνα — κάθετες ρίγες."""
    return _stripe_pen(u, v) if x in STRIPE_COLS else None


def wrapper_pleats(x, y, u, v, pen, base, shade):
    """Οι πτυχές του αλουμινόχαρτου στις δύο στριφτές άκρες.

    Διαγώνια λουρίδα στο σώμα ΔΕΝ μπαίνει: θα διαβαζόταν σαν ρίγα και το
    ριγέ είναι άλλο candy. Το περιτύλιγμα το λένε οι πτυχές.
    """
    if abs(v) <= 0.52:
        return None
    if x in (4, 7):
        return shade                      # οι δύο τσακίσεις του χωνιού
    # Το λεπτό χαρτί πιάνει φως και στις δύο άκρες: η γραμμή σκιάς του
    # σώματος θα έκανε την κάτω άκρη μια σκοτεινή μουτζούρα.
    return shade if (u + 0.30 * v) > 0.45 else base
