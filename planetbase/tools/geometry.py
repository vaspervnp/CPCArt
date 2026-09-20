"""Γεωμετρία θόλου, δακτυλίου, διαδρόμων και σημείων σύνδεσης.

Όλα παραμετρικά. Οπτικές συντεταγμένες: το x διπλασιάζεται (αναλογία 2:1),
ώστε ένας «κύκλος» να βγαίνει στρογγυλός στην οθόνη.
"""

import math

from palette import (PEN_OUTSIDE, PEN_DOME_FLOOR, PEN_DOME_EDGE,
                     PEN_CORR_FLOOR, PEN_CORR_EDGE)

# Κατηγορίες pixel
OUTSIDE, DOME, CORRIDOR = 0, 1, 2

CORRIDOR_W = 8                     # οπτικό πλάτος δακτυλίου/διαδρόμου

# Τα τρία μεγέθη θόλου: (κωδικός, οπτική διάμετρος).
# Το μεγάλο γεμίζει ακριβώς τεταρτημόριο 32x64 (πλαίσιο 64x128, οπτικά 128x128).
DOME_SIZES = [("s", 48), ("m", 80), ("l", 112)]

MAX_QUAD_W, MAX_QUAD_H = 32, 64    # το τεταρτημόριο του μεγάλου θόλου

# Οι 8 κατευθύνσεις σύνδεσης, με το μοναδιαίο διάνυσμά τους σε ΟΠΤΙΚΕΣ συντεταγμένες
DIRS = [
    ("n",   0.0, -1.0), ("ne",  0.7071, -0.7071),
    ("e",   1.0,  0.0), ("se",  0.7071,  0.7071),
    ("s",   0.0,  1.0), ("sw", -0.7071,  0.7071),
    ("w",  -1.0,  0.0), ("nw", -0.7071, -0.7071),
]


def frame_size(diameter, uniform):
    """Διαστάσεις πλαισίου (pixels, γραμμές) για δεδομένη οπτική διάμετρο θόλου."""
    if uniform:
        return MAX_QUAD_W * 2, MAX_QUAD_H * 2
    outer = diameter + 2 * CORRIDOR_W          # οπτική διάμετρος με δακτύλιο
    return outer // 2, outer


def classify_frame(diameter, fw, fh):
    """Πίνακας [fh][fw] με OUTSIDE / DOME / CORRIDOR."""
    cx, cy = fw / 2, fh / 2
    r_dome = diameter / 2
    r_corr = r_dome + CORRIDOR_W
    out = []
    for y in range(fh):
        row = []
        vy = (y + 0.5) - cy
        for x in range(fw):
            vx = (x + 0.5) * 2 - 2 * cx
            r = math.hypot(vx, vy)
            row.append(DOME if r <= r_dome else CORRIDOR if r <= r_corr else OUTSIDE)
        out.append(row)
    return out


def _edges(cls, fw, fh, keep):
    """Χρωματισμός μιας μόνο κατηγορίας· ό,τι άλλο γίνεται διαφανές (pen 0).

    Άκρη = κάποιος από τους 4 γείτονες ανήκει σε άλλη κατηγορία. Γείτονας έξω
    από το πλαίσιο μετρά ως OUTSIDE — έτσι η άκρη κλείνει και στα όρια.
    """
    floor, edge = ((PEN_DOME_FLOOR, PEN_DOME_EDGE) if keep == DOME
                   else (PEN_CORR_FLOOR, PEN_CORR_EDGE))

    def at(x, y):
        return cls[y][x] if 0 <= x < fw and 0 <= y < fh else OUTSIDE

    pens = []
    for y in range(fh):
        row = []
        for x in range(fw):
            if cls[y][x] != keep:
                row.append(PEN_OUTSIDE)
                continue
            is_edge = any(at(x + dx, y + dy) != keep
                          for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            row.append(edge if is_edge else floor)
        pens.append(row)
    return pens


def dome_pens(cls, fw, fh):
    """Μόνο ο θόλος. Ο δακτύλιος και το έξω είναι διαφανή."""
    return _edges(cls, fw, fh, DOME)


def ring_pens(cls, fw, fh):
    """Μόνο ο δακτύλιος — «ο διάδρομος χωρίς το κεντρικό κομμάτι του»."""
    return _edges(cls, fw, fh, CORRIDOR)


def quadrants(pens, fw, fh):
    """Το πλαίσιο κομμένο σε 4 τεταρτημόρια: nw, ne, sw, se."""
    qw, qh = fw // 2, fh // 2
    out = []
    for name, ox, oy in (("nw", 0, 0), ("ne", qw, 0), ("sw", 0, qh), ("se", qw, qh)):
        out.append((name, [row[ox:ox + qw] for row in pens[oy:oy + qh]]))
    return out


# --------------------------------------------------------------------------
# Ευθύγραμμοι και διαγώνιοι διάδρομοι
# --------------------------------------------------------------------------

CORR_PX = CORRIDOR_W // 2          # πλάτος διαδρόμου σε pixels (4)


def corr_h():
    """Οριζόντιος διάδρομος 8x8 — τοιχώματα πάνω και κάτω."""
    return [[PEN_CORR_EDGE if y in (0, CORRIDOR_W - 1) else PEN_CORR_FLOOR
             for _ in range(8)] for y in range(CORRIDOR_W)]


def corr_v():
    """Κάθετος διάδρομος 4x16 — τοιχώματα αριστερά και δεξιά."""
    return [[PEN_CORR_EDGE if x in (0, CORR_PX - 1) else PEN_CORR_FLOOR
             for x in range(CORR_PX)] for _ in range(16)]


DIAG_W, DIAG_H = 16, 16            # το tile
DIAG_STEP_X, DIAG_STEP_Y = 8, 16   # βήμα τοποθέτησης = 45° οπτικά

# Τα tiles ΕΠΙΚΑΛΥΠΤΟΝΤΑΙ κατά 8 pixels· η μάσκα φροντίζει να κουμπώνουν χωρίς
# κενά. Γι' αυτό το tile είναι 16 φαρδύ ενώ το βήμα είναι 8.


def corr_diag(down_right=True):
    """Διαγώνιος διάδρομος 16x16, οπτικά 45°, με οπτικό πλάτος CORRIDOR_W.

    Τοποθετείται με βήμα (±DIAG_STEP_X, +DIAG_STEP_Y)· η επικάλυψη των 8 pixels
    κλείνει τη σκάλα που θα άφηναν εφαπτόμενα tiles.
    """
    half = CORRIDOR_W / 2 * math.sqrt(2)       # οριζόντιο ημιπλάτος της ζώνης
    offset = DIAG_W                            # οπτικό κέντρο στην πάνω γραμμή

    def band(x, y):
        vx = (x + 0.5) * 2
        vy = (y + 0.5)
        if not down_right:
            vx = 2 * DIAG_W - vx
        return abs(vx - vy - offset / 2) <= half

    cls = [[CORRIDOR if band(x, y) else OUTSIDE for x in range(DIAG_W)]
           for y in range(DIAG_H)]

    def at(x, y):
        if 0 <= x < DIAG_W and 0 <= y < DIAG_H:
            return cls[y][x]
        # έξω από το tile συνεχίζει το γειτονικό: η ζώνη δεν κλείνει στα άκρα
        return CORRIDOR if band(min(max(x, 0), DIAG_W - 1),
                                min(max(y, 0), DIAG_H - 1)) and (
            0 <= x < DIAG_W or 0 <= y < DIAG_H) else OUTSIDE

    pens = []
    for y in range(DIAG_H):
        row = []
        for x in range(DIAG_W):
            if cls[y][x] != CORRIDOR:
                row.append(PEN_OUTSIDE)
                continue
            is_edge = any(at(x + dx, y + dy) != CORRIDOR
                          for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            row.append(PEN_CORR_EDGE if is_edge else PEN_CORR_FLOOR)
        pens.append(row)
    return pens


# --------------------------------------------------------------------------
# Σημεία σύνδεσης
# --------------------------------------------------------------------------

CONN_W, CONN_H = 4, 8              # ακριβώς η διατομή ενός διαδρόμου


def connector(name):
    """Η πόρτα στο τοίχωμα του δακτυλίου, για μία από τις 8 κατευθύνσεις.

    Είναι ΚΟΜΜΑΤΙ του ίδιου του διαδρόμου, όχι ξεχωριστό σχέδιο: έτσι τα
    τοιχώματα και το δάπεδο συνεχίζουν χωρίς ασυνέχεια εκεί που ο διάδρομος
    συναντά τον δακτύλιο.
    """
    if name in ("n", "s"):
        return [row[:] for row in corr_v()[:CONN_H]]            # κάθετη διατομή
    if name in ("e", "w"):
        return [row[:CONN_W] for row in corr_h()]               # οριζόντια διατομή
    # Διαγώνια: η ίδια ζώνη 45° με τον corr_diag, αλλά με τις παραστάδες
    # υπολογισμένες ΜΕΣΑ στο κουτί — αλλιώς η ζώνη το γεμίζει ολόκληρο και η
    # πόρτα διαβάζεται σαν σκέτη τρύπα στον δακτύλιο.
    down_right = name in ("se", "nw")
    half = CORRIDOR_W / 2 * math.sqrt(2)
    cx, cy = CONN_W / 2, CONN_H / 2
    pens = []
    for y in range(CONN_H):
        vy = (y + 0.5) - cy
        row = []
        for x in range(CONN_W):
            vx = (x + 0.5) * 2 - 2 * cx
            if not down_right:
                vx = -vx
            d = abs(vx - vy)
            if d > half:
                row.append(PEN_OUTSIDE)
            elif d > half - 2:
                row.append(PEN_CORR_EDGE)
            else:
                row.append(PEN_CORR_FLOOR)
        pens.append(row)
    return pens


def conn_points(diameter, fw, fh):
    """Πού κουμπώνει κάθε κατεύθυνση πάνω στον δακτύλιο ενός θόλου.

    Επιστρέφει (κατεύθυνση, x, y): η πάνω-αριστερή γωνία του connector μέσα στο
    πλαίσιο του θόλου, σε pixels/γραμμές.
    """
    cx, cy = fw / 2, fh / 2
    r = diameter / 2 + CORRIDOR_W / 2           # στο μέσο του δακτυλίου
    out = []
    for name, dx, dy in DIRS:
        vx, vy = dx * r, dy * r                 # οπτικές συντεταγμένες
        x = int(round(cx + vx / 2 - CONN_W / 2))
        y = int(round(cy + vy - CONN_H / 2))
        x = max(0, min(fw - CONN_W, x))
        y = max(0, min(fh - CONN_H, y))
        out.append((name, x & ~1, y))           # ζυγό x = ακέραιο byte
    return out


# --------------------------------------------------------------------------
# Διάταξη εσωτερικού θόλου
# --------------------------------------------------------------------------
# Όλες οι θέσεις είναι σχετικές με το ΚΕΝΤΡΟ του θόλου, σε pixels/γραμμές.
# Τα x είναι ζυγά (ακέραια bytes). Στοιβάζονται κάθετα: εικονίδιο τύπου πάνω,
# μηχανήματα στη μέση, επικάλυμμα πληρότητας κάτω.

MACHINE_W, MACHINE_H = 12, 22      # οπτικά 24x22 — σχεδόν τετράγωνο
MACHINE_GAP = 2
MAX_MACHINES = 8

MACHINE_COUNT = {"s": 1, "m": 4, "l": 8}

# Στον μεγάλο θόλο τα μηχανήματα μπαίνουν ΠΕΡΙΜΕΤΡΙΚΑ, σε κύκλο αυτής της
# οπτικής ακτίνας, με το εικονίδιο τύπου στο κέντρο. Στον μεσαίο και τον μικρό
# μπαίνουν στη ΜΕΣΗ, με το εικονίδιο από πάνω.
PERIM_R = 38                       # η μέγιστη που χωράει με μηχάνημα 12x22

_FLOOR = {}


def _floor(diameter, fw, fh):
    key = (diameter, fw, fh)
    if key not in _FLOOR:
        _FLOOR[key] = dome_pens(classify_frame(diameter, fw, fh), fw, fh)
    return _FLOOR[key]


def _fits(dp, fw, fh, rects):
    """Όλα τα ορθογώνια πέφτουν σε δάπεδο θόλου (όχι άκρη) χωρίς επικαλύψεις."""
    taken = set()
    for x, y, w, h in rects:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if not (0 <= xx < fw and 0 <= yy < fh):
                    return False
                if dp[yy][xx] != PEN_DOME_FLOOR:
                    return False
                if (xx, yy) in taken:
                    return False
                taken.add((xx, yy))
    return True


def interior(code, diameter, fw, fh):
    """Απόλυτες θέσεις μέσα στο πλαίσιο: (όνομα, x, y, w, h). Τα x είναι ζυγά.

    Στον μεγάλο θόλο το εικονίδιο πάει στο κέντρο και τα μηχανήματα περιμετρικά.
    Στους άλλους δύο στοιβάζονται κάθετα — και επειδή το εικονίδιο κλιμακώνεται,
    η κατακόρυφη θέση της στοίβας δεν κεντράρεται τυφλά: δοκιμάζονται θέσεις
    γύρω από το κέντρο και κρατιέται η πρώτη που χωράει ολόκληρη.
    """
    from icons import ICON_SIZES
    iw = ih = ICON_SIZES[code]
    cx, cy = fw // 2, fh // 2
    n = MACHINE_COUNT[code]
    out = []

    if code == "l":
        out.append(("icon", (cx - iw // 2) & ~1, cy - ih // 2, iw, ih))
        for k in range(n):
            a = math.radians(90 + k * 45)          # ξεκινά από Βορρά, δεξιόστροφα
            vx, vy = PERIM_R * math.cos(a), -PERIM_R * math.sin(a)
            x = int(cx + vx / 2 - MACHINE_W / 2) & ~1
            y = int(round(cy + vy - MACHINE_H / 2))
            out.append((f"machine{k}", x, y, MACHINE_W, MACHINE_H))
        return out

    cols = 2 if n > 1 else 1
    rows = -(-n // cols)
    tot = ih + MACHINE_GAP + rows * MACHINE_H + (rows - 1) * MACHINE_GAP
    gw = cols * MACHINE_W + (cols - 1) * MACHINE_GAP
    gx = int(cx - gw / 2) & ~1
    ix = (cx - iw // 2) & ~1

    def stack(top):
        r = [("icon", ix, top, iw, ih)]
        for k in range(n):
            i, j = k % cols, k // cols
            r.append((f"machine{k}",
                      gx + i * (MACHINE_W + MACHINE_GAP),
                      top + ih + MACHINE_GAP + j * (MACHINE_H + MACHINE_GAP),
                      MACHINE_W, MACHINE_H))
        return r

    dp = _floor(diameter, fw, fh)
    mid = cy - tot // 2
    for delta in range(0, fh):                 # από το κέντρο προς τα έξω
        for top in {mid - delta, mid + delta}:
            cand = stack(top)
            if _fits(dp, fw, fh, [(x, y, w, h) for _, x, y, w, h in cand]):
                return cand
    raise ValueError(f"{code}: δεν χωράει εικονίδιο {iw}x{ih} με {n} μηχανήματα "
                     f"{MACHINE_W}x{MACHINE_H} στο πλαίσιο {fw}x{fh}")


# --------------------------------------------------------------------------
# Θέσεις αποίκων στους διαδρόμους
# --------------------------------------------------------------------------
# Οι άνθρωποι δεν είναι πια μέσα στον θόλο αλλά πάνω στον δακτύλιο, ανάμεσα
# στα σημεία σύνδεσης (μετατοπισμένες κατά 22,5° ώστε να μην πέφτουν σε πόρτα).

CORR_SLOTS = 8
SLOT_W, SLOT_H = 4, 8              # ίδιο κουτί με τα σημεία σύνδεσης

# Σειρά γεμίσματος: σκορπισμένη, για να μη φαίνεται ότι στοιβάζονται
SLOT_FILL = [0, 4, 2, 6, 1, 5, 3, 7]


def corridor_slots(diameter, fw, fh):
    """(k, x, y) της πάνω-αριστερής γωνίας κάθε θέσης αποίκου πάνω στον δακτύλιο."""
    cx, cy = fw / 2, fh / 2
    r = diameter / 2 + CORRIDOR_W / 2
    out = []
    for k in range(CORR_SLOTS):
        a = math.radians(22.5 + k * 45)
        vx, vy = r * math.cos(a), -r * math.sin(a)
        x = int(round(cx + vx / 2 - SLOT_W / 2)) & ~1
        y = int(round(cy + vy - SLOT_H / 2))
        out.append((k, max(0, min(fw - SLOT_W, x)), max(0, min(fh - SLOT_H, y))))
    return out
