"""Shared helpers: CPC palette, 8x16 Mode 0 tiles, tile bank with dedupe, PNG output.

Pure Python (zlib + struct), no PIL/numpy needed.
Coordinates: a tile is 8 Mode 0 pixels wide and 16 rows tall. A Mode 0 pixel is twice as
wide as it is tall, so a tile is square on screen (16x16 "visual units").
"""
import struct
import zlib

# pen -> (letter, name, CPC firmware ink, RGB)
PALETTE = [
    ('k', 'Black',         0, (0x00, 0x00, 0x00)),
    ('b', 'Blue',          1, (0x00, 0x00, 0x80)),
    ('g', 'Grey',         13, (0x80, 0x80, 0x80)),
    ('w', 'Bright White', 26, (0xFF, 0xFF, 0xFF)),
    ('y', 'Bright Yellow', 24, (0xFF, 0xFF, 0x00)),
    ('o', 'Yellow',       12, (0x80, 0x80, 0x00)),
    ('r', 'Red',           3, (0x80, 0x00, 0x00)),
    ('R', 'Bright Red',    6, (0xFF, 0x00, 0x00)),
    ('n', 'Orange',       15, (0xFF, 0x80, 0x00)),
    ('v', 'Green',         9, (0x00, 0x80, 0x00)),
    ('l', 'Lime',         21, (0x80, 0xFF, 0x00)),
    ('s', 'Sky Blue',     11, (0x00, 0x80, 0xFF)),
    ('p', 'Pastel Blue',  14, (0x80, 0x80, 0xFF)),
    ('c', 'Pastel Yellow', 25, (0xFF, 0xFF, 0x80)),
    ('t', 'Cyan',         10, (0x00, 0x80, 0x80)),
    ('i', 'Pink',         16, (0xFF, 0x80, 0x80)),
]
PEN = {p[0]: i for i, p in enumerate(PALETTE)}
RGB = [p[3] for p in PALETTE]
K, B, G, W, Y, O, r_, R, N, V, L, S, P, C, T, I = range(16)

TW, TH = 8, 16  # tile size in Mode 0 pixels


def blank(w_px, h_rows, pen=0):
    return [[pen] * w_px for _ in range(h_rows)]


def parse_art(text, transparent='.'):
    """ASCII art -> rows of pens (None for transparent)."""
    rows = []
    for line in text.strip('\n').splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append([None if ch == transparent else PEN[ch] for ch in line])
    return rows


def stamp(dst, art, x, y):
    for j, row in enumerate(art):
        for i, pen in enumerate(row):
            if pen is None:
                continue
            yy, xx = y + j, x + i
            if 0 <= yy < len(dst) and 0 <= xx < len(dst[0]):
                dst[yy][xx] = pen


def cut_tiles(img):
    """Split an image (rows of pens) into a 2D list of 8x16 tiles (tuples)."""
    h, w = len(img), len(img[0])
    assert h % TH == 0 and w % TW == 0, (w, h)
    out = []
    for ty in range(h // TH):
        line = []
        for tx in range(w // TW):
            t = tuple(tuple(img[ty * TH + j][tx * TW:(tx + 1) * TW]) for j in range(TH))
            line.append(t)
        out.append(line)
    return out


class TileBank:
    """Unique tiles in insertion order, grouped by tag (tags stay contiguous)."""

    def __init__(self):
        self.tiles = []      # tuple-of-rows
        self.names = []
        self.tags = []
        self.index = {}

    def add(self, tile, name, tag):
        if tile in self.index:
            return self.index[tile]
        if self.tags and self.tags[-1] != tag and tag in self.tags:
            raise ValueError('tag %s would not be contiguous' % tag)
        idx = len(self.tiles)
        self.tiles.append(tile)
        self.names.append(name)
        self.tags.append(tag)
        self.index[tile] = idx
        return idx

    def add_image(self, img, name, tag):
        """Cut an image into tiles, add them, return a 2D list of tile indices."""
        grid = cut_tiles(img)
        rows = []
        for ty, line in enumerate(grid):
            idxs = []
            for tx, t in enumerate(line):
                nm = name if len(grid) == 1 and len(line) == 1 else '%s_%d_%d' % (name, tx, ty)
                idxs.append(self.add(t, nm, tag))
            rows.append(idxs)
        return rows

    def tag_ranges(self):
        out, start = [], 0
        for i in range(1, len(self.tags) + 1):
            if i == len(self.tags) or self.tags[i] != self.tags[start]:
                out.append((self.tags[start], start, i - 1))
                start = i
        return out

    def sheet(self, cols=8):
        n = len(self.tiles)
        rows = (n + cols - 1) // cols
        img = blank(cols * TW, rows * TH, 0)
        for i, t in enumerate(self.tiles):
            ox, oy = (i % cols) * TW, (i // cols) * TH
            for j in range(TH):
                img[oy + j][ox:ox + TW] = list(t[j])
        return img


def compose(bank, grid):
    """2D list of tile indices (None = empty) -> image of pens (None where empty)."""
    h, w = len(grid), max(len(r) for r in grid)
    img = [[None] * (w * TW) for _ in range(h * TH)]
    for ty, line in enumerate(grid):
        for tx, idx in enumerate(line):
            if idx is None:
                continue
            t = bank.tiles[idx]
            for j in range(TH):
                img[ty * TH + j][tx * TW:(tx + 1) * TW] = list(t[j])
    return img


# ---------------------------------------------------------------- PNG output

def _png(path, w, h, color_type, raw_rows, plte=None, trns=None):
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r for r in raw_rows)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, color_type, 0, 0, 0))
    if plte:
        png += chunk(b'PLTE', plte)
    if trns:
        png += chunk(b'tRNS', trns)
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def write_indexed_png(path, img):
    """Native Mode 0 pixels, 16-colour indexed PNG with the CPC palette."""
    h, w = len(img), len(img[0])
    plte = b''.join(bytes(c) for c in RGB)
    _png(path, w, h, 3, [bytes(0 if p is None else p for p in row) for row in img], plte)


class Canvas:
    """RGB canvas for previews/mockups."""

    def __init__(self, w, h, bg=(24, 24, 32)):
        self.w, self.h = w, h
        self.px = [bytearray(bytes(bg) * w) for _ in range(h)]

    def rect(self, x, y, w, h, rgb):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        seg = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            self.px[yy][x0 * 3:x1 * 3] = seg

    def blit_pens(self, img, x, y, sx, sy):
        """Draw a pen image; each Mode 0 pixel becomes sx*sy screen pixels."""
        for j, row in enumerate(img):
            yy = y + j * sy
            if yy >= self.h or yy + sy <= 0:
                continue
            for i, pen in enumerate(row):
                if pen is None:
                    continue
                self.rect(x + i * sx, yy, sx, sy, RGB[pen])

    def text(self, s, x, y, scale, rgb):
        for ch in s.upper():
            glyph = FONT.get(ch, FONT['?'])
            for j, line in enumerate(glyph):
                for i, c in enumerate(line):
                    if c == '#':
                        self.rect(x + i * scale, y + j * scale, scale, scale, rgb)
            x += 4 * scale
        return x

    def save(self, path):
        _png(path, self.w, self.h, 2, [bytes(r) for r in self.px])


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
    if not _chunk:
        continue
    _parts = _chunk.split(' ')
    FONT[_parts[0].upper() if _parts[0] != 'x' else '*'] = _parts[1:]
