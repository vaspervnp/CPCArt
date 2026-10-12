"""Όλα τα sprites του match-3: candies, κελιά ταμπλό, επικαλύψεις, HUD.

Τα candies και οι επικαλύψεις είναι **με μάσκα** (pen 0 διάφανο) και πατάνε
πάνω στα κελιά του ταμπλό, που είναι **αδιαφανή**. Έτσι το ίδιο candy πέφτει
πάνω σε σκέτο κελί, σε ζελέ ή σε σοκολάτα χωρίς αντίγραφα — αλλιώς τα 25
candies θα χρειάζονταν μία έκδοση για κάθε φόντο.
"""
import math

import shapes as sh
from cpcgfx import (CANDY_PENS, CANDY_NAMES, CW, CH, HW, HH, PEN,
                    PEN_GREY, PEN_HI, PEN_JELLY, PEN_LINE, PEN_MASK,
                    SpriteSet, blank, opaque, parse_art, stamp)

# ---------------------------------------------------------------- candies

def _bomb(w=CW, h=CH):
    """Η βόμβα χρώματος: γυαλιστερή μπάλα με τρούφες σε κάθε χρώμα.

    Δεν έχει χρώμα η ίδια — καθαρίζει ό,τι χρώμα της δώσεις, άρα το σώμα είναι
    το μπλε της νύχτας και τα χρώματα μπαίνουν σαν τρούφες.
    """
    spots = [(4, 4), (7, 5), (2, 8), (5, 9), (8, 10), (3, 12),
             (6, 13), (9, 14), (4, 16), (7, 17), (5, 19)]
    paint = {}
    for i, (sx, sy) in enumerate(spots):
        pen = CANDY_PENS[i % len(CANDY_PENS)][1]
        paint[(sx, sy)] = pen
        paint[(sx, sy + 1)] = pen          # 1 pixel x 2 γραμμές = τετράγωνη τρούφα

    def over(x, y, u, v, pen, base, shade):
        return paint.get((x, y))

    return sh.render(sh.circle, PEN_LINE, PEN_MASK, w, h,
                     line=PEN_GREY, over=over)


def _cherry():
    """Υλικό 1: κεράσια. Το ζητούμενο «κατέβασέ τα ώς κάτω»."""
    img = blank(CW, CH)
    r, R, g, N = PEN['r'], PEN['R'], PEN['g'], PEN['N']
    ball = sh.render(sh.circle, r, R, 7, 14)        # σώμα 5x10
    stamp(img, ball, 0, 10)
    stamp(img, ball, 5, 8)
    for (sx, sy) in ((3, 9), (4, 8), (4, 7), (5, 6), (5, 5), (6, 4),
                     (8, 7), (8, 6), (7, 5)):
        img[sy][sx] = N
    for (sx, sy) in ((6, 3), (6, 2)):
        img[sy][sx] = g
    for (sx, sy) in ((2, 3), (3, 3), (4, 3), (3, 2), (4, 2), (3, 4)):
        img[sy][sx] = g                              # φύλλο
    img[3][2] = N
    return img


def _nut():
    """Υλικό 2: φουντούκι. Καπέλο σκούρο με ψίχα, καρύδι πορτοκαλί-καφέ.

    Το σώμα παίρνει πορτοκαλί βάση και μπορντό σκιά: λαδί βάση με μπορντό σκιά
    έβγαινε σχεδόν ολόκληρο μπορντό, γιατί η σκιά πιάνει το μισό σχήμα.
    """
    def cap(x, y, u, v, pen, base, shade):
        if v > -0.26:
            return None
        if v > -0.36:
            return PEN_GREY                          # το χείλος του καπέλου
        return PEN_GREY if (x % 3 == 0 and y % 3 == 1) else PEN['R']

    img = sh.render(sh.circle, PEN['o'], PEN['R'], inset=(2, 2), over=cap)
    for sy in (6, 7):                                # ο γύρος του καπέλου
        img[sy][1] = img[sy][10] = PEN['R']
        img[sy][2] = img[sy][9] = PEN['R']
    for sy in (0, 1):
        img[sy][5] = img[sy][6] = PEN['R']           # κοτσανάκι
    return img


def candies():
    s = SpriteSet('candy_cpc_mode0', CW, CH, masked=True,
                  note='candies 12x24 με μάσκα — 6 χρώματα x 4 μορφές, βόμβα, υλικά')
    for (name, base, shade), shape in zip(CANDY_PENS, sh.SILHOUETTES):
        s.add(sh.render(shape, base, shade), name, 'plain')
    # Τα ριγέ χωρίς ανταύγεια: η λευκή βούλα κολλάει στις ρίγες και μπαλώνει.
    for (name, base, shade), shape in zip(CANDY_PENS, sh.SILHOUETTES):
        s.add(sh.render(shape, base, shade, over=sh.stripes_h, highlight=False),
              name, 'striped_h')
    for (name, base, shade), shape in zip(CANDY_PENS, sh.SILHOUETTES):
        s.add(sh.render(shape, base, shade, over=sh.stripes_v, highlight=False),
              name, 'striped_v')
    # Το περιτύλιγμα είναι ένα σχήμα για όλα τα χρώματα — όπως στο Candy Crush.
    for name, base, shade in CANDY_PENS:
        s.add(sh.render(sh.wrapped, base, shade, over=sh.wrapper_pleats),
              name, 'wrapped')
    s.add(_bomb(), 'colour_bomb', 'bomb')
    s.add(_cherry(), 'cherry', 'ingredient')
    s.add(_nut(), 'nut', 'ingredient')
    return s


# ------------------------------------------------------------ κελιά ταμπλό
# Αδιαφανή 12x24. Το πλέγμα μπαίνει στη δεξιά κολόνα και στην κάτω γραμμή,
# ώστε δύο γειτονικά κελιά να δίνουν μία συνεχή γραμμή και όχι δύο.

def _grid(img, pen=PEN_MASK):
    """Το πλέγμα μπαίνει δεξιά και κάτω, ώστε δύο γειτονικά κελιά να δίνουν
    μία γραμμή και όχι δύο."""
    for y in range(CH):
        img[y][CW - 1] = pen
    for x in range(CW):
        img[CH - 1][x] = pen
    return img


def _dither(img, pen, every=2, box=None):
    """Πλέγμα 1 pixel x 2 γραμμές — ο μόνος dither που δεν τρεμοπαίζει σε Mode 0."""
    x0, y0, x1, y1 = box or (0, 0, CW, CH)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x + y // 2) % every == 0:
                img[y][x] = pen
    return img


def _ellipse(img, cx, cy, r, pen):
    """Κύκλος στην οθόνη: r pixels φάρδος, 2r γραμμές ύψος."""
    for y in range(CH):
        for x in range(CW):
            if ((x - cx) / r) ** 2 + ((y - cy) / (2.0 * r)) ** 2 <= 1.0:
                img[y][x] = pen
    return img


def _polyline(img, pts, pen):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            x = int(round(x0 + (x1 - x0) * i / float(steps)))
            y = int(round(y0 + (y1 - y0) * i / float(steps)))
            if 0 <= x < CW and 0 <= y < CH:
                img[y][x] = pen
    return img


def _frame(img, pen, rows=1, cols=1):
    for y in range(CH - 1):
        for c in range(cols):
            img[y][c] = img[y][CW - 2 - c] = pen
    for x in range(CW - 1):
        for rr in range(rows):
            img[rr][x] = img[CH - 2 - rr][x] = pen
    return img


# Οι ρωγμές του γλάσου: όσο λιγότερα στρώματα, τόσο περισσότερες.
ICE_CRACKS = [
    [(3, 3), (4, 6), (3, 9)],
    [(8, 5), (7, 9), (8, 13)],
    [(5, 14), (6, 17), (4, 21)],
]


def cells():
    s = SpriteSet('cells_cpc_mode0', CW, CH, masked=False,
                  note='κελιά ταμπλό 12x24, αδιαφανή — φόντο, ζελέ, γλάσο, εμπόδια')

    s.add(_grid(blank(CW, CH, PEN_LINE)), 'plain', 'board')
    # Η σκακιέρα είναι διακριτική επίτηδες: το ταμπλό δεν πρέπει να τραβάει
    # το μάτι από τα candies. Αραιές βούλες, όχι dither — ο dither έβγαζε
    # διαγώνιες ρίγες που χτυπούσαν με τις ρίγες των ριγέ candies.
    alt = blank(CW, CH, PEN_LINE)
    for (dx, dy) in ((2, 4), (8, 10), (4, 16)):
        alt[dy][dx] = alt[dy + 1][dx] = PEN_MASK
    s.add(_grid(alt), 'plain_alt', 'board')
    s.add(blank(CW, CH, PEN_MASK), 'hole', 'board')

    # Ζελέ: ένα ή δύο στρώματα. Το σημάδι μπαίνει στο ΠΕΡΙΓΡΑΜΜΑ του κελιού,
    # γιατί αυτό είναι το μόνο κομμάτι που δεν το σκεπάζει το candy από πάνω.
    s.add(_grid(_frame(blank(CW, CH, PEN_LINE), PEN_JELLY)), 'jelly1', 'jelly')
    j2 = _frame(blank(CW, CH, PEN_LINE), PEN_JELLY)
    for (cx, cy) in ((0, 0), (CW - 3, 0), (0, CH - 5), (CW - 3, CH - 5)):
        for dy in range(4):
            for dx in range(2):
                j2[cy + dy][cx + dx] = PEN_JELLY
    s.add(_grid(j2), 'jelly2', 'jelly')

    # Γλάσο: τρία στρώματα. Το μέτρημα διαβάζεται και από τη φωτεινότητα και
    # από τις ρωγμές — μόνο οι ρωγμές ήταν πολύ λίγο σε 12x24.
    for layers in (3, 2, 1):
        if layers == 3:
            ice = blank(CW, CH, PEN_HI)
        elif layers == 2:
            ice = _dither(blank(CW, CH, PEN_GREY), PEN_HI, every=2)
        else:
            ice = _dither(blank(CW, CH, PEN_GREY), PEN_LINE, every=2)
        for x in range(CW - 1):
            ice[0][x] = PEN_HI
        for y in range(CH - 1):
            ice[y][0] = PEN_HI
        for x in range(1, CW - 1):
            ice[CH - 3][x] = ice[CH - 2][x] = PEN_GREY if layers == 3 else PEN_LINE
        for y in range(1, CH - 1):
            ice[y][CW - 2] = PEN_GREY if layers == 3 else PEN_LINE
        for crack in ICE_CRACKS[:4 - layers]:
            _polyline(ice, crack, PEN_LINE)
        s.add(_grid(ice), 'icing%d' % layers, 'icing')

    # Σοκολάτα: εξαπλώνεται μόνη της αν δεν τη σπάσεις. Σκούρο καφέ με λαδί
    # λεκέδες — στρογγυλοί, όχι dither: το ύφασμα του dither το έχει το γλάσο.
    cho = blank(CW, CH, PEN['R'])
    for (bx, by, br) in ((3.0, 6.0, 2.4), (8.0, 13.0, 2.6), (4.0, 19.0, 2.0)):
        _ellipse(cho, bx, by, br, PEN['O'])
    for x in range(CW - 1):
        cho[0][x] = PEN['O']
    s.add(_grid(cho), 'chocolate', 'blocker')

    # Γλυκόριζα: ρόδα. Ομόκεντροι δακτύλιοι μαύρο-γκρι, άσπρο κέντρο.
    lic = blank(CW, CH, PEN_MASK)
    for y in range(CH - 1):
        for x in range(CW - 1):
            u = (x + 0.5 - (CW - 1) / 2.0) / ((CW - 1) / 2.0)
            v = (y + 0.5 - (CH - 1) / 2.0) / ((CH - 1) / 2.0)
            r = math.hypot(u, v)
            if r > 1.0:
                continue
            lic[y][x] = (PEN_GREY, PEN_MASK)[int(r * 5) % 2]
    _ellipse(lic, 5.0, 11.0, 1.2, PEN_HI)
    s.add(_grid(lic), 'licorice', 'blocker')
    return s


# ------------------------------------------------- επικαλύψεις και εφέ
# Με μάσκα, 12x24, ζωγραφίζονται ΠΑΝΩ από ένα candy.

def _ring(r0, r1, pen_out, pen_in=None, gaps=0):
    """Στεφάνι ακτίνας r0..r1 στον χώρο u, v — για τις εκρήξεις."""
    def dist(u, v):
        return 0.0 if r0 <= math.hypot(u, v) <= r1 else 9.9

    def over(x, y, u, v, pen, base, shade):
        if gaps and int((math.atan2(v, u) + math.pi) / (math.pi / gaps)) % 2:
            return PEN_MASK
        return None

    img = sh.render(dist, pen_out, pen_in or pen_out, over=over, outline=False,
                    highlight=False)
    return [[None if p == PEN_MASK else p for p in row] for row in img]


# Τα αστέρια ζωγραφίζονται: η πολική μορφή τα έκοβε σε κομμάτια όταν η ακτίνα
# έπεφτε κάτω από ένα pixel, και το μικρό έβγαινε «διαίρεση».
STAR_SMALL = """
------------
------------
------------
------------
------------
------------
------------
------------
-----XX-----
-----XX-----
-----XX-----
----XXXX----
----XXXX----
-----XX-----
-----XX-----
-----XX-----
------------
------------
------------
------------
------------
------------
------------
------------
"""

STAR_BIG = """
------------
------------
------------
------------
-----XX-----
-----XX-----
-----XX-----
-----XX-----
----XXXX----
----XXXX----
---XXXXXX---
-XXXXXXXXXX-
-XXXXXXXXXX-
---XXXXXX---
----XXXX----
----XXXX----
-----XX-----
-----XX-----
-----XX-----
-----XX-----
------------
------------
------------
------------
"""


def _star(art, pen, core=None):
    img = blank(CW, CH)
    for y, line in enumerate(a for a in art.strip('\n').splitlines() if a.strip()):
        for x, ch in enumerate(line.strip()):
            if ch != '-':
                img[y][x] = pen
    if core:
        for dy in (-2, -1, 0, 1):
            for dx in (-1, 0):
                img[CH // 2 + dy][CW // 2 + dx] = core
    return img


def overlays():
    s = SpriteSet('overlay_cpc_mode0', CW, CH, masked=True,
                  note='επικαλύψεις 12x24 με μάσκα — δείκτης, κλουβί, εφέ')

    # Δείκτης: τέσσερα γωνιακά αγκύλια, δύο καρέ για να αναβοσβήνει.
    for frame, pen in enumerate((PEN_HI, PEN_JELLY)):
        img = blank(CW, CH)
        for (ox, dx) in ((0, 1), (CW - 1, -1)):
            for (oy, dy) in ((0, 1), (CH - 1, -1)):
                for i in range(4):
                    img[oy][ox + dx * i] = pen
                for j in range(1, 5):
                    img[oy + dy * j][ox] = pen
        s.add(img, 'cursor%d' % (frame + 1), 'cursor')

    # Κλουβί γλυκόριζας: κλειδώνει ένα candy ώσπου να γίνει match δίπλα του.
    cage = blank(CW, CH)
    for y in range(1, CH - 1):
        for x in (1, 2, 9, 10):
            cage[y][x] = PEN_GREY if x in (1, 9) else PEN_MASK
    for x in range(1, 11):
        for y in (5, 6, 17, 18):
            cage[y][x] = PEN_GREY if y in (5, 17) else PEN_MASK
    for (cx, cy) in ((1, 0), (9, 0), (1, 22), (9, 22)):
        cage[cy][cx] = cage[cy][cx + 1] = PEN_HI
        cage[cy + 1][cx] = cage[cy + 1][cx + 1] = PEN_GREY
    return_cage = cage

    # Μαρμελάδα: διάφανο κέλυφος. Ο dither 1x2 κάνει το «μισό-διάφανο» που
    # το Mode 0 δεν έχει· στο ένα-στα-τρία το candy από κάτω αναγνωρίζεται
    # ακόμα, στο ένα-στα-δύο χανόταν.
    mar = blank(CW, CH)
    for y in range(1, CH - 1):
        for x in range(1, CW - 1):
            if (x + y // 2) % 2 == 0:
                mar[y][x] = PEN['y']
    for x in range(2, CW - 2):
        mar[0][x] = mar[CH - 1][x] = PEN['O']
    for y in range(2, CH - 2):
        mar[y][0] = mar[y][CW - 1] = PEN['O']
    for (gx, gy) in ((3, 3), (4, 3), (3, 4), (2, 5), (3, 5), (2, 6)):
        mar[gy][gx] = PEN_HI
    s.add(return_cage, 'cage', 'blocker')
    s.add(mar, 'marmalade', 'blocker')

    # Έκρηξη: λάμψη, στεφάνι που ανοίγει, σπάσιμο, σκόνη.
    s.add(_star(STAR_SMALL, PEN_HI), 'pop1', 'pop')
    s.add(_ring(0.34, 0.58, PEN_HI, PEN_JELLY), 'pop2', 'pop')
    s.add(_ring(0.62, 0.86, PEN_JELLY, PEN_HI, gaps=6), 'pop3', 'pop')
    s.add(_ring(0.88, 1.00, PEN_JELLY, PEN_JELLY, gaps=10), 'pop4', 'pop')

    # Δέσμες: το ριγέ candy καθαρίζει γραμμή ή κολόνα· η δέσμη τρέχει πάνω τους.
    for i, half in enumerate((5, 3)):
        img = blank(CW, CH)
        for y in range(CH // 2 - half, CH // 2 + half):
            edge = y in (CH // 2 - half, CH // 2 + half - 1)
            for x in range(CW):
                img[y][x] = PEN_JELLY if edge else PEN_HI
        s.add(img, 'beam_h%d' % (i + 1), 'beam_h')
    for i, half in enumerate((3, 2)):
        img = blank(CW, CH)
        for x in range(CW // 2 - half, CW // 2 + half):
            edge = x in (CW // 2 - half, CW // 2 + half - 1)
            for y in range(CH):
                img[y][x] = PEN_JELLY if edge else PEN_HI
        s.add(img, 'beam_v%d' % (i + 1), 'beam_v')

    s.add(_star(STAR_SMALL, PEN_HI), 'star1', 'star')
    s.add(_star(STAR_BIG, PEN_JELLY, PEN_HI), 'star2', 'star')
    return s


# ----------------------------------------------------------------- HUD
# Αδιαφανή 4x8 — ίδιο κελί με τη γραμματοσειρά 4x8 του planetbase, άρα τα
# γράμματα από εκείνη μπαίνουν δίπλα σε αυτά τα ψηφία χωρίς πειράγματα.

DIGITS = """
0:WWW W.W W.W W.W W.W WWW
1:.W. WW. .W. .W. .W. WWW
2:WWW ..W .WW W.. W.. WWW
3:WWW ..W .WW ..W ..W WWW
4:W.W W.W W.W WWW ..W ..W
5:WWW W.. WWW ..W ..W WWW
6:.WW W.. WWW W.W W.W WWW
7:WWW ..W ..W .W. .W. .W.
8:WWW W.W WWW W.W W.W WWW
9:WWW W.W WWW ..W ..W WW.
"""

SYMBOLS = """
colon:... .W. ... ... .W. ...
slash:..W ..W .W. .W. W.. W..
times:W..W W..W .WW. .WW. W..W W..W ...
plus :... .W. WWW .W. ... ...
"""

# Εικονίδια 4x8 — τέσσερις στήλες μόνο, άρα σύμβολα, όχι εικόνες.
ICONS = """
moves:.W.. WWWW .W.. .... ...W WWWW ..W. ....
star :.WW. .WW. WWWW WWWW .WW. .WW. .... ....
goal :.WW. W..W W..W .WW. .... .... .... ....
time :WWWW .WW. .WW. WWWW .... .... .... ....
lock :.WW. W..W WWWW WWWW WWWW .... .... ....
"""


def _glyph(rows, pen=PEN_HI, top=1):
    """Γραμμές από '.' και 'W' -> κελί HUD 4x8, αριστερά στοιχισμένο."""
    img = blank(HW, HH, PEN_MASK)
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            if ch == 'W' and i < HW and top + j < HH:
                img[top + j][i] = pen
    return img


def _parse_glyphs(block):
    out = []
    for line in block.strip('\n').splitlines():
        name, _, rest = line.partition(':')
        out.append((name.strip(), rest.split()))
    return out


def hud():
    s = SpriteSet('hud_cpc_mode0', HW, HH, masked=False,
                  note='κελιά HUD 4x8 αδιαφανή — ψηφία, σύμβολα, εικονίδια, πλαίσιο')
    for name, rows in _parse_glyphs(DIGITS):
        s.add(_glyph(rows), 'digit_' + name, 'digits')
    for name, rows in _parse_glyphs(SYMBOLS):
        s.add(_glyph(rows), name, 'symbols')
    for name, rows in _parse_glyphs(ICONS):
        s.add(_glyph(rows, PEN_JELLY, top=0), name, 'icons')

    # Πλαίσιο HUD, 9 κομμάτια: γωνίες, πλευρές, γέμισμα.
    for ky in ('t', 'm', 'b'):
        for kx in ('l', 'c', 'r'):
            img = blank(HW, HH, PEN_LINE)
            if ky == 't':
                for x in range(HW):
                    img[0][x] = PEN_GREY
            if ky == 'b':
                for x in range(HW):
                    img[HH - 1][x] = PEN_GREY
            if kx == 'l':
                for y in range(HH):
                    img[y][0] = PEN_GREY
            if kx == 'r':
                for y in range(HH):
                    img[y][HW - 1] = PEN_GREY
            s.add(img, 'panel_%s%s' % (ky, kx), 'panel')
    return s


def all_sets():
    return [candies(), cells(), overlays(), hud()]
