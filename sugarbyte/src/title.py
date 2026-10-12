"""Ο τίτλος και το πλαίσιο του overscan.

Η οθόνη του παιχνιδιού είναι 192x248 σε σελίδα 32 KB: πάνω ο τίτλος (192x32),
γύρω-γύρω κορδόνι από ζαχαρωτό, και στη μέση τα 160x192 του παιχνιδιού.

Τα γράμματα δεν είναι ASCII art: είναι φτιαγμένα από μπάρες και στύλους σε
κουτί 14x26, με μία πέρασμα στρογγυλέματος στις γωνίες. Έτσι το πάχος της
πένας αλλάζει από ένα σημείο και όλα τα γράμματα ακολουθούν.
"""
from cpcgfx import (CANDY_PENS, PEN, PEN_GREY, PEN_HI, PEN_LINE, PEN_MASK,
                    SpriteSet, blank)

# --------------------------------------------------------------- γεωμετρία
TITLE_W, TITLE_H = 192, 32      # πάνω μπορντούρα
EDGE_W, EDGE_H = 16, 24         # πλακάκι πλαϊνής και κάτω μπορντούρας

GLYPH_W, GLYPH_H = 14, 26       # κουτί γράμματος
STEM = 3                        # πάχος στύλου σε pixels   (6 μονάδες οθόνης)
BAR = 5                         # πάχος μπάρας σε γραμμές  (5 μονάδες οθόνης)
LX0, LX1 = 1, 3                 # αριστερός στύλος
RX0, RX1 = 10, 12               # δεξιός στύλος
CX0, CX1 = 5, 8                 # κεντρικός στύλος
TY0, TY1 = 0, 4                 # πάνω μπάρα
MY0, MY1 = 10, 14               # μεσαία μπάρα
BY0, BY1 = 21, 25               # κάτω μπάρα

# Κάθε γράμμα: λίστα από ορθογώνια (x0, y0, x1, y1) χωρίς αποκλεισμό.
GLYPHS = {
    'S': [(1, TY0, 12, TY1), (LX0, 3, LX1, 12), (1, MY0, 12, MY1),
          (RX0, 12, RX1, 23), (1, BY0, 12, BY1)],
    'U': [(LX0, 0, LX1, 23), (RX0, 0, RX1, 23), (1, BY0, 12, BY1)],
    'G': [(1, TY0, 12, TY1), (LX0, 3, LX1, 23), (1, BY0, 12, BY1),
          (RX0, 13, RX1, 23), (6, 13, 12, 17)],
    'A': [(1, TY0, 12, TY1), (LX0, 3, LX1, 25), (RX0, 3, RX1, 25),
          (1, 11, 12, 15)],
    'R': [(LX0, 0, LX1, 25), (1, TY0, 12, TY1), (RX0, 3, RX1, 12),
          (1, MY0, 12, MY1)],
    'B': [(LX0, 0, LX1, 25), (1, TY0, 12, TY1), (RX0, 3, RX1, 12),
          (1, MY0, 12, MY1), (RX0, 13, RX1, 23), (1, BY0, 12, BY1)],
    'Y': [(CX0, 12, CX1, 25)],
    'T': [(1, TY0, 12, TY1), (CX0, 3, CX1, 25)],
    'E': [(LX0, 0, LX1, 25), (1, TY0, 12, TY1), (1, MY0, 10, MY1),
          (1, BY0, 12, BY1)],
}

# Διαγώνιες: λίστες σημείων, κάθε σημείο βάφει DIAG pixels x 2 γραμμές.
# Το πόδι του R το χρειάζεται γιατί χωρίς αυτό το R είναι P· τα μπράτσα του Y
# το χρειάζονται γιατί με ίσιους στύλους και μπάρα το Y βγαίνει βελάκι.
#
# Η διαγώνιος είναι ΦΑΡΔΥΤΕΡΗ από τον στύλο: στις 45 μοίρες το πάχος που
# βλέπει το μάτι είναι το οριζόντιο δια ρίζα δύο. Με DIAG = STEM το πόδι του R
# έβγαινε 4 μονάδες δίπλα σε στύλο 6 και φαινόταν ψιλό.
# Κάθε διαγώνιος κουβαλάει το δικό της πλάτος, γιατί δεν έχουν ίδια κλίση:
# του R είναι 45 μοιρών και θέλει 5, του Y είναι πιο όρθια και 4 φτάνουν.
DIAGS = {
    # Το πόδι ξεκινά κάτω από τη μέση της κοιλιάς και ΤΕΛΕΙΩΝΕΙ ΙΣΙΟ: η
    # διαγώνιος σταματά στο x=8 και από κει κατεβαίνει κάθετα στο x=10..12,
    # δηλαδή ακριβώς εκεί που κάθεται ο δεξιός στύλος κάθε άλλου γράμματος.
    # Αν συνέχιζε διαγώνια, το πέλμα έφτανε στο χείλος του κουτιού και το R
    # έδειχνε να γέρνει έξω από το πλάτος του.
    'R': [(5, [(5, 15), (6, 17), (7, 19), (8, 21)]),
          (3, [(10, 21), (10, 23), (10, 25)])],
    # Τα μπράτσα σμίγουν στο y=12, όχι στο y=8: με γρήγορη σύγκλιση το άνοιγμα
    # του V έκλεινε στη δεύτερη γραμμή και το Y έβγαινε συμπαγές τρίγωνο.
    'Y': [(4, [(1, 0), (1, 2), (2, 4), (2, 6), (3, 8), (3, 10), (4, 12)]),
          (4, [(9, 0), (9, 2), (8, 4), (8, 6), (7, 8), (7, 10), (6, 12)])],
}

TEXT = 'SUGAR BYTE'


def glyph_mask(ch):
    """Γράμμα -> πίνακας bool 14x26.

    Σειρά: ορθογώνια, μετά στρογγύλεμα γωνιών, ΜΕΤΑ οι διαγώνιες. Αν οι
    διαγώνιες μπουν πριν το στρογγύλεμα τις τρώει ολόκληρες — κάθε σκαλοπάτι
    διαγωνίου είναι κυρτή γωνία, και το πόδι του R έμενε ένα pixel.
    """
    m = [[False] * GLYPH_W for _ in range(GLYPH_H)]
    for (x0, y0, x1, y1) in GLYPHS[ch]:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                m[y][x] = True

    def out(x, y):
        return not (0 <= x < GLYPH_W and 0 <= y < GLYPH_H and m[y][x])

    # Στρογγύλεμα: η κοψιά είναι 1 pixel x 2 γραμμές, ώστε να βγει τετράγωνη
    # στην οθόνη με την αναλογία 2:1.
    cut = set()
    for y in range(GLYPH_H):
        for x in range(GLYPH_W):
            if not m[y][x]:
                continue
            for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                if out(x + dx, y) and out(x, y + dy):
                    cut.add((x, y))
                    if not out(x, y + dy * -1) and out(x + dx, y + dy * -1):
                        pass
                    ny = y + dy
                    if not out(x, ny) and out(x + dx, ny):
                        cut.add((x, ny))
                    break
    for (x, y) in cut:
        m[y][x] = False

    for (wide, poly) in DIAGS.get(ch, []):
        for (x, y) in poly:
            for dx in range(wide):
                for dy in range(2):
                    if y + dy < GLYPH_H and x + dx < GLYPH_W:
                        m[y + dy][x + dx] = True
    return m


def draw_glyph(img, ch, ox, oy, base, shade):
    """Εξώθηση στη σκιά, σώμα στη βάση, ανταύγεια πάνω-αριστερά, περίγραμμα."""
    m = glyph_mask(ch)
    put = []

    def at(x, y, pen):
        if 0 <= oy + y < len(img) and 0 <= ox + x < len(img[0]):
            img[oy + y][ox + x] = pen
            put.append((ox + x, oy + y))

    for y in range(GLYPH_H):                       # 1. εξώθηση
        for x in range(GLYPH_W):
            if m[y][x]:
                at(x + 1, y + 2, shade)
    for y in range(GLYPH_H):                       # 2. σώμα
        for x in range(GLYPH_W):
            if m[y][x]:
                at(x, y, base)
    for y in range(GLYPH_H):                       # 3. ανταύγεια
        for x in range(GLYPH_W):
            if not m[y][x]:
                continue
            up = y == 0 or not m[y - 1][x]
            left = x == 0 or not m[y][x - 1]
            if up or left:
                at(x, y, PEN_HI)
    return put


def _outline(img, pens, line=PEN_LINE):
    """Περίγραμμα γύρω από ό,τι δεν είναι φόντο, μέσα στην εικόνα."""
    h, w = len(img), len(img[0])
    edge = []
    for y in range(h):
        for x in range(w):
            if img[y][x] not in pens:
                continue
            for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1),
                             (-1, -1), (1, -1), (-1, 1), (1, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and img[ny][nx] is None:
                    edge.append((nx, ny))
    for (x, y) in edge:
        img[y][x] = line
    return img


SPRINKLES = [(4, 6), (10, 20), (4, 26), (186, 6), (180, 20), (186, 26),
             (14, 13), (176, 13), (94, 3), (94, 27), (100, 14), (88, 14)]


def title():
    """Το λογότυπο: ουράνιο τόξο από τα έξι χρώματα των candies."""
    img = blank(TITLE_W, TITLE_H)

    # Τα γράμματα. Κενό ανάμεσα στις δύο λέξεις, το σύνολο στο κέντρο.
    advance = GLYPH_W + 2
    width = (len(TEXT) - 1) * advance + GLYPH_W
    x = (TITLE_W - width) // 2
    colour = 0
    for ch in TEXT:
        if ch != ' ':
            _, base, shade = CANDY_PENS[colour % len(CANDY_PENS)]
            draw_glyph(img, ch, x, 2, base, shade)
            colour += 1
        x += advance

    _outline(img, {p for _, b, s in CANDY_PENS for p in (b, s)} | {PEN_HI})

    for i, (sx, sy) in enumerate(SPRINKLES):        # τρούφες στο φόντο
        pen = CANDY_PENS[i % len(CANDY_PENS)][1]
        if all(img[sy + dy][sx + dx] is None
               for dy in range(2) for dx in range(2)):
            for dy in range(2):
                for dx in range(2):
                    img[sy + dy][sx + dx] = pen
    return img


# ------------------------------------------------------------- μπορντούρα

ROPE_PENS = (PEN['r'], PEN_HI)          # κόκκινο / άσπρο, σαν candy cane
ROPE_SHADE = PEN['R']


STRIPE = 2


def _rope_pen(x, y, lean):
    """Οι ρίγες στις 45 μοίρες: 1 pixel ανά 2 γραμμές, όπως το θέλει το 2:1.

    Το πλάτος ρίγας ΔΕΝ είναι ελεύθερο. Το πλαϊνό πλακάκι επαναλαμβάνεται κάθε
    24 γραμμές, δηλαδή η φάση μετατοπίζεται κατά 12 pixels· το κάτω πλακάκι
    επαναλαμβάνεται κάθε 16 pixels. Για να μη φαίνεται ραφή πρέπει και το
    12/ΡΙΓΑ και το 16/ΡΙΓΑ να βγαίνουν ΖΥΓΑ — αλλιώς οι ρίγες αντιστρέφονται
    σε κάθε ένωση. Με ρίγα 4 το 12/4 = 3 ήταν μονό και το κάθετο κορδόνι
    έσπαγε κάθε 24 γραμμές. Το 2 είναι η μόνη τιμή που ικανοποιεί και τα δύο.
    """
    return ROPE_PENS[((x + lean * (y // 2)) // STRIPE) % 2]


def _rope(img, x0, x1, y0, y1, lean, vertical):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img[y][x] = _rope_pen(x, y, lean)
    # σκιά στη μία πλευρά για να στρογγυλέψει το κορδόνι
    if vertical:
        for y in range(y0, y1 + 1):
            img[y][x1] = ROPE_SHADE
            img[y][x0] = PEN_LINE
    else:
        for x in range(x0, x1 + 1):
            img[y1][x] = ROPE_SHADE
            img[y0][x] = PEN_LINE
    return img


def _dots(img, pts):
    for (x, y, pen) in pts:
        img[y][x] = img[y + 1][x] = pen
    return img


def border():
    s = SpriteSet('border_cpc_mode0', EDGE_W, EDGE_H, masked=False,
                  note='μπορντούρα overscan 16x24 αδιαφανή — κορδόνι και γωνία')

    # Πλαϊνά: κάθετο κορδόνι 8 pixels, τρούφες δεξιά κι αριστερά.
    for name, lean, dots in (
            ('edge_left', 1, ((1, 4, PEN['g']), (14, 14, PEN['y']))),
            ('edge_right', -1, ((1, 14, PEN['y']), (14, 4, PEN['g'])))):
        img = blank(EDGE_W, EDGE_H, PEN_MASK)
        _rope(img, 4, 11, 0, EDGE_H - 1, lean, True)
        _dots(img, dots)
        s.add(img, name, 'edge')

    # Κάτω: οριζόντιο κορδόνι 16 γραμμών.
    img = blank(EDGE_W, EDGE_H, PEN_MASK)
    _rope(img, 0, EDGE_W - 1, 4, 19, 1, False)
    _dots(img, ((2, 0, PEN['b']), (10, 21, PEN['m'])))
    s.add(img, 'edge_bottom', 'edge')

    # Γωνία: ένα ζαχαρωτό που κρύβει την ένωση των δύο κορδονιών.
    img = blank(EDGE_W, EDGE_H, PEN_MASK)
    cx, cy, rx, ry = 7.5, 11.5, 6.5, 11.0
    for y in range(EDGE_H):
        for x in range(EDGE_W):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = u * u + v * v
            if d <= 1.0:
                img[y][x] = PEN['m'] if (u + v) <= 0.3 else PEN['M']
            if 0.72 <= d <= 1.0 and (u + v) > 0.3:
                img[y][x] = PEN['M']
    for (hx, hy) in ((4, 6), (5, 6), (4, 7), (5, 7), (3, 8), (4, 8)):
        img[hy][hx] = PEN_HI
    _outline(img, {PEN['m'], PEN['M'], PEN_HI})
    s.add(img, 'corner', 'corner')
    return s


def title_set():
    s = SpriteSet('title_cpc_mode0', TITLE_W, TITLE_H, masked=False,
                  note='λογότυπο overscan 192x32 αδιαφανές — πάνω μπορντούρα')
    s.add(title(), 'sugar_byte', 'title')
    return s


# ------------------------------------------------------------------ μενού
# Ίδιο κελί με τη μπορντούρα (16x24) ώστε τα δύο σετ να μοιράζονται γεωμετρία.

PLATE_Y0, PLATE_Y1 = 4, 19          # το πιάτο μέσα στο κελί
PLATE_BASE, PLATE_SHADE = PEN['m'], PEN['M']


def _plate_row_pen(y):
    if y == PLATE_Y0:
        return PEN_HI                               # ανταύγεια στην κορυφή
    if y == PLATE_Y1:
        return PEN_LINE                             # σκούρο χείλος στη βάση
    return PLATE_BASE if y <= 11 else PLATE_SHADE


def _plate(cap):
    """Πιάτο μενού. cap: 'l' στρογγυλό αριστερά, 'r' δεξιά, None ίσιο."""
    img = blank(EDGE_W, EDGE_H, PEN_MASK)
    cx, rx, cy, ry = 12.0, 8.0, 11.5, 8.0
    for y in range(PLATE_Y0, PLATE_Y1 + 1):
        for x in range(EDGE_W):
            sx = EDGE_W - 1 - x if cap == 'r' else x
            if cap is None or sx >= cx or \
               ((sx - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                img[y][x] = _plate_row_pen(y)
    return img


def _pointer(phase):
    """Δείκτης επιλογής: τρίγωνο από ζαχαρωτό, δύο φάσεις για να «τρέχει»."""
    img = blank(EDGE_W, EDGE_H, PEN_MASK)
    for y in range(PLATE_Y0, PLATE_Y1 + 1):
        t = abs(y - 11.5) / 8.0
        for x in range(3, 3 + int(round(9 * (1.0 - t))) + 1):
            img[y][x] = _rope_pen(x + phase, y, 1)
    return img


def menu():
    s = SpriteSet('menu_cpc_mode0', EDGE_W, EDGE_H, masked=False,
                  note='μενού 16x24 αδιαφανές — πιάτο επιλογής και δείκτης')
    for cap, name in ((None, 'plate_m'), ('l', 'plate_l'), ('r', 'plate_r')):
        s.add(_plate(cap), name, 'plate')
    for i in (0, 1):
        s.add(_pointer(i), 'pointer%d' % (i + 1), 'pointer')
    return s
