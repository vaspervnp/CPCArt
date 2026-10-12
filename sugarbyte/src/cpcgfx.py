"""Βάση για τα γραφικά Mode 0 του match-3: παλέτα, εικόνες από pens, PNG, καμβάς.

Καθαρή Python (zlib + struct) — καμία εξάρτηση.

Mode 0: 160x200 pixels, 16 pens, 2 pixels το byte, αναλογία pixel 2:1.
Ένα *κελί* του ταμπλό είναι 12 pixels φάρδος x 24 γραμμές, δηλαδή **τετράγωνο
στην οθόνη** (24x24 «μονάδες») και 6 bytes τη γραμμή.
"""
import struct
import zlib

# (χαρακτήρας ASCII, όνομα firmware, firmware #, RGB, χρήση)
#
# Το pen 0 είναι ΚΑΙ το φόντο του ταμπλό ΚΑΙ η μάσκα των sprites: ό,τι είναι
# μαύρο σε ένα candy είναι διάφανο, άρα το περίγραμμα δεν μπορεί να είναι
# μαύρο — είναι το pen 3 (μπλε της νύχτας).
#
# Τα pens 5-15 είναι τα έξι χρώματα των candies, βάση + σκιά. Ο πίνακας
# CANDY_PENS δίνει το ζεύγος κάθε χρώματος· το πορτοκαλί και το κίτρινο
# μοιράζονται τη σκιά τους (pen 8), γι' αυτό χρειάζεται πίνακας και όχι τύπος.
PALETTE = [
    ('.', 'Black',           0, (0x00, 0x00, 0x00), 'φόντο ταμπλό / μάσκα'),
    ('W', 'Bright white',   26, (0xFF, 0xFF, 0xFF), 'ανταύγεια, ρίγες, γράμματα'),
    ('G', 'White',          13, (0x80, 0x80, 0x80), 'γκρι: πλέγμα, γλάσο, χρώμια'),
    ('K', 'Blue',            1, (0x00, 0x00, 0x80), 'περίγραμμα, σκιά, ταμπλό HUD'),
    ('C', 'Bright cyan',    20, (0x00, 0xFF, 0xFF), 'ζελέ, εφέ, τόνος UI'),
    ('r', 'Bright red',      6, (0xFF, 0x00, 0x00), 'ΚΟΚΚΙΝΟ — βάση'),
    ('R', 'Red',             3, (0x80, 0x00, 0x00), 'ΚΟΚΚΙΝΟ — σκιά, σοκολάτα'),
    ('o', 'Orange',         15, (0xFF, 0x80, 0x00), 'ΠΟΡΤΟΚΑΛΙ — βάση'),
    ('O', 'Yellow',         12, (0x80, 0x80, 0x00), 'ΠΟΡΤΟΚΑΛΙ+ΚΙΤΡΙΝΟ — σκιά'),
    ('y', 'Bright yellow',  24, (0xFF, 0xFF, 0x00), 'ΚΙΤΡΙΝΟ — βάση'),
    ('g', 'Bright green',   18, (0x00, 0xFF, 0x00), 'ΠΡΑΣΙΝΟ — βάση'),
    ('N', 'Green',           9, (0x00, 0x80, 0x00), 'ΠΡΑΣΙΝΟ — σκιά'),
    ('b', 'Sky blue',       11, (0x00, 0x80, 0xFF), 'ΜΠΛΕ — βάση'),
    ('B', 'Bright blue',     2, (0x00, 0x00, 0xFF), 'ΜΠΛΕ — σκιά'),
    ('m', 'Bright magenta',  8, (0xFF, 0x00, 0xFF), 'ΜΩΒ — βάση'),
    ('M', 'Magenta',         4, (0x80, 0x00, 0x80), 'ΜΩΒ — σκιά'),
]

PEN   = {p[0]: i for i, p in enumerate(PALETTE)}
RGB   = [p[3] for p in PALETTE]
FW    = [p[2] for p in PALETTE]
NAMES = [p[1] for p in PALETTE]
CHARS = [p[0] for p in PALETTE]
USAGE = [p[4] for p in PALETTE]

# Ρόλοι — ο κώδικας των σχημάτων δεν αναφέρεται σε γυμνούς αριθμούς.
PEN_MASK  = 0    # φόντο ταμπλό και διάφανο των sprites
PEN_HI    = 1    # ανταύγεια
PEN_GREY  = 2
PEN_LINE  = 3    # περίγραμμα candy, πλέγμα, σκιά
PEN_JELLY = 4

# Τα έξι χρώματα των candies: (βάση, σκιά). Η σειρά ΕΙΝΑΙ ο κωδικός χρώματος.
CANDY_PENS = [
    ('red',    PEN['r'], PEN['R']),
    ('orange', PEN['o'], PEN['O']),
    ('yellow', PEN['y'], PEN['O']),
    ('green',  PEN['g'], PEN['N']),
    ('blue',   PEN['b'], PEN['B']),
    ('purple', PEN['m'], PEN['M']),
]
CANDY_NAMES = [c[0] for c in CANDY_PENS]

# Το κελί του ταμπλό και το κελί του HUD, σε pixels Mode 0 x γραμμές.
CW, CH = 12, 24
HW, HH = 4, 8

# Firmware -> RGB, και τα 27 ονόματα, για έλεγχο της παλέτας.
FW_RGB = [
    (0x00,0x00,0x00), (0x00,0x00,0x80), (0x00,0x00,0xFF), (0x80,0x00,0x00),
    (0x80,0x00,0x80), (0x80,0x00,0xFF), (0xFF,0x00,0x00), (0xFF,0x00,0x80),
    (0xFF,0x00,0xFF), (0x00,0x80,0x00), (0x00,0x80,0x80), (0x00,0x80,0xFF),
    (0x80,0x80,0x00), (0x80,0x80,0x80), (0x80,0x80,0xFF), (0xFF,0x80,0x00),
    (0xFF,0x80,0x80), (0xFF,0x80,0xFF), (0x00,0xFF,0x00), (0x00,0xFF,0x80),
    (0x00,0xFF,0xFF), (0x80,0xFF,0x00), (0x80,0xFF,0x80), (0x80,0xFF,0xFF),
    (0xFF,0xFF,0x00), (0xFF,0xFF,0x80), (0xFF,0xFF,0xFF),
]
FW_NAMES = [
    'Black', 'Blue', 'Bright blue', 'Red', 'Magenta', 'Mauve', 'Bright red',
    'Purple', 'Bright magenta', 'Green', 'Cyan', 'Sky blue', 'Yellow', 'White',
    'Pastel blue', 'Orange', 'Pink', 'Pastel magenta', 'Bright green',
    'Sea green', 'Bright cyan', 'Lime', 'Pastel green', 'Pastel cyan',
    'Bright yellow', 'Pastel yellow', 'Bright white',
]

assert len(PALETTE) == 16
assert len(set(CHARS)) == 16, 'κάθε pen θέλει μοναδικό χαρακτήρα ASCII'
# Το όνομα και το RGB κάθε pen είναι αντίγραφα του firmware number του.
assert all(p[1] == FW_NAMES[p[2]] and p[3] == FW_RGB[p[2]] for p in PALETTE), \
    'pen με όνομα ή RGB που δεν ταιριάζει στο firmware number του'
assert len(set(FW)) == 16, 'δύο pens με το ίδιο firmware number'


# ------------------------------------------------------------------ εικόνες
# Μια «εικόνα» είναι λίστα γραμμών, κάθε γραμμή λίστα pens· None = διάφανο.

def blank(w, h, pen=None):
    return [[pen] * w for _ in range(h)]


def parse_art(text, transparent='-'):
    """ASCII art -> γραμμές pens, με τους χαρακτήρες της παλέτας."""
    rows = []
    for line in text.strip('\n').splitlines():
        line = line.strip()
        if line:
            rows.append([None if ch == transparent else PEN[ch] for ch in line])
    return rows


def stamp(dst, art, x=0, y=0):
    for j, row in enumerate(art):
        for i, pen in enumerate(row):
            if pen is None:
                continue
            yy, xx = y + j, x + i
            if 0 <= yy < len(dst) and 0 <= xx < len(dst[0]):
                dst[yy][xx] = pen
    return dst


def opaque(img, pen=PEN_MASK):
    """Αντίγραφο με το διάφανο γεμισμένο — για τα κελιά, που δεν έχουν μάσκα."""
    return [[pen if p is None else p for p in row] for row in img]


def recolour(img, mapping):
    return [[mapping.get(p, p) for p in row] for row in img]


def nonempty(img):
    return any(p is not None for row in img for p in row)


def pens_used(img):
    return sorted({p for row in img for p in row if p is not None})


# --------------------------------------------------------- κωδικοποίηση CPC
# Mode 0: δύο pixels το byte, με τα bits μπλεγμένα. Αριστερό pixel a, δεξί b:
#   a: bit3->b7  bit2->b3  bit1->b5  bit0->b1
#   b: bit3->b6  bit2->b2  bit1->b4  bit0->b0

def mode0_byte(a, b):
    return (((a >> 3) & 1) << 7 | ((a >> 2) & 1) << 3 |
            ((a >> 1) & 1) << 5 | (a & 1) << 1 |
            ((b >> 3) & 1) << 6 | ((b >> 2) & 1) << 2 |
            ((b >> 1) & 1) << 4 | (b & 1))


def encode_opaque(img):
    """Εικόνα -> bytes Mode 0. Το διάφανο γίνεται pen 0."""
    out = bytearray()
    for row in img:
        assert len(row) % 2 == 0, 'το φάρδος πρέπει να είναι ζυγό'
        for i in range(0, len(row), 2):
            a, b = row[i], row[i + 1]
            out.append(mode0_byte(0 if a is None else a, 0 if b is None else b))
    return bytes(out)


def encode_masked(img):
    """Εικόνα -> bytes Mode 0 με μάσκα, πλεγμένα mask,data ανά γραμμή.

    Η μάσκα έχει pen 15 (όλα τα bits) όπου το pixel είναι διάφανο, 0 αλλού:
    `AND mask` μετά `OR data`. Το πλάτος σε bytes ΔΕΔΟΜΕΝΩΝ είναι len(row)//2,
    η γραμμή στη μνήμη είναι το διπλό.
    """
    out = bytearray()
    for row in img:
        assert len(row) % 2 == 0
        for i in range(0, len(row), 2):
            a, b = row[i], row[i + 1]
            out.append(mode0_byte(15 if a is None else 0, 15 if b is None else 0))
            out.append(mode0_byte(0 if a is None else a, 0 if b is None else b))
    return bytes(out)


# ------------------------------------------------------------------ σετ sprites

class SpriteSet:
    """Καρέ ίδιου μεγέθους, ομαδοποιημένα σε tags που μένουν συνεχόμενα."""

    def __init__(self, name, w, h, masked=True, note=''):
        self.name, self.w, self.h = name, w, h
        self.masked = masked
        self.note = note
        self.frames, self.names, self.tags = [], [], []

    def add(self, img, name, tag):
        assert len(img) == self.h and all(len(r) == self.w for r in img), \
            '%s/%s: %dx%d, περίμενα %dx%d' % (self.name, name, len(img[0]), len(img),
                                              self.w, self.h)
        if self.tags and self.tags[-1] != tag and tag in self.tags:
            raise ValueError('το tag %s δεν θα έμενε συνεχόμενο' % tag)
        self.frames.append([list(r) for r in img])
        self.names.append(name)
        self.tags.append(tag)
        return len(self.frames) - 1

    def tag_ranges(self):
        out, start = [], 0
        for i in range(1, len(self.tags) + 1):
            if i == len(self.tags) or self.tags[i] != self.tags[start]:
                out.append((self.tags[start], start, i - 1))
                start = i
        return out

    def frames_of(self, tag):
        return [i for i, t in enumerate(self.tags) if t == tag]

    def bytes_per_frame(self):
        return self.w * self.h if self.masked else self.w * self.h // 2

    def total_bytes(self):
        return self.bytes_per_frame() * len(self.frames)

    def sheet(self, cols=8):
        rows = (len(self.frames) + cols - 1) // cols
        img = blank(cols * self.w, rows * self.h, None)
        for i, f in enumerate(self.frames):
            ox, oy = (i % cols) * self.w, (i // cols) * self.h
            for j in range(self.h):
                img[oy + j][ox:ox + self.w] = list(f[j])
        return img


# ------------------------------------------------------------------- PNG

def _png(path, w, h, color_type, raw_rows, plte=None, trns=None):
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r for r in raw_rows)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, color_type, 0, 0, 0))
    if plte:
        png += chunk(b'PLTE', plte)
    if trns is not None:
        png += chunk(b'tRNS', trns)
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def write_indexed_png(path, img, transparent_pen0=False):
    """Αυθεντικά pixels Mode 0, PNG 16 χρωμάτων με την παλέτα του CPC."""
    h, w = len(img), len(img[0])
    plte = b''.join(bytes(c) for c in RGB)
    trns = b'\x00' + b'\xff' * 15 if transparent_pen0 else None
    rows = [bytes(0 if p is None else p for p in row) for row in img]
    _png(path, w, h, 3, rows, plte, trns)


class Canvas:
    """Καμβάς RGB για προεπισκοπήσεις και mockups."""

    def __init__(self, w, h, bg=(22, 22, 30)):
        self.w, self.h = w, h
        self.px = [bytearray(bytes(bg) * w) for _ in range(h)]

    def rect(self, x, y, w, h, rgb):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        seg = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            self.px[yy][x0 * 3:x1 * 3] = seg

    def frame(self, x, y, w, h, rgb):
        self.rect(x, y, w, 1, rgb)
        self.rect(x, y + h - 1, w, 1, rgb)
        self.rect(x, y, 1, h, rgb)
        self.rect(x + w - 1, y, 1, h, rgb)

    def blit_pens(self, img, x, y, sx, sy):
        """Κάθε pixel Mode 0 γίνεται sx x sy pixels οθόνης. None = δεν ζωγραφίζει."""
        for j, row in enumerate(img):
            for i, pen in enumerate(row):
                if pen is not None:
                    self.rect(x + i * sx, y + j * sy, sx, sy, RGB[pen])

    def text(self, s, x, y, scale, rgb):
        for ch in s.upper():
            for j, line in enumerate(FONT.get(ch, FONT['?'])):
                for i, c in enumerate(line):
                    if c == '#':
                        self.rect(x + i * scale, y + j * scale, scale, scale, rgb)
            x += 4 * scale
        return x

    def text_w(self, s, scale):
        return len(s) * 4 * scale

    def save(self, path):
        _png(path, self.w, self.h, 2, [bytes(r) for r in self.px])


# Γραμματοσειρά 3x5 μόνο για τις ετικέτες των προεπισκοπήσεων (όχι του παιχνιδιού).
_F = """
A .#. #.# ### #.# #.#|B ##. #.# ##. #.# ##.|C .## #.. #.. #.. .##|D ##. #.# #.# #.# ##.
E ### #.. ##. #.. ###|F ### #.. ##. #.. #..|G .## #.. #.# #.# .##|H #.# #.# ### #.# #.#
I ### .#. .#. .#. ###|J ..# ..# ..# #.# .#.|K #.# #.# ##. #.# #.#|L #.. #.. #.. #.. ###
M #.# ### ### #.# #.#|N ##. #.# #.# #.# #.#|O .#. #.# #.# #.# .#.|P ##. #.# ##. #.. #..
Q .#. #.# #.# ##. .##|R ##. #.# ##. #.# #.#|S .## #.. .#. ..# ##.|T ### .#. .#. .#. .#.
U #.# #.# #.# #.# ###|V #.# #.# #.# #.# .#.|W #.# #.# ### ### #.#|X #.# #.# .#. #.# #.#
Y #.# #.# .#. .#. .#.|Z ### ..# .#. #.. ###|0 ### #.# #.# #.# ###|1 .#. ##. .#. .#. ###
2 ##. ..# .#. #.. ###|3 ##. ..# .#. ..# ##.|4 #.# #.# ### ..# ..#|5 ### #.. ##. ..# ##.
6 .## #.. ### #.# ###|7 ### ..# .#. .#. .#.|8 ### #.# ### #.# ###|9 ### #.# ### ..# ##.
_ ... ... ... ... ###|- ... ... ### ... ...|+ ... .#. ### .#. ...|. ... ... ... ... .#.
: ... .#. ... .#. ...|( .#. #.. #.. #.. .#.|) .#. ..# ..# ..# .#.|/ ..# ..# .#. #.. #..
x ... #.# .#. #.# ...|? ##. ..# .#. ... .#.|= ... ### ... ### ...|, ... ... ... .#. #..
"""
FONT = {' ': ['...'] * 5}
for _chunk in _F.replace('\n', '|').split('|'):
    _chunk = _chunk.strip()
    if _chunk:
        _parts = _chunk.split(' ')
        FONT['*' if _parts[0] == 'x' else _parts[0].upper()] = _parts[1:]
