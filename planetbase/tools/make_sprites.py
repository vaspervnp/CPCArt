#!/usr/bin/env python3
"""Παράγει όλα τα sprites Mode 0 του colony sim προγραμματιστικά.

    python3 tools/make_sprites.py [--anim-frames 1|2] [--out build/sprites]

Βγάζει: sprites.asm (RASM), sprites.bin, sprites_map.txt και PNG προεπισκοπήσεις.
Τίποτα δεν φορτώνεται από έτοιμα γραφικά: όλα προκύπτουν από γεωμετρία ή ASCII art.
"""

import argparse
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from palette import (PALETTE, FW, RGB, PEN_CHARS, NAMES, USAGE, pens_to_ascii,
                     PEN_OUTSIDE, PEN_DOME_FLOOR, PEN_DOME_EDGE,
                     PEN_CORR_FLOOR, PEN_CORR_EDGE, PEN_COLONIST)
import icons


# --------------------------------------------------------------------------
# 1. Κωδικοποίηση Mode 0
# --------------------------------------------------------------------------

def encode_mode0(p0, p1):
    """Ζεύγος pixels (αριστερό, δεξί) -> ένα byte οθόνης Mode 0."""
    return (((p0 >> 0) & 1) << 7) | (((p1 >> 0) & 1) << 6) | \
           (((p0 >> 2) & 1) << 5) | (((p1 >> 2) & 1) << 4) | \
           (((p0 >> 1) & 1) << 3) | (((p1 >> 1) & 1) << 2) | \
           (((p0 >> 3) & 1) << 1) | (((p1 >> 3) & 1) << 0)


def decode_mode0(b):
    """Byte οθόνης Mode 0 -> ζεύγος pixels (αριστερό, δεξί)."""
    p0 = ((b >> 7) & 1) | (((b >> 3) & 1) << 1) | (((b >> 5) & 1) << 2) | (((b >> 1) & 1) << 3)
    p1 = ((b >> 6) & 1) | (((b >> 2) & 1) << 1) | (((b >> 4) & 1) << 2) | (((b >> 0) & 1) << 3)
    return p0, p1


def flip_byte(b):
    """Το byte με τα δύο pixels του ανταλλαγμένα."""
    p0, p1 = decode_mode0(b)
    return encode_mode0(p1, p0)


FLIP_TABLE = [flip_byte(b) for b in range(256)]


# --------------------------------------------------------------------------
# 2. Γεωμετρία θόλου και δακτυλίου
# --------------------------------------------------------------------------

DOME_D      = 48          # οπτική διάμετρος θόλου
CORRIDOR_W  = 8           # οπτικό πλάτος δακτυλίου
FRAME_W     = 32          # pixels Mode 0
FRAME_H     = 64          # γραμμές
CX, CY      = FRAME_W // 2, FRAME_H // 2

OUTSIDE, DOME, CORRIDOR = 0, 1, 2

R_DOME = DOME_D / 2
R_CORR = DOME_D / 2 + CORRIDOR_W


def classify(x, y):
    """Κατηγορία του pixel (x, y) του πλαισίου, σε οπτικές συντεταγμένες (2:1)."""
    vx = (x + 0.5) * 2 - 2 * CX
    vy = (y + 0.5) - CY
    r = math.hypot(vx, vy)
    if r <= R_DOME:
        return DOME
    if r <= R_CORR:
        return CORRIDOR
    return OUTSIDE


def build_frame(ring):
    """Το πλήρες πλαίσιο 32x64 σε pens. ring=False: ο διάδρομος γίνεται φόντο."""
    cls = [[classify(x, y) for x in range(FRAME_W)] for y in range(FRAME_H)]
    if not ring:
        cls = [[OUTSIDE if c == CORRIDOR else c for c in row] for row in cls]

    def at(x, y):
        # γείτονας έξω από το πλαίσιο μετρά ως OUTSIDE
        if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
            return cls[y][x]
        return OUTSIDE

    pens = []
    for y in range(FRAME_H):
        row = []
        for x in range(FRAME_W):
            c = cls[y][x]
            if c == OUTSIDE:
                row.append(PEN_OUTSIDE)
                continue
            edge = any(at(x + dx, y + dy) != c
                       for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            if c == DOME:
                row.append(PEN_DOME_EDGE if edge else PEN_DOME_FLOOR)
            else:
                row.append(PEN_CORR_EDGE if edge else PEN_CORR_FLOOR)
        pens.append(row)
    return cls, pens


# --------------------------------------------------------------------------
# 3. Sprites
# --------------------------------------------------------------------------

class Sprite:
    """Ένα sprite: pens σε πίνακα [h][w], με w ζυγό. Τα bytes είναι γραμμικά."""

    def __init__(self, name, pens):
        self.name = name
        self.pens = pens
        self.h = len(pens)
        self.w = len(pens[0])
        if self.w % 2:
            raise ValueError(f"{name}: πλάτος {self.w} — πρέπει να είναι ζυγό")
        if any(len(r) != self.w for r in pens):
            raise ValueError(f"{name}: μη ορθογώνιο")

    @property
    def bw(self):
        return self.w // 2

    def rows_bytes(self):
        return [[encode_mode0(row[x], row[x + 1]) for x in range(0, self.w, 2)]
                for row in self.pens]

    def data(self):
        return bytes(b for row in self.rows_bytes() for b in row)


QUAD_W, QUAD_H = 16, 32
ICON_POS = (12, 14)        # θέση εικονιδίου μέσα στο πλαίσιο 32x64
OCC_POS  = (10, 26)        # θέση επικαλύμματος πληρότητας
OCC_W, OCC_H = 12, 16

CORNERS = [("nw", 0, 0), ("ne", QUAD_W, 0), ("sw", 0, QUAD_H), ("se", QUAD_W, QUAD_H)]

# 4 στήλες x 2 σειρές, με σειρά γεμίσματος που σπάει το πλέγμα οπτικά
SLOT_ORDER = [(3, 1), (6, 9), (9, 1), (0, 9), (6, 1), (3, 9), (0, 1), (9, 9)]
LEVEL_FIGURES = [0, 1, 3, 5, 8]      # αντιστοιχεί στο level_tab


def build_quads(frames):
    out = []
    for variant in ("ring", "bare"):
        pens = frames[variant][1]
        for corner, ox, oy in CORNERS:
            sub = [row[ox:ox + QUAD_W] for row in pens[oy:oy + QUAD_H]]
            out.append(Sprite(f"quad_{corner}_{variant}", sub))
    return out


def build_icons():
    out = []
    for name, art in icons.ROOM_ICONS:
        pens = icons.parse_art(art, icons.ICON_W, icons.ICON_H, what=f"icon {name}")
        out.append(Sprite(f"icon_{name}", pens))
    return out


def build_occupancy(frames_count):
    fig = icons.parse_art(icons.COLONIST, icons.COLONIST_W, icons.COLONIST_H,
                          icons.COLONIST_LEGEND, "colonist")
    out = []
    for frame in range(frames_count):
        for level, n in enumerate(LEVEL_FIGURES):
            pens = [[PEN_DOME_FLOOR] * OCC_W for _ in range(OCC_H)]
            for sx, sy in SLOT_ORDER[:n]:
                sy += frame                      # frame 1: μία γραμμή πιο κάτω
                for j, frow in enumerate(fig):
                    for i, p in enumerate(frow):
                        if p is not None:
                            pens[sy + j][sx + i] = p
            suffix = "" if frames_count == 1 else f"_f{frame}"
            out.append(Sprite(f"occ_level{level}{suffix}", pens))
    return out


def build_corridors():
    ch = [[PEN_CORR_EDGE if y in (0, 7) else PEN_CORR_FLOOR for x in range(8)]
          for y in range(8)]
    cv = [[PEN_CORR_EDGE if x in (0, 3) else PEN_CORR_FLOOR for x in range(4)]
          for y in range(16)]
    return [Sprite("corr_h", ch), Sprite("corr_v", cv)]


# --------------------------------------------------------------------------
# 4. Επαλήθευση
# --------------------------------------------------------------------------

class CheckFailed(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise CheckFailed(msg)


def hflip_pens(pens):
    return [list(reversed(r)) for r in pens]


def vflip_pens(pens):
    return list(reversed([list(r) for r in pens]))


def verify(frames, quads, icon_sprites, occ, corr):
    # 1. κωδικοποίηση
    for a, b, want in ((1, 0, 0x80), (0, 1, 0x40), (15, 15, 0xFF),
                       (0, 0, 0x00), (8, 0, 0x02)):
        got = encode_mode0(a, b)
        check(got == want, f"encode_mode0({a},{b}) = #{got:02X}, περίμενα #{want:02X}")
    for b in range(256):
        check(encode_mode0(*decode_mode0(b)) == b, f"encode(decode(#{b:02X})) != #{b:02X}")

    # 2. καθρεφτισμός
    for b in range(256):
        check(FLIP_TABLE[FLIP_TABLE[b]] == b, f"flip(flip(#{b:02X})) != #{b:02X}")

    # 3. διαστάσεις κάθε sprite
    for s in quads + icon_sprites + occ + corr:
        check(s.w % 2 == 0, f"{s.name}: μονό πλάτος {s.w}")
        check(len(s.data()) == s.bw * s.h,
              f"{s.name}: {len(s.data())} bytes αντί για {s.bw * s.h}")

    by_name = {s.name: s for s in quads}

    # 4. τα 4 τεταρτημόρια συναρμολογημένα == πλήρες πλαίσιο
    for variant in ("ring", "bare"):
        full = frames[variant][1]
        rebuilt = [[None] * FRAME_W for _ in range(FRAME_H)]
        for corner, ox, oy in CORNERS:
            q = by_name[f"quad_{corner}_{variant}"]
            for y in range(QUAD_H):
                for x in range(QUAD_W):
                    rebuilt[oy + y][ox + x] = q.pens[y][x]
        for y in range(FRAME_H):
            for x in range(FRAME_W):
                check(rebuilt[y][x] == full[y][x],
                      f"{variant}: διαφορά στο pixel ({x},{y})")

    # 5. συμμετρία τεταρτημορίων
    for variant in ("ring", "bare"):
        nw = by_name[f"quad_nw_{variant}"].pens
        check(by_name[f"quad_ne_{variant}"].pens == hflip_pens(nw),
              f"quad_ne_{variant} != οριζόντιο καθρέφτισμα του quad_nw_{variant}")
        check(by_name[f"quad_sw_{variant}"].pens == vflip_pens(nw),
              f"quad_sw_{variant} != κάθετο καθρέφτισμα του quad_nw_{variant}")

    # 6. εικονίδιο και επικάλυμμα: μέσα στον θόλο, όχι σε άκρη, χωρίς επικάλυψη
    cls, pens = frames["ring"]
    occupied = set()
    for what, (px, py), (w, h) in (("εικονίδιο", ICON_POS, (icons.ICON_W, icons.ICON_H)),
                                   ("επικάλυμμα", OCC_POS, (OCC_W, OCC_H))):
        for y in range(py, py + h):
            for x in range(px, px + w):
                check(0 <= x < FRAME_W and 0 <= y < FRAME_H,
                      f"{what}: το pixel ({x},{y}) είναι έξω από το πλαίσιο")
                check(cls[y][x] == DOME,
                      f"{what}: το pixel ({x},{y}) δεν είναι DOME")
                check(pens[y][x] == PEN_DOME_FLOOR,
                      f"{what}: το pixel ({x},{y}) είναι άκρη του θόλου")
                check((x, y) not in occupied,
                      f"{what}: επικάλυψη στο pixel ({x},{y})")
                occupied.add((x, y))


# --------------------------------------------------------------------------
# 5. Έξοδος: sprites.asm / sprites.bin / sprites_map.txt
# --------------------------------------------------------------------------

class Blob:
    """Η διάταξη των δεδομένων: ίδια σειρά σε .asm και .bin."""

    def __init__(self):
        self.items = []     # (label, bytes, sprite|None, category)
        self.groups = []    # (label, [equ...]) που μπαίνουν πριν από ένα item
        self.marks = {}     # label -> offset στην αρχή του item

    def add(self, label, data, sprite=None, category="άλλο", extra_labels=()):
        self.marks[label] = self.size()
        for e in extra_labels:
            self.marks[e] = self.size()
        self.items.append((label, bytes(data), sprite, category, tuple(extra_labels)))

    def size(self):
        return sum(len(i[1]) for i in self.items)

    def data(self):
        return b"".join(i[1] for i in self.items)


def build_blob(quads, icon_sprites, occ, corr, anim_frames):
    blob = Blob()

    blob.add("dome_quads", b"", category="—")        # ετικέτα ομάδας, 0 bytes
    for s in quads:
        blob.add(s.name, s.data(), s, "τεταρτημόρια θόλου")

    blob.add("room_icons", b"", category="—")
    for s in icon_sprites:
        blob.add(s.name, s.data(), s, "εικονίδια δωματίων")

    blob.add("occupancy", b"", category="—")
    for s in occ:
        blob.add(s.name, s.data(), s, "επικαλύμματα πληρότητας")

    for s in corr:
        blob.add(s.name, s.data(), s, "ευθύγραμμοι διάδρομοι")

    blob.add("palette_fw", bytes(FW), None, "παλέτα")

    pad = (-blob.size()) % 256
    if pad:
        blob.add("sprites_pad", bytes(pad), None, "στοίχιση")

    blob.add("flip_mode0", bytes(FLIP_TABLE), None, "πίνακας καθρεφτισμού")
    return blob


ASM_HEADER = """\
; sprites.asm — Colony sim, Amstrad CPC Mode 0
; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από tools/make_sprites.py — μην το επεξεργάζεσαι με το χέρι.
;
; Τα δεδομένα είναι γραμμικά (γραμμή-γραμμή, πάνω προς τα κάτω), ΟΧΙ στη διάταξη
; της μνήμης οθόνης. Τον υπολογισμό διεύθυνσης τον κάνει η ρουτίνα blit.
; Όλα τα blits είναι αδιαφανή — δεν χρειάζεται mask.
;
; Το μπλοκ πρέπει να φορτωθεί σε διεύθυνση πολλαπλάσιο του 256, ώστε το
; flip_mode0 να πέφτει σε σελίδα (το padding πριν από αυτό είναι ήδη υπολογισμένο).
"""


def emit_asm(blob, anim_frames, occ_count):
    L = [ASM_HEADER]
    L.append("QUAD_W      equ %d           ; bytes ανά γραμμή" % (QUAD_W // 2))
    L.append("QUAD_H      equ %d" % QUAD_H)
    L.append("QUAD_SIZE   equ %d" % (QUAD_W // 2 * QUAD_H))
    L.append("QUAD_BARE   equ %d          ; dome_quads + QUAD_BARE + corner*QUAD_SIZE" % (4 * QUAD_W // 2 * QUAD_H))
    L.append("ICON_W      equ %d" % (icons.ICON_W // 2))
    L.append("ICON_H      equ %d" % icons.ICON_H)
    L.append("ICON_SIZE   equ %d          ; room_icons + type*ICON_SIZE" % (icons.ICON_W // 2 * icons.ICON_H))
    L.append("ICON_X      equ %d           ; bytes, σχετικά με την αρχή του θόλου" % (ICON_POS[0] // 2))
    L.append("ICON_Y      equ %d" % ICON_POS[1])
    L.append("OCC_W       equ %d" % (OCC_W // 2))
    L.append("OCC_H       equ %d" % OCC_H)
    L.append("OCC_SIZE    equ %d          ; occupancy + level*OCC_SIZE" % (OCC_W // 2 * OCC_H))
    L.append("OCC_X       equ %d           ; bytes" % (OCC_POS[0] // 2))
    L.append("OCC_Y       equ %d" % OCC_POS[1])
    L.append("OCC_LEVELS  equ %d" % len(LEVEL_FIGURES))
    if anim_frames > 1:
        L.append("OCC_FRAMES  equ %d" % anim_frames)
        L.append("OCC_FRAME   equ %d         ; occupancy + frame*OCC_FRAME + level*OCC_SIZE"
                 % (len(LEVEL_FIGURES) * OCC_W // 2 * OCC_H))
    L.append("CORR_H_W    equ 4")
    L.append("CORR_H_H    equ 8")
    L.append("CORR_V_W    equ 2")
    L.append("CORR_V_H    equ 16")
    L.append("")

    for label, data, sprite, category, extras in blob.items:
        for e in extras:
            L.append("%s:" % e)
        if sprite is None:
            if label == "flip_mode0":
                L.append("")
                L.append("; --- πίνακας καθρεφτισμού: flip_mode0[b] = b με ανταλλαγμένα pixels ---")
                L.append("align 256")
                L.append("flip_mode0:")
                for i in range(0, 256, 16):
                    L.append("    db " + ",".join("#%02X" % b for b in data[i:i + 16]))
                continue
            if label == "sprites_pad":
                L.append("")
                L.append("; --- %d bytes γέμισμα ώστε το flip_mode0 να πέσει σε σελίδα 256 ---" % len(data))
                L.append("sprites_pad:")
                L.append("    defs %d,#00" % len(data))
                continue
            if label == "palette_fw":
                L.append("")
                L.append("; --- παλέτα: 16 firmware colour numbers, pen 0..15 ---")
                L.append("palette_fw:")
                L.append("    db " + ",".join("#%02X" % b for b in data))
                for i, (pen, name, fw, rgb, ch, use) in enumerate(PALETTE):
                    L.append("    ; pen %2d  FW %2d  %-13s %s" % (pen, fw, name, use))
                continue
            L.append("")
            L.append("%s:" % label)
            continue

        L.append("")
        L.append("; %s — %d x %d pixels (%d x %d bytes), %d bytes"
                 % (label, sprite.w, sprite.h, sprite.bw, sprite.h, len(data)))
        L.append("%s:" % label)
        for row_pens, row_bytes in zip(sprite.pens, sprite.rows_bytes()):
            L.append("    db " + ",".join("#%02X" % b for b in row_bytes)
                     + "   ; " + pens_to_ascii(row_pens))
    L.append("")
    return "\n".join(L)


ASM_BYTE_RE = re.compile(r"^\s*db\s+(.*)$", re.I)
ASM_DEFS_RE = re.compile(r"^\s*defs\s+(\d+)\s*,\s*#([0-9A-Fa-f]{1,2})\s*$", re.I)


def parse_asm_bytes(text):
    """Ξαναδιαβάζει το παραγόμενο .asm και βγάζει τα bytes του — για την επαλήθευση 7."""
    out = bytearray()
    for line in text.splitlines():
        line = line.split(";", 1)[0]
        if not line.strip():
            continue
        m = ASM_DEFS_RE.match(line)
        if m:
            out.extend(bytes([int(m.group(2), 16)]) * int(m.group(1)))
            continue
        m = ASM_BYTE_RE.match(line)
        if m:
            for tok in m.group(1).split(","):
                tok = tok.strip()
                if tok:
                    out.append(int(tok.lstrip("#"), 16))
    return bytes(out)


def emit_map(blob):
    L = ["# sprite                offset  μέγεθος  διαστάσεις        κατηγορία",
         "# " + "-" * 74]
    for label, data, sprite, category, extras in blob.items:
        if not data and sprite is None:
            L.append("# %-22s #%04X   %6s  %-16s %s"
                     % (label, blob.marks[label], "-", "(ετικέτα ομάδας)", category))
            continue
        dims = "%dx%d px" % (sprite.w, sprite.h) if sprite else "-"
        L.append("  %-22s #%04X   %6d  %-16s %s"
                 % (label, blob.marks[label], len(data), dims, category))
    L.append("")
    L.append("  %-22s #%04X   %6d" % ("ΣΥΝΟΛΟ", 0, blob.size()))
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# 6. Προεπισκοπήσεις PNG
# --------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageFont

SCALE = 4
PIX_W, PIX_H = 2 * SCALE, 1 * SCALE      # αναλογία 2:1 -> 8x4 πραγματικά pixels


def sprite_from_bytes(data, bw, h):
    """Αποκωδικοποιεί bytes σε pens — η προεπισκόπηση επαληθεύει την κωδικοποίηση."""
    pens = []
    for y in range(h):
        row = []
        for b in data[y * bw:(y + 1) * bw]:
            row.extend(decode_mode0(b))
        pens.append(row)
    return pens


def render(pens, grid=False):
    w, h = len(pens[0]), len(pens)
    img = Image.new("RGB", (w * PIX_W, h * PIX_H))
    d = ImageDraw.Draw(img)
    for y in range(h):
        for x in range(w):
            d.rectangle([x * PIX_W, y * PIX_H, (x + 1) * PIX_W - 1, (y + 1) * PIX_H - 1],
                        fill=RGB[pens[y][x]])
    if grid:
        for x in range(1, w):
            d.line([(x * PIX_W, 0), (x * PIX_W, h * PIX_H)], fill=(48, 48, 48))
        for y in range(1, h):
            d.line([(0, y * PIX_H), (w * PIX_W, y * PIX_H)], fill=(48, 48, 48))
    return img


def composite_pens(blob, icon_type, level):
    """Πλήρης θόλος, συντεθειμένος ΑΠΟ ΤΑ BYTES (όχι από την ενδιάμεση εικόνα)."""
    data = blob.data()
    out = [[PEN_OUTSIDE] * FRAME_W for _ in range(FRAME_H)]

    for corner, ox, oy in CORNERS:
        off = blob.marks["quad_%s_ring" % corner]
        q = sprite_from_bytes(data[off:off + QUAD_W // 2 * QUAD_H], QUAD_W // 2, QUAD_H)
        for y in range(QUAD_H):
            for x in range(QUAD_W):
                out[oy + y][ox + x] = q[y][x]

    off = blob.marks["room_icons"] + icon_type * (icons.ICON_W // 2 * icons.ICON_H)
    ic = sprite_from_bytes(data[off:off + icons.ICON_W // 2 * icons.ICON_H],
                           icons.ICON_W // 2, icons.ICON_H)
    for y in range(icons.ICON_H):
        for x in range(icons.ICON_W):
            out[ICON_POS[1] + y][ICON_POS[0] + x] = ic[y][x]

    off = blob.marks["occupancy"] + level * (OCC_W // 2 * OCC_H)
    oc = sprite_from_bytes(data[off:off + OCC_W // 2 * OCC_H], OCC_W // 2, OCC_H)
    for y in range(OCC_H):
        for x in range(OCC_W):
            out[OCC_POS[1] + y][OCC_POS[0] + x] = oc[y][x]

    return out


# Ισοδύναμα ASCII, για την περίπτωση που δεν βρεθεί γραμματοσειρά με ελληνικά.
CATEGORY_ASCII = {
    "τεταρτημόρια θόλου":      "dome quadrants",
    "εικονίδια δωματίων":      "room icons",
    "επικαλύμματα πληρότητας": "occupancy overlays",
    "ευθύγραμμοι διάδρομοι":   "straight corridors",
}

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
]


def font(size=12):
    """(γραμματοσειρά, έχει_ελληνικά). Χωρίς TTF πέφτουμε στο bitmap font + ASCII."""
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size), True
        except OSError:
            continue
    try:
        return ImageFont.load_default(size), False
    except TypeError:
        return ImageFont.load_default(), False


def make_sheet(entries, path):
    """Όλα τα sprites σε ένα φύλλο με πλέγμα και ετικέτες, ομαδοποιημένα."""
    F, greek = font()
    PAD, LABEL_H, HEAD_H, MARGIN, LIMIT = 12, 16, 24, 14, 1000

    groups = []
    for category, name, pens in entries:
        if not groups or groups[-1][0] != category:
            groups.append((category, []))
        groups[-1][1].append((name, pens))

    tiles = {n: render(p, grid=True) for _, g in groups for n, p in g}

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # το κελί είναι όσο το πλατύτερο από sprite και ετικέτα, ώστε να μην πατάνε
    cell_w = {n: max(im.width, int(probe.textlength(n, font=F)) + 4)
              for n, im in tiles.items()}

    layout, total_h, sheet_w = [], MARGIN, 0
    for category, members in groups:
        total_h += HEAD_H
        rows, cur, cur_w = [], [], 0
        for name, _ in members:
            w = cell_w[name] + PAD
            if cur and cur_w + w > LIMIT:
                rows.append(cur)
                cur, cur_w = [], 0
            cur.append(name)
            cur_w += w
        if cur:
            rows.append(cur)
        for r in rows:
            total_h += max(tiles[n].height for n in r) + LABEL_H + PAD
            sheet_w = max(sheet_w, sum(cell_w[n] + PAD for n in r))
        layout.append((category, rows))
        total_h += PAD

    img = Image.new("RGB", (sheet_w + 2 * MARGIN, total_h + MARGIN), (24, 24, 32))
    d = ImageDraw.Draw(img)

    y = MARGIN
    for category, rows in layout:
        label = category if greek else CATEGORY_ASCII.get(category, category)
        d.text((MARGIN, y), label, fill=(255, 210, 120), font=F)
        y += HEAD_H
        for r in rows:
            x, rh = MARGIN, max(tiles[n].height for n in r)
            for n in r:
                im = tiles[n]
                img.paste(im, (x, y))
                d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                            outline=(90, 90, 100))
                d.text((x, y + rh + 3), n, fill=(200, 200, 210), font=F)
                x += cell_w[n] + PAD
            y += rh + LABEL_H + PAD
        y += PAD
    img.save(path)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.join(os.path.dirname(here), "build", "sprites")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anim-frames", type=int, choices=(1, 2), default=1,
                    help="frames ανά επίπεδο πληρότητας (2 = απλό animation)")
    ap.add_argument("--out", default=default_out, help="φάκελος εξόδου")
    ap.add_argument("--composite-icon", type=int, default=5,
                    help="τύπος δωματίου για το composite.png (προεπιλογή: θερμοκήπιο)")
    args = ap.parse_args()

    frames = {"ring": build_frame(True), "bare": build_frame(False)}
    quads = build_quads(frames)
    icon_sprites = build_icons()
    occ = build_occupancy(args.anim_frames)
    corr = build_corridors()

    try:
        verify(frames, quads, icon_sprites, occ, corr)
    except CheckFailed as e:
        print("ΑΠΟΤΥΧΙΑ ΕΠΑΛΗΘΕΥΣΗΣ: %s" % e, file=sys.stderr)
        return 1

    blob = build_blob(quads, icon_sprites, occ, corr, args.anim_frames)
    asm = emit_asm(blob, args.anim_frames, len(occ))
    binary = blob.data()

    # 7. το .bin ταυτίζεται με τα δεδομένα του .asm
    from_asm = parse_asm_bytes(asm)
    if from_asm != binary:
        print("ΑΠΟΤΥΧΙΑ ΕΠΑΛΗΘΕΥΣΗΣ: sprites.asm (%d bytes) != sprites.bin (%d bytes)"
              % (len(from_asm), len(binary)), file=sys.stderr)
        for i, (a, b) in enumerate(zip(from_asm, binary)):
            if a != b:
                print("  πρώτη διαφορά στο offset #%04X: #%02X vs #%02X" % (i, a, b),
                      file=sys.stderr)
                break
        return 1

    prev = os.path.join(args.out, "preview")
    os.makedirs(prev, exist_ok=True)

    with open(os.path.join(args.out, "sprites.asm"), "w", encoding="utf-8") as f:
        f.write(asm)
    with open(os.path.join(args.out, "sprites.bin"), "wb") as f:
        f.write(binary)
    with open(os.path.join(args.out, "sprites_map.txt"), "w", encoding="utf-8") as f:
        f.write(emit_map(blob))

    # PNG ανά sprite, αποκωδικοποιημένα από τα bytes
    entries = []
    for label, data, sprite, category, extras in blob.items:
        if sprite is None:
            continue
        pens = sprite_from_bytes(data, sprite.bw, sprite.h)
        render(pens).save(os.path.join(prev, label + ".png"))
        entries.append((category, label, pens))

    make_sheet(entries, os.path.join(prev, "sheet.png"))
    render(composite_pens(blob, args.composite_icon, 3)).save(
        os.path.join(prev, "composite.png"))

    # 8. σύνοψη
    cats = {}
    for label, data, sprite, category, extras in blob.items:
        if not data:
            continue
        n, tot = cats.get(category, (0, 0))
        cats[category] = (n + 1, tot + len(data))
    print("Γράφτηκαν στο %s" % args.out)
    print()
    print("  %-26s %6s %8s" % ("κατηγορία", "πλήθος", "bytes"))
    print("  " + "-" * 42)
    for c, (n, tot) in cats.items():
        print("  %-26s %6d %8d" % (c, n, tot))
    print("  " + "-" * 42)
    print("  %-26s %6d %8d  (%.2f KB)"
          % ("ΣΥΝΟΛΟ", sum(n for n, _ in cats.values()), len(binary), len(binary) / 1024))
    print()
    print("  Όλες οι επαληθεύσεις (1-8) πέρασαν.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
