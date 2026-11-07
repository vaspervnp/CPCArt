"""Η παλέτα του Empire, τα εργαλεία ζωγραφικής και τα σετ sprites.

Ο ΚΩΔΙΚΟΠΟΙΗΤΗΣ ΔΕΝ ΕΙΝΑΙ ΕΔΩ. Είναι στο `cpcimg.py`, που είναι symlink στο
`steampunk/src/cpcimg.py` — ένας κωδικοποιητής Mode 0 για όλο το repo, με
αντίστροφο και ισχυρισμό που τους δένει και στις 256 τιμές. Η σειρά των bits
του Mode 0 είναι αντιδιαισθητική και έχει ήδη γραφτεί λάθος μία φορά εδώ.

ΤΟ PEN 0 ΕΙΝΑΙ ΤΟ ΔΙΑΦΑΝΟ, ΟΧΙ ΤΟ ΜΑΥΡΟ

Σε sprite με μάσκα το pen 0 σημαίνει «μη ζωγραφίσεις εδώ». Άρα τα
περιγράμματα ΔΕΝ μπορούν να είναι pen 0 — θα γίνονταν τρύπες. Το pen 1 είναι
το μπλε της νύχτας (#000080): περνάει για μαύρο σε οθόνη και κρατάει το 0
ελεύθερο για τη μάσκα.

ΤΑ ΧΡΩΜΑΤΑ ΤΗΣ ΟΜΑΔΑΣ

Τα pens 2 και 3 είναι ΤΟ ΧΡΩΜΑ ΤΟΥ ΠΑΙΚΤΗ, φωτεινό και σκιά. Στα δεδομένα
είναι μπλε. Για τους άλλους παίκτες δεν ξαναζωγραφίζεται τίποτα: ένας πίνακας
16 bytes ανά παίκτη αλλάζει αυτά τα δύο pens (δες `TEAMS`). Δεν γίνεται με
αλλαγή του INK, γιατί τότε ΟΛΟΙ οι παίκτες θα άλλαζαν μαζί.
"""
import os

import cpcimg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)

# χαρ, όνομα firmware, firmware number, ρόλος
PALETTE = [
    ('.', 'Black',          0,  'ΔΙΑΦΑΝΟ — η μάσκα, ποτέ χρώμα'),
    ('K', 'Blue',           1,  'περίγραμμα και βαθιά σκιά (περνάει για μαύρο)'),
    ('T', 'Bright blue',    2,  'ΟΜΑΔΑ φωτεινό — αλλάζει ανά παίκτη'),
    ('t', 'Sky blue',      11,  'ΟΜΑΔΑ σκιά — αλλάζει ανά παίκτη'),
    ('d', 'Red',            3,  'καφέ σκούρο: ξύλο, δέρμα, μαλλιά, σκουριά'),
    ('D', 'Orange',        15,  'καφέ φωτεινό: κοντάρι, τρίχωμα, χώμα'),
    ('s', 'Pink',          16,  'δέρμα'),
    ('S', 'Pastel yellow', 25,  'δέρμα στο φως, λινό, άχυρο'),
    ('i', 'White',         13,  'σίδερο, πέτρα, ατσάλι'),
    ('I', 'Bright white',  26,  'ανταύγεια μετάλλου, λευκό ύφασμα'),
    ('y', 'Bright yellow', 24,  'χρυσό, μπρούντζος στο φως'),
    ('o', 'Yellow',        12,  'λαδί: μπρούντζος σκιά, άχυρο σκιά'),
    ('g', 'Bright green',  18,  'πράσινο φωτεινό: φυτά, λοφίο'),
    ('n', 'Green',          9,  'πράσινο σκούρο'),
    ('r', 'Bright red',     6,  'κόκκινο: αίμα, λάβαρο, φωτιά'),
    ('m', 'Magenta',        4,  'μωβ σκούρο: σκιά υφάσματος, πορφύρα'),
]

PEN = {p[0]: i for i, p in enumerate(PALETTE)}
FW = [p[2] for p in PALETTE]
NAMES = [p[1] for p in PALETTE]
CHARS = [p[0] for p in PALETTE]
USAGE = [p[3] for p in PALETTE]
RGB = [cpcimg.FW_RGB[f] for f in FW]

assert len(PALETTE) == 16 and len(set(CHARS)) == 16 and len(set(FW)) == 16
assert PEN['.'] == 0, 'το διάφανο πρέπει να είναι το pen 0'

PEN_MASK = PEN['.']
PEN_LINE = PEN['K']
TEAM_HI, TEAM_LO = PEN['T'], PEN['t']

# Τα τέσσερα χρώματα παικτών. Κάθε ζευγάρι είναι (φωτεινό, σκιά) και πρέπει να
# υπάρχει ΗΔΗ στην παλέτα — δεν προστίθενται pens, μόνο ανταλλάσσονται.
TEAMS = [
    ('blue',   PEN['T'], PEN['t']),      # η προεπιλογή: όπως είναι γραμμένα
    ('red',    PEN['r'], PEN['d']),
    ('yellow', PEN['y'], PEN['o']),
    ('green',  PEN['g'], PEN['n']),
]


def team_table(idx):
    """Πίνακας 16 bytes: pen -> pen, για τον παίκτη `idx`."""
    _, hi, lo = TEAMS[idx]
    t = list(range(16))
    t[TEAM_HI], t[TEAM_LO] = hi, lo
    return t


# ------------------------------------------------------------ ζωγραφική

def blank(w, h, pen=None):
    return [[pen] * w for _ in range(h)]


def parse_art(text, transparent='-'):
    """ASCII -> γραμμές pens. Το '-' είναι διάφανο, τα υπόλοιπα της παλέτας."""
    rows = []
    for line in text.strip('\n').splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append([None if ch == transparent else PEN[ch] for ch in line])
    return rows


def stamp(dst, art, x=0, y=0):
    """Ζωγραφίζει το `art` πάνω στο `dst`. Το διάφανο αφήνει ό,τι υπάρχει."""
    for j, row in enumerate(art):
        for i, pen in enumerate(row):
            if pen is None:
                continue
            yy, xx = y + j, x + i
            if 0 <= yy < len(dst) and 0 <= xx < len(dst[0]):
                dst[yy][xx] = pen
    return dst


def recolour(img, mapping):
    return [[mapping.get(p, p) for p in row] for row in img]


def mirror(img):
    """Καθρέφτισμα. Το W φτιάχνεται έτσι από το E και δεν ζωγραφίζεται ξεχωριστά.

    Στο CPC το ίδιο γίνεται και σε χρόνο εκτέλεσης: μέσα στο byte τα δύο pixels
    ανταλλάσσονται με έναν πίνακα 256 bytes, και τα bytes της γραμμής
    αντιστρέφονται. Αν προτιμάς μνήμη από κύκλους, κόψε τα W από το δίσκο.
    """
    return [list(reversed(row)) for row in img]


def nonempty(img):
    return any(p is not None for row in img for p in row)


def pens_used(img):
    return sorted({p for row in img for p in row if p is not None})


def shift(img, dx=0, dy=0):
    h, w = len(img), len(img[0])
    out = blank(w, h, None)
    for y in range(h):
        for x in range(w):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                out[yy][xx] = img[y][x]
    return out


# ------------------------------------------------------- κωδικοποίηση

def encode_masked(img):
    """Εικόνα -> bytes Mode 0, πλεγμένα mask,data ανά ΖΕΥΓΑΡΙ pixels.

    Η μάσκα έχει όλα τα bits αναμμένα όπου το pixel είναι διάφανο: `AND mask`
    και μετά `OR data`. Το πλάτος σε bytes ΔΕΔΟΜΕΝΩΝ είναι w//2 — η γραμμή στη
    μνήμη είναι το ΔΙΠΛΟ. Οι σταθερές `_W` στο .asm είναι bytes δεδομένων.
    """
    out = bytearray()
    for row in img:
        assert len(row) % 2 == 0, 'το πλάτος πρέπει να είναι ζυγό'
        for i in range(0, len(row), 2):
            a, b = row[i], row[i + 1]
            out.append(cpcimg.mode0_byte(15 if a is None else 0,
                                         15 if b is None else 0))
            out.append(cpcimg.mode0_byte(0 if a is None else a,
                                         0 if b is None else b))
    return bytes(out)


def encode_opaque(img):
    out = bytearray()
    for row in img:
        assert len(row) % 2 == 0
        for i in range(0, len(row), 2):
            a, b = row[i], row[i + 1]
            out.append(cpcimg.mode0_byte(0 if a is None else a,
                                         0 if b is None else b))
    return bytes(out)


def decode_masked(data, w, h):
    """Αποκωδικοποίηση πίσω σε pens — για την επαλήθευση, όχι για το παιχνίδι."""
    img, k = [], 0
    for _ in range(h):
        row = []
        for _ in range(w // 2):
            ma, mb = cpcimg.mode0_pens(data[k])
            da, db = cpcimg.mode0_pens(data[k + 1])
            k += 2
            row.append(None if ma == 15 else da)
            row.append(None if mb == 15 else db)
        img.append(row)
    return img


# ----------------------------------------------------------- σετ sprites

class SpriteSet:
    """Καρέ ίδιου μεγέθους. Τα tags μένουν ΣΥΝΕΧΟΜΕΝΑ ώστε το παιχνίδι να
    παίζει μια κίνηση με «πρώτο καρέ + πλήθος», χωρίς πίνακα δεικτών."""

    def __init__(self, name, w, h, note=''):
        self.name, self.w, self.h, self.note = name, w, h, note
        self.frames, self.names, self.tags = [], [], []

    def add(self, img, name, tag):
        assert len(img) == self.h and all(len(r) == self.w for r in img), \
            '%s/%s: %dx%d, περίμενα %dx%d' % (self.name, name, len(img[0]),
                                              len(img), self.w, self.h)
        if self.tags and self.tags[-1] != tag and tag in self.tags:
            raise ValueError('%s: το tag %s δεν θα έμενε συνεχόμενο'
                             % (self.name, tag))
        self.frames.append([list(r) for r in img])
        self.names.append(name)
        self.tags.append(tag)
        return len(self.frames) - 1

    def tag_ranges(self):
        out, start = [], 0
        for i in range(1, len(self.tags) + 1):
            if i == len(self.tags) or self.tags[i] != self.tags[start]:
                out.append((self.tags[start], start, i - start))
                start = i
        return out

    def bytes_per_frame(self):
        return self.w * self.h          # μάσκα + δεδομένα

    def total_bytes(self):
        return self.bytes_per_frame() * len(self.frames)

    def sheet(self, cols=12):
        rows = (len(self.frames) + cols - 1) // cols
        img = blank(cols * self.w, rows * self.h, None)
        for i, f in enumerate(self.frames):
            ox, oy = (i % cols) * self.w, (i // cols) * self.h
            for j in range(self.h):
                img[oy + j][ox:ox + self.w] = list(f[j])
        return img
