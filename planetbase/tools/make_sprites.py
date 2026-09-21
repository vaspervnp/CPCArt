#!/usr/bin/env python3
"""Παράγει όλα τα sprites Mode 0 του colony sim προγραμματιστικά.

    python3 tools/make_sprites.py [--quads all|nw] [--uniform-quads] [--out DIR]

Βγάζει: sprites.asm (RASM), sprites.bin, sprites_map.txt, dump για το Aseprite
και PNG προεπισκοπήσεις. Τίποτα δεν φορτώνεται από έτοιμα γραφικά.

Οι θόλοι, οι δακτύλιοι, οι διάδρομοι και τα σημεία σύνδεσης είναι ΞΕΧΩΡΙΣΤΑ
sprites με μάσκα (screen = (screen AND mask) OR data), ώστε να συντίθενται
ελεύθερα. Τα εικονίδια και τα επικαλύμματα πληρότητας μένουν αδιαφανή: κάθονται
πάντα πάνω στο δάπεδο του θόλου και δεν χρειάζονται μάσκα.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from palette import (PALETTE, FW, RGB, PEN_CHARS, pens_to_ascii, PEN_OUTSIDE,
                     PEN_DOME_FLOOR)
import geometry as geo
import icons
import structures as st


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
    p0, p1 = decode_mode0(b)
    return encode_mode0(p1, p0)


def mask_mode0(p0, p1):
    """Μάσκα: 1 στα bits των ΔΙΑΦΑΝΩΝ pixels, ώστε το AND να κρατά το φόντο."""
    return encode_mode0(15 if p0 == PEN_OUTSIDE else 0,
                        15 if p1 == PEN_OUTSIDE else 0)


FLIP_TABLE = [flip_byte(b) for b in range(256)]


def hflip_row(row, masked):
    """Οριζόντιο καθρέφτισμα μιας γραμμής bytes.

    Αντίστροφη σειρά bytes, με κάθε byte να περνά από το flip_mode0. Στα sprites
    με μάσκα το ζεύγος (mask, data) μένει ενιαίο — αντιστρέφονται τα ΖΕΥΓΗ.
    """
    if masked:
        pairs = [row[i:i + 2] for i in range(0, len(row), 2)]
        return [FLIP_TABLE[b] for pair in reversed(pairs) for b in pair]
    return [FLIP_TABLE[b] for b in reversed(row)]


def derive_quad(rows, corner, masked):
    """Παράγει ne/sw/se από τις γραμμές του nw."""
    if corner in ("ne", "se"):
        rows = [hflip_row(r, masked) for r in rows]
    if corner in ("sw", "se"):
        rows = list(reversed(rows))
    return rows


# --------------------------------------------------------------------------
# 2. Sprites
# --------------------------------------------------------------------------

class Sprite:
    """pens σε πίνακα [h][w], με w ζυγό.

    masked=True  -> bytes «mask, data, mask, data...» ανά γραμμή (διαδοχικές
                    αναγνώσεις HL στον Z80)
    masked=False -> μόνο data
    """

    def __init__(self, name, pens, category, masked):
        self.name, self.pens = name, pens
        self.category, self.masked = category, masked
        self.h, self.w = len(pens), len(pens[0])
        if self.w % 2:
            raise ValueError(f"{name}: πλάτος {self.w} — πρέπει να είναι ζυγό")
        if any(len(r) != self.w for r in pens):
            raise ValueError(f"{name}: μη ορθογώνιο")

    @property
    def bw(self):
        return self.w // 2

    def rows_bytes(self):
        out = []
        for row in self.pens:
            r = []
            for x in range(0, self.w, 2):
                p0, p1 = row[x], row[x + 1]
                if self.masked:
                    r.append(mask_mode0(p0, p1))
                r.append(encode_mode0(p0, p1))
            out.append(r)
        return out

    def data(self):
        return bytes(b for row in self.rows_bytes() for b in row)

    @property
    def stride(self):
        return self.bw * (2 if self.masked else 1)


def pad_to(pens, w, h):
    """Κεντράρει ένα sprite σε μεγαλύτερο διαφανές πλαίσιο (για το Aseprite)."""
    ox, oy = (w - len(pens[0])) // 2, (h - len(pens)) // 2
    out = [[PEN_OUTSIDE] * w for _ in range(h)]
    for y, row in enumerate(pens):
        for x, p in enumerate(row):
            out[oy + y][ox + x] = p
    return out


SLOT_SIZE = geo.SLOT_W // 2 * geo.SLOT_H          # bytes ανά θέση (αδιαφανής)


def build_domes(uniform):
    """Ανά μέγεθος: 4 τεταρτημόρια θόλου και 4 τεταρτημόρια δακτυλίου."""
    domes, rings, frames = [], [], {}
    for code, d in geo.DOME_SIZES:
        fw, fh = geo.frame_size(d, uniform)
        cls = geo.classify_frame(d, fw, fh)
        dp, rp = geo.dome_pens(cls, fw, fh), geo.ring_pens(cls, fw, fh)
        frames[code] = (d, fw, fh, cls, dp, rp)
        for corner, pens in geo.quadrants(dp, fw, fh):
            domes.append(Sprite(f"dome_{code}_{corner}", pens, "θόλοι", True))
        for corner, pens in geo.quadrants(rp, fw, fh):
            rings.append(Sprite(f"ring_{code}_{corner}", pens, "δακτύλιοι", True))
    return domes, rings, frames


def build_corridors():
    c = "διάδρομοι"
    return [
        Sprite("corr_h", geo.corr_h(), c, True),
        Sprite("corr_v", geo.corr_v(), c, True),
        Sprite("corr_dr", geo.corr_diag(True), c, True),
        Sprite("corr_dl", geo.corr_diag(False), c, True),
    ]


def build_connectors():
    return [Sprite(f"conn_{name}", geo.connector(name), "σημεία σύνδεσης", True)
            for name, _, _ in geo.DIRS]


def build_machines():
    out = []
    for name, sizes, art in icons.MACHINES:
        pens = icons.parse_art(art, icons.MACHINE_W, icons.MACHINE_H,
                               what=f"machine {name}")
        out.append(Sprite(f"mach_{name}", pens, "μηχανήματα", False))
    return out


PLANT_CLASSES = ["starch", "veg", "medicine", "morale"]


def build_structures():
    """Εξωτερικά κτίσματα — ΟΧΙ μηχανές θόλου. Έχουν μάσκα και δικά τους μεγέθη."""
    out = []
    for key, _, _, _ in st.STRUCTURES:
        for name, pens in st.build(key):
            out.append(Sprite(name, pens, "εξωτερικές δομές", True))
    return out


def build_plants():
    """Τα φυτά του Bio-Dome. Ίδιο μέγεθος με τα μηχανήματα: μπαίνουν στις ίδιες
    υποδοχές, ώστε ένας θόλος-θερμοκήπιο να γεμίζει με παρτέρια αντί για μηχανές."""
    out = []
    for name, cls, top in icons.PLANTS:
        pens = icons.parse_art(top + icons.PLANT_BED, icons.PLANT_W, icons.PLANT_H,
                               what=f"plant {name}")
        out.append(Sprite(f"plant_{name}", pens, "φυτά", False))
    return out


def build_icons():
    """Ένα σετ ανά μέγεθος θόλου — το εικονίδιο κλιμακώνεται μαζί του."""
    out = []
    for code, _ in geo.DOME_SIZES:
        n = icons.ICON_SIZES[code]
        for name, per in icons.ROOM_ICONS:
            pens = icons.parse_art(per[n], n, n, what=f"icon {name}@{n}")
            out.append(Sprite(f"icon_{code}_{name}", pens, "εικονίδια δωματίων", False))
    return out


def build_corridor_slots(frames):
    """Θέσεις αποίκων πάνω στον δακτύλιο, σε δύο παραλλαγές: κενή και με άποικο.

    Κόβονται από το ΣΥΝΘΕΤΟ πλαίσιο (θόλος + δακτύλιος), ώστε η κενή παραλλαγή
    να επαναφέρει ακριβώς ό,τι υπήρχε εκεί. Έτσι ένα αδιαφανές blit αρκεί και
    για να εμφανιστεί και για να σβηστεί ένας άποικος.
    """
    fig = icons.parse_art(icons.COLONIST, icons.COLONIST_W, icons.COLONIST_H,
                          icons.COLONIST_LEGEND, "colonist")
    ox = (geo.SLOT_W - icons.COLONIST_W) // 2
    oy = (geo.SLOT_H - icons.COLONIST_H) // 2
    out = []
    for code, d in geo.DOME_SIZES:
        _, fw, fh, cls, dp, rp = frames[code]
        full = [[dp[y][x] or rp[y][x] for x in range(fw)] for y in range(fh)]
        for k, x, y in geo.corridor_slots(d, fw, fh):
            empty = [row[x:x + geo.SLOT_W] for row in full[y:y + geo.SLOT_H]]
            out.append(Sprite(f"slot_{code}_{k}_e", empty, "θέσεις διαδρόμου", False))
            person = [r[:] for r in empty]
            for j, frow in enumerate(fig):
                for i, pen in enumerate(frow):
                    if pen is not None:
                        person[oy + j][ox + i] = pen
            out.append(Sprite(f"slot_{code}_{k}_p", person, "θέσεις διαδρόμου", False))
    return out


# --------------------------------------------------------------------------
# 3. Επαλήθευση
# --------------------------------------------------------------------------

class CheckFailed(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise CheckFailed(msg)


def verify(frames, domes, rings, corr, conns, icon_sprites, slots, machines,
           plants, structs, uniform):
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

    allspr = (domes + rings + corr + conns + icon_sprites + slots + machines
              + plants + structs)

    # 3. διαστάσεις
    for s in allspr:
        check(s.w % 2 == 0, f"{s.name}: μονό πλάτος {s.w}")
        check(len(s.data()) == s.stride * s.h,
              f"{s.name}: {len(s.data())} bytes αντί για {s.stride * s.h}")

    # 4. η μάσκα συμφωνεί με τα δεδομένα: όπου διαφανές, data=0 και mask=1
    for s in allspr:
        if not s.masked:
            continue
        for y, row in enumerate(s.pens):
            rb = s.rows_bytes()[y]
            for i in range(s.bw):
                m, dbyte = rb[2 * i], rb[2 * i + 1]
                p0, p1 = row[2 * i], row[2 * i + 1]
                check(m & dbyte == 0, f"{s.name}: mask και data επικαλύπτονται στη γραμμή {y}")
                check(m == mask_mode0(p0, p1), f"{s.name}: λάθος μάσκα στη γραμμή {y}")

    by = {s.name: s for s in domes + rings}

    # 5. τα τεταρτημόρια συναρμολογημένα == το πλήρες πλαίσιο
    for code, (d, fw, fh, cls, dp, rp) in frames.items():
        for kind, full in (("dome", dp), ("ring", rp)):
            qw, qh = fw // 2, fh // 2
            for corner, ox, oy in (("nw", 0, 0), ("ne", qw, 0), ("sw", 0, qh), ("se", qw, qh)):
                q = by[f"{kind}_{code}_{corner}"]
                for y in range(qh):
                    for x in range(qw):
                        check(q.pens[y][x] == full[oy + y][ox + x],
                              f"{kind}_{code}_{corner}: διαφορά στο pixel ({x},{y})")

    # 6. συμμετρία τεταρτημορίων
    for code, _ in geo.DOME_SIZES:
        for kind in ("dome", "ring"):
            nw = by[f"{kind}_{code}_nw"].pens
            check(by[f"{kind}_{code}_ne"].pens == [list(reversed(r)) for r in nw],
                  f"{kind}_{code}_ne != οριζόντιο καθρέφτισμα του nw")
            check(by[f"{kind}_{code}_sw"].pens == list(reversed([list(r) for r in nw])),
                  f"{kind}_{code}_sw != κάθετο καθρέφτισμα του nw")

    # 6β. τα ne/sw/se παράγονται από το nw με το flip_mode0 σε επίπεδο BYTES —
    #     ακριβώς ό,τι θα κάνει ο Z80 όταν αποθηκεύεται μόνο το nw
    for code, _ in geo.DOME_SIZES:
        for kind in ("dome", "ring"):
            rows = by[f"{kind}_{code}_nw"].rows_bytes()
            for corner in ("ne", "sw", "se"):
                got = by[f"{kind}_{code}_{corner}"].rows_bytes()
                check(got == derive_quad(rows, corner, True),
                      f"{kind}_{code}_{corner}: δεν παράγεται από το nw με το flip_mode0")

    # 7. θόλος και δακτύλιος δεν επικαλύπτονται και μαζί δίνουν το πλήρες σχήμα
    for code, (d, fw, fh, cls, dp, rp) in frames.items():
        for y in range(fh):
            for x in range(fw):
                a, b2 = dp[y][x] != PEN_OUTSIDE, rp[y][x] != PEN_OUTSIDE
                check(not (a and b2), f"{code}: θόλος και δακτύλιος επικαλύπτονται στο ({x},{y})")
                check((a or b2) == (cls[y][x] != geo.OUTSIDE),
                      f"{code}: κενό ανάμεσα σε θόλο και δακτύλιο στο ({x},{y})")

    # 8. εικονίδιο, μηχανήματα και επικάλυμμα: μέσα στον θόλο, όχι σε άκρη,
    #    χωρίς επικαλύψεις μεταξύ τους
    for code, (d, fw, fh, cls, dp, rp) in frames.items():
        taken = {}
        for what, px, py, w, h in geo.interior(code, d, fw, fh):
            check(px % 2 == 0, f"{code}/{what}: μονό x = {px}")
            for y in range(py, py + h):
                for x in range(px, px + w):
                    check(0 <= x < fw and 0 <= y < fh,
                          f"{code}/{what}: pixel ({x},{y}) έξω από το πλαίσιο")
                    check(dp[y][x] == PEN_DOME_FLOOR,
                          f"{code}/{what}: pixel ({x},{y}) δεν είναι δάπεδο θόλου")
                    check((x, y) not in taken,
                          f"{code}/{what}: επικάλυψη με {taken.get((x, y))} στο ({x},{y})")
                    taken[(x, y)] = what

    # 8β. κάθε μέγεθος έχει τόσες θέσεις όσες λέει ο κανόνας, και κάθε
    #     μηχάνημα επιτρέπεται σε τουλάχιστον ένα μέγεθος
    want = {"s": 1, "m": 4, "l": 8}
    for code, n in want.items():
        d, fw, fh, *_ = frames[code]
        got = sum(1 for nm, *_ in geo.interior(code, d, fw, fh) if nm.startswith("machine"))
        check(got == n, f"{code}: {got} θέσεις μηχανημάτων αντί για {n}")
    for name, sizes, _ in icons.MACHINES:
        check(sizes and all(c in "sml" for c in sizes),
              f"μηχάνημα {name}: άκυρα μεγέθη {sizes!r}")

    # 8γ. τα φυτά χωράνε στις ίδιες υποδοχές με τα μηχανήματα
    for sp in plants:
        check((sp.w, sp.h) == (geo.MACHINE_W, geo.MACHINE_H),
              f"φυτό {sp.name}: {sp.w}x{sp.h} αντί για {geo.MACHINE_W}x{geo.MACHINE_H}")
    for name, cls, _ in icons.PLANTS:
        check(cls in PLANT_CLASSES, f"φυτό {name}: άγνωστη κατηγορία {cls!r}")

    # 9β. οι θέσεις αποίκων πέφτουν πάνω στον δακτύλιο και δεν πατάνε πόρτα
    for code, (d, fw, fh, cls, dp, rp) in frames.items():
        doors = set()
        for name, x, y in geo.conn_points(d, fw, fh):
            doors |= {(a, b) for b in range(y, y + geo.CONN_H)
                      for a in range(x, x + geo.CONN_W)}
        for k, x, y in geo.corridor_slots(d, fw, fh):
            check(x % 2 == 0, f"{code}/θέση {k}: μονό x = {x}")
            cxp, cyp = x + geo.SLOT_W // 2, y + geo.SLOT_H // 2
            check(cls[cyp][cxp] == geo.CORRIDOR,
                  f"{code}/θέση {k}: το κέντρο ({cxp},{cyp}) δεν είναι στον δακτύλιο")
            box = {(a, b) for b in range(y, y + geo.SLOT_H)
                   for a in range(x, x + geo.SLOT_W)}
            check(not (box & doors), f"{code}/θέση {k}: πέφτει πάνω σε σημείο σύνδεσης")

    # 9. τα σημεία σύνδεσης πέφτουν πάνω στον δακτύλιο
    for code, (d, fw, fh, cls, dp, rp) in frames.items():
        for name, x, y in geo.conn_points(d, fw, fh):
            check(x % 2 == 0, f"{code}/conn_{name}: μονό x = {x}")
            cxp, cyp = x + geo.CONN_W // 2, y + geo.CONN_H // 2
            check(cls[cyp][cxp] == geo.CORRIDOR,
                  f"{code}/conn_{name}: το κέντρο ({cxp},{cyp}) δεν είναι πάνω στον δακτύλιο")


# --------------------------------------------------------------------------
# 4. Έξοδος
# --------------------------------------------------------------------------

class Blob:
    def __init__(self):
        self.items = []
        self.marks = {}

    def add(self, label, data, sprite=None, category="άλλο"):
        self.marks[label] = self.size()
        self.items.append((label, bytes(data), sprite, category))

    def size(self):
        return sum(len(i[1]) for i in self.items)

    def data(self):
        return b"".join(i[1] for i in self.items)


def build_blob(frames, domes, rings, corr, conns, icon_sprites, slots, machines,
               plants, structs, quads):
    """quads="all": και τα 4 τεταρτημόρια. quads="nw": μόνο το nw — τα υπόλοιπα
    τρία τα παράγει ο Z80 με το flip_mode0 (το ένα τέταρτο της μνήμης)."""
    keep = (lambda n: True) if quads == "all" else (lambda n: n.endswith("_nw"))
    blob = Blob()
    for code, _ in geo.DOME_SIZES:
        blob.add(f"domes_{code}", b"", None, "—")
        for s in domes:
            if s.name.startswith(f"dome_{code}_") and keep(s.name):
                blob.add(s.name, s.data(), s, s.category)
    for code, _ in geo.DOME_SIZES:
        blob.add(f"rings_{code}", b"", None, "—")
        for s in rings:
            if s.name.startswith(f"ring_{code}_") and keep(s.name):
                blob.add(s.name, s.data(), s, s.category)

    blob.add("corridors", b"", None, "—")
    for s in corr:
        blob.add(s.name, s.data(), s, s.category)
    blob.add("connectors", b"", None, "—")
    for s in conns:
        blob.add(s.name, s.data(), s, s.category)

    # πίνακας σημείων σύνδεσης: ανά μέγεθος, 8 κατευθύνσεις x (x σε bytes, y)
    pts = bytearray()
    for code, _ in geo.DOME_SIZES:
        d, fw, fh, *_ = frames[code]
        for name, x, y in geo.conn_points(d, fw, fh):
            pts += bytes([x // 2, y])
    blob.add("conn_points", pts, None, "πίνακας συνδέσεων")

    for code, _ in geo.DOME_SIZES:
        blob.add(f"room_icons_{code}", b"", None, "—")
        for s in icon_sprites:
            if s.name.startswith(f"icon_{code}_"):
                blob.add(s.name, s.data(), s, s.category)
    blob.add("corr_slot_gfx", b"", None, "—")
    for s in slots:
        blob.add(s.name, s.data(), s, s.category)

    # πού πέφτει κάθε θέση αποίκου πάνω στον δακτύλιο
    pts = bytearray()
    for code, _ in geo.DOME_SIZES:
        d, fw, fh, *_ = frames[code]
        for k, x, y in geo.corridor_slots(d, fw, fh):
            pts += bytes([x // 2, y])
    blob.add("corr_slots", pts, None, "πίνακες δωματίου")
    blob.add("corr_fill", bytes(geo.SLOT_FILL), None, "πίνακες δωματίου")

    blob.add("machines", b"", None, "—")
    for sp in machines:
        blob.add(sp.name, sp.data(), sp, sp.category)

    # πόσα μηχανήματα χωράει κάθε μέγεθος
    blob.add("plants", b"", None, "—")
    for sp in plants:
        blob.add(sp.name, sp.data(), sp, sp.category)
    blob.add("plant_class", bytes(PLANT_CLASSES.index(c) for _, c, _ in icons.PLANTS),
             None, "πίνακες δωματίου")

    blob.add("structures", b"", None, "—")
    for sp in structs:
        blob.add(sp.name, sp.data(), sp, sp.category)

    # διαστάσεις κάθε παραλλαγής: 4 θέσεις ανά δομή, (w bytes, h) — 0,0 = δεν υπάρχει
    dims = bytearray()
    for _, _, sizes, _ in st.STRUCTURES:
        for i in range(4):
            dims += bytes([sizes[i][1] // 2, sizes[i][2]]) if i < len(sizes) else b"\x00\x00"
    blob.add("struct_dims", dims, None, "πίνακες δομών")

    blob.add("machine_count", bytes(geo.MACHINE_COUNT[c] for c, _ in geo.DOME_SIZES),
             None, "πίνακες δωματίου")

    # θέσεις μηχανημάτων: γεμισμένες σε MAX_MACHINES ανά μέγεθος ώστε ο δείκτης
    # να είναι machine_slots + size*MAX_MACHINES*2 + slot*2
    slots = bytearray()
    for code, _ in geo.DOME_SIZES:
        d, fw, fh, *_ = frames[code]
        got = [(x, y) for what, x, y, w, h in geo.interior(code, d, fw, fh)
               if what.startswith("machine")]
        for i in range(geo.MAX_MACHINES):
            slots += bytes([got[i][0] // 2, got[i][1]]) if i < len(got) else b"\xff\xff"
    blob.add("machine_slots", slots, None, "πίνακες δωματίου")

    # ποια μεγέθη δέχονται ποιο μηχάνημα (bit0=s, bit1=m, bit2=l)
    rules = bytearray()
    for name, sizes, _ in icons.MACHINES:
        rules.append(sum(1 << i for i, c in enumerate("sml") if c in sizes))
    blob.add("machine_rules", rules, None, "πίνακες δωματίου")

    # θέσεις εικονιδίου και επικαλύμματος ανά μέγεθος (προσημασμένα bytes)
    ofs = bytearray()
    for code, _ in geo.DOME_SIZES:
        d, fw, fh, *_ = frames[code]
        ix, iy = next((x, y) for n, x, y, w, h in geo.interior(code, d, fw, fh) if n == "icon")
        ofs += bytes([((ix - fw // 2) // 2) & 0xFF, (iy - fh // 2) & 0xFF])
    blob.add("interior_ofs", ofs, None, "πίνακες δωματίου")

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
; Δεδομένα γραμμικά (γραμμή-γραμμή), ΟΧΙ στη διάταξη της μνήμης οθόνης.
;
; Θόλοι, δακτύλιοι, διάδρομοι και σημεία σύνδεσης έχουν ΜΑΣΚΑ, σε μορφή
; «mask, data, mask, data...» ανά γραμμή:
;       ld a,(hl) : inc hl : and (de) : ld b,a
;       ld a,(hl) : inc hl : or b     : ld (de),a : inc de
; Τα εικονίδια και τα επικαλύμματα πληρότητας είναι αδιαφανή (μόνο data).
;
; Φόρτωσε το μπλοκ σε διεύθυνση πολλαπλάσιο του 256 (το flip_mode0 θέλει σελίδα).
"""


QUADS_NW_NOTE = """\
; ΠΡΟΣΟΧΗ: αποθηκεύεται ΜΟΝΟ το τεταρτημόριο nw κάθε θόλου και δακτυλίου.
; Τα άλλα τρία παράγονται τη στιγμή του blit με το flip_mode0:
;
;   ne = οριζόντιο καθρέφτισμα -> αντίστροφη σειρά ΖΕΥΓΩΝ (mask,data) σε κάθε
;        γραμμή, με κάθε byte να περνά από το flip_mode0
;   sw = κάθετο καθρέφτισμα    -> οι γραμμές με αντίστροφη σειρά, bytes ως έχουν
;   se = και τα δύο μαζί
;
; Το ζεύγος (mask, data) μένει ΕΝΙΑΙΟ στον οριζόντιο καθρεφτισμό — αντιστρέφονται
; τα ζεύγη, όχι τα μεμονωμένα bytes.
"""


def emit_asm(blob, frames, uniform, quads):
    L = [ASM_HEADER]
    if quads == "nw":
        L.append(QUADS_NW_NOTE)
    for code, d in geo.DOME_SIZES:
        _, fw, fh, *_ = frames[code]
        u = code.upper()
        L.append("DOME_%s_D    equ %-4d      ; οπτική διάμετρος" % (u, d))
        L.append("DOME_%s_W    equ %-4d      ; bytes ανά γραμμή τεταρτημορίου" % (u, fw // 4))
        L.append("DOME_%s_H    equ %-4d      ; γραμμές τεταρτημορίου" % (u, fh // 2))
        L.append("DOME_%s_SZ   equ %-4d      ; bytes ανά τεταρτημόριο (mask+data)"
                 % (u, fw // 4 * 2 * (fh // 2)))
    L.append("")
    for code, _ in geo.DOME_SIZES:
        n = icons.ICON_SIZES[code]
        u = code.upper()
        L.append("ICON_%s_W    equ %-4d      ; bytes· room_icons_%s + type*ICON_%s_SZ"
                 % (u, n // 2, code, u))
        L.append("ICON_%s_H    equ %-4d" % (u, n))
        L.append("ICON_%s_SZ   equ %-4d" % (u, n // 2 * n))
    L.append("SLOT_W      equ %d           ; θέση αποίκου στον διάδρομο" % (geo.SLOT_W // 2))
    L.append("SLOT_H      equ %d" % geo.SLOT_H)
    L.append("SLOT_SIZE   equ %d          ; bytes ανά παραλλαγή" % SLOT_SIZE)
    L.append("SLOT_STRIDE equ %d          ; κενή + με άποικο" % (2 * SLOT_SIZE))
    L.append("SLOT_BANK   equ %d         ; bytes ανά μέγεθος θόλου"
             % (geo.CORR_SLOTS * 2 * SLOT_SIZE))
    L.append("CORR_SLOTS  equ %d" % geo.CORR_SLOTS)
    L.append("            ; corr_slot_gfx + size*SLOT_BANK + slot*SLOT_STRIDE")
    L.append("            ; + (0 = κενή, SLOT_SIZE = με άποικο)")
    L.append("")
    L.append("CORR_H_W    equ 4")
    L.append("CORR_H_H    equ 8")
    L.append("CORR_V_W    equ 2")
    L.append("CORR_V_H    equ 16")
    L.append("CORR_D_W    equ %d           ; διαγώνιο tile" % (geo.DIAG_W // 2))
    L.append("CORR_D_H    equ %d" % geo.DIAG_H)
    L.append("CORR_D_SX   equ %d           ; βήμα τοποθέτησης σε bytes" % (geo.DIAG_STEP_X // 2))
    L.append("CORR_D_SY   equ %d" % geo.DIAG_STEP_Y)
    L.append("MACH_W      equ %d" % (geo.MACHINE_W // 2))
    L.append("MACH_H      equ %d" % geo.MACHINE_H)
    L.append("MACH_SIZE   equ %d          ; machines + type*MACH_SIZE"
             % (geo.MACHINE_W // 2 * geo.MACHINE_H))
    L.append("MACH_TYPES  equ %d           ; %s"
             % (len(icons.MACHINES), ", ".join(n for n, _, _ in icons.MACHINES)))
    L.append("MACH_SLOTS  equ %d           ; θέσεις ανά μέγεθος στον πίνακα" % geo.MAX_MACHINES)
    L.append("")
    L.append("PLANT_SIZE  equ %d          ; ίδιες διαστάσεις με τα μηχανήματα"
             % (icons.PLANT_W // 2 * icons.PLANT_H))
    L.append("PLANT_TYPES equ %d          ; plants + type*PLANT_SIZE" % len(icons.PLANTS))
    L.append("")
    L.append("; Εξωτερικές δομές: αυτοτελή κτίσματα στο έδαφος, ΟΧΙ μηχανές θόλου.")
    L.append("; Κάθε παραλλαγή έχει δική της ετικέτα· διαστάσεις στο struct_dims.")
    L.append("STRUCT_KINDS equ %d          ; %s" % (len(st.STRUCTURES),
             ", ".join(k for k, _, _, _ in st.STRUCTURES)))
    for i, (n, c, _) in enumerate(icons.PLANTS):
        L.append("            ; %2d %-10s %s" % (i, n, c))
    L.append("")
    L.append("CONN_W      equ %d" % (geo.CONN_W // 2))
    L.append("CONN_H      equ %d" % geo.CONN_H)
    L.append("CONN_DIRS   equ %d           ; n,ne,e,se,s,sw,w,nw" % len(geo.DIRS))
    L.append("")

    for label, data, sprite, category in blob.items:
        if sprite is None:
            if label == "flip_mode0":
                L += ["", "; --- flip_mode0[b] = b με ανταλλαγμένα pixels ---",
                      "align 256", "flip_mode0:"]
                for i in range(0, 256, 16):
                    L.append("    db " + ",".join("#%02X" % b for b in data[i:i + 16]))
                continue
            if label == "sprites_pad":
                L += ["", "; --- %d bytes γέμισμα για τη σελίδα του flip_mode0 ---" % len(data),
                      "sprites_pad:", "    defs %d,#00" % len(data)]
                continue
            if label == "palette_fw":
                L += ["", "; --- 16 firmware colour numbers, pen 0..15 ---", "palette_fw:",
                      "    db " + ",".join("#%02X" % b for b in data)]
                for pen, name, fw_, rgb, ch, use in PALETTE:
                    L.append("    ; pen %2d  FW %2d  %-13s %s" % (pen, fw_, name, use))
                continue
            if label == "struct_dims":
                L += ["", "; --- διαστάσεις εξωτερικών δομών, 4 θέσεις ανά δομή ---",
                      "; struct_dims + kind*8 + size*2 -> (w bytes, h)· 0,0 = δεν υπάρχει",
                      "struct_dims:"]
                i = 0
                for key, _, sizes, doc in st.STRUCTURES:
                    vals = ",".join("%3d,%3d" % (data[i + 2 * k], data[i + 2 * k + 1])
                                    for k in range(4))
                    L.append("    db %s   ; %s — %s" % (vals, key, doc))
                    i += 8
                continue
            if label == "plant_class":
                L += ["", "; --- κατηγορία κάθε φυτού: %s ---"
                      % ", ".join("%d=%s" % (i, c) for i, c in enumerate(PLANT_CLASSES)),
                      "plant_class:",
                      "    db " + ",".join(str(b) for b in data),
                      "    ; " + ", ".join(n for n, _, _ in icons.PLANTS)]
                continue
            if label in ("machine_count", "machine_rules"):
                names = ([c for c, _ in geo.DOME_SIZES] if label == "machine_count"
                         else [n for n, _, _ in icons.MACHINES])
                L += ["", "%s:" % label,
                      "    db " + ",".join(str(b) for b in data),
                      "    ; " + ", ".join(names)]
                continue
            if label == "machine_slots":
                L += ["", "; --- θέσεις μηχανημάτων, %d ανά μέγεθος (255 = κενή) ---"
                      % geo.MAX_MACHINES,
                      "; machine_slots + size*MACH_SLOTS*2 + slot*2 -> (x bytes, y)",
                      "machine_slots:"]
                i = 0
                for code, _ in geo.DOME_SIZES:
                    for k in range(geo.MAX_MACHINES):
                        L.append("    db %3d,%3d   ; %s θέση %d"
                                 % (data[i], data[i + 1], code, k))
                        i += 2
                continue
            if label == "interior_ofs":
                L += ["", "; --- θέσεις εικονιδίου/πληρότητας από το ΚΕΝΤΡΟ του θόλου ---",
                      "; interior_ofs + size*2 -> (icon dx bytes, icon dy) από το κέντρο",
                      "interior_ofs:"]
                for i, (code, _) in enumerate(geo.DOME_SIZES):
                    L.append("    db %3d,%3d   ; %s" % (data[2 * i], data[2 * i + 1], code))
                continue
            if label == "corr_slots":
                L += ["", "; --- θέσεις αποίκων πάνω στον δακτύλιο ---",
                      "; corr_slots + size*CORR_SLOTS*2 + slot*2 -> (x bytes, y)",
                      "corr_slots:"]
                i = 0
                for code, _ in geo.DOME_SIZES:
                    for k in range(geo.CORR_SLOTS):
                        L.append("    db %3d,%3d   ; %s θέση %d"
                                 % (data[i], data[i + 1], code, k))
                        i += 2
                continue
            if label == "corr_fill":
                L += ["", "; --- σειρά γεμίσματος θέσεων (σκορπισμένη) ---", "corr_fill:",
                      "    db " + ",".join(str(b) for b in data)]
                continue
            if label == "conn_points":
                L += ["", "; --- σημεία σύνδεσης: ανά μέγεθος, 8 κατευθύνσεις x (x bytes, y) ---",
                      "; conn_points + size*CONN_DIRS*2 + dir*2", "conn_points:"]
                i = 0
                for code, _ in geo.DOME_SIZES:
                    for name, _, _ in geo.DIRS:
                        L.append("    db %3d,%3d   ; %s %s" % (data[i], data[i + 1], code, name))
                        i += 2
                continue
            L += ["", "%s:" % label]
            continue

        L += ["", "; %s — %d x %d pixels, %s, %d bytes"
              % (label, sprite.w, sprite.h,
                 "mask+data" if sprite.masked else "αδιαφανές", len(data)),
              "%s:" % label]
        for row_pens, row_bytes in zip(sprite.pens, sprite.rows_bytes()):
            L.append("    db " + ",".join("#%02X" % b for b in row_bytes)
                     + "   ; " + pens_to_ascii(row_pens))
    L.append("")
    return "\n".join(L)


ASM_BYTE_RE = re.compile(r"^\s*db\s+(.*)$", re.I)
ASM_DEFS_RE = re.compile(r"^\s*defs\s+(\d+)\s*,\s*#([0-9A-Fa-f]{1,2})\s*$", re.I)


def parse_asm_bytes(text):
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
                    # όπως η RASM: «#» = δεκαεξαδικό, γυμνός αριθμός = δεκαδικό
                    out.append(int(tok[1:], 16) if tok.startswith("#") else int(tok, 10))
    return bytes(out)


def emit_map(blob):
    L = ["# sprite                offset  bytes  διαστάσεις     μορφή      κατηγορία",
         "# " + "-" * 76]
    for label, data, sprite, category in blob.items:
        if not data and sprite is None:
            L.append("# %-21s #%04X      -  %-14s %-10s %s"
                     % (label, blob.marks[label], "", "", "(ομάδα)"))
            continue
        dims = "%dx%d px" % (sprite.w, sprite.h) if sprite else ""
        fmt = ("mask+data" if sprite.masked else "αδιαφανές") if sprite else ""
        L.append("  %-21s #%04X %6d  %-14s %-10s %s"
                 % (label, blob.marks[label], len(data), dims, fmt, category))
    L.append("")
    L.append("  %-21s       %6d" % ("ΣΥΝΟΛΟ", blob.size()))
    return "\n".join(L) + "\n"


def emit_aseprite_dump(groups):
    """Text dump που διαβάζει το make_aseprite.lua (μία γραμμή ανά frame)."""
    L = ["pal " + " ".join("%02X%02X%02X" % c for c in RGB)]
    for gname, w, h, members in groups:
        L.append("group %s %d %d" % (gname, w, h))
        for name, pens in members:
            flat = "".join("%X" % p for row in pens for p in row)
            L.append("frame %s %s" % (name, flat))
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# 5. Προεπισκοπήσεις PNG
# --------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageFont

CHECKER = ((40, 40, 48), (28, 28, 34))      # φόντο για τα διαφανή pixels


def sprite_from_bytes(data, bw, h, masked):
    """Αποκωδικοποιεί bytes σε pens — επαληθεύει και την κωδικοποίηση."""
    stride = bw * (2 if masked else 1)
    pens = []
    for y in range(h):
        row, line = [], data[y * stride:(y + 1) * stride]
        for i in range(bw):
            b = line[2 * i + 1] if masked else line[i]
            m = line[2 * i] if masked else 0
            p0, p1 = decode_mode0(b)
            mp0, mp1 = decode_mode0(m)
            row.append(PEN_OUTSIDE if mp0 == 15 else p0)
            row.append(PEN_OUTSIDE if mp1 == 15 else p1)
        pens.append(row)
    return pens


def render(pens, scale=4, grid=False):
    w, h = len(pens[0]), len(pens)
    pw, ph = 2 * scale, 1 * scale
    img = Image.new("RGB", (w * pw, h * ph))
    d = ImageDraw.Draw(img)
    for y in range(h):
        for x in range(w):
            p = pens[y][x]
            col = CHECKER[(x + y) & 1] if p == PEN_OUTSIDE else RGB[p]
            d.rectangle([x * pw, y * ph, (x + 1) * pw - 1, (y + 1) * ph - 1], fill=col)
    if grid and scale >= 3:
        for x in range(1, w):
            d.line([(x * pw, 0), (x * pw, h * ph)], fill=(60, 60, 70))
        for y in range(1, h):
            d.line([(0, y * ph), (w * pw, y * ph)], fill=(60, 60, 70))
    return img


def paste_pens(dst, src, ox, oy):
    """Σύνθεση με μάσκα: τα διαφανή pixels δεν γράφονται."""
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p != PEN_OUTSIDE and 0 <= oy + y < len(dst) and 0 <= ox + x < len(dst[0]):
                dst[oy + y][ox + x] = p


def composite_pens(blob, frames, code, icon_type, people, with_ring=True):
    """Πλήρης θόλος, συντεθειμένος ΑΠΟ ΤΑ BYTES των sprites."""
    data = blob.data()
    d, fw, fh, cls, dp, rp = frames[code]
    out = [[PEN_OUTSIDE] * fw for _ in range(fh)]
    qw, qh = fw // 2, fh // 2

    def blit(label, w, h, masked, ox, oy):
        off = blob.marks[label]
        n = (w // 2) * (2 if masked else 1) * h
        paste_pens(out, sprite_from_bytes(data[off:off + n], w // 2, h, masked), ox, oy)

    def quad(kind, corner):
        """Τα pens ενός τεταρτημορίου: από το blob, ή παραγμένα από το nw.

        Όταν τρέχει με --quads nw, αυτό εδώ κάνει ακριβώς ό,τι θα κάνει ο Z80,
        οπότε η προεπισκόπηση επαληθεύει και την παραγωγή.
        """
        stride, label = qw // 2 * 2, f"{kind}_{code}_{corner}"
        if label not in blob.marks:
            label, derive = f"{kind}_{code}_nw", corner
        else:
            derive = None
        off = blob.marks[label]
        rows = [list(data[off + y * stride:off + (y + 1) * stride]) for y in range(qh)]
        if derive:
            rows = derive_quad(rows, derive, True)
        return sprite_from_bytes(bytes(b for r in rows for b in r), qw // 2, qh, True)

    order = (["ring"] if with_ring else []) + ["dome"]
    for kind in order:
        for corner, ox, oy in (("nw", 0, 0), ("ne", qw, 0), ("sw", 0, qh), ("se", qw, qh)):
            paste_pens(out, quad(kind, corner), ox, oy)

    greenhouse = icons.ROOM_ICONS[icon_type][0] == "greenhouse"
    allowed = ([(n, "") for n, _, _ in icons.PLANTS] if greenhouse
               else [(n, sz) for n, sz, _ in icons.MACHINES if code in sz])
    prefix = "plant_" if greenhouse else "mach_"
    for what, x, y, w, h in geo.interior(code, d, fw, fh):
        if what == "icon":
            blit(f"icon_{code}_{icons.ROOM_ICONS[icon_type][0]}", w, h, False, x, y)
        else:
            k = int(what[len("machine"):])
            blit(f"{prefix}{allowed[k % len(allowed)][0]}", w, h, False, x, y)

    if with_ring:
        for name, x, y in geo.conn_points(d, fw, fh):
            blit(f"conn_{name}", geo.CONN_W, geo.CONN_H, True, x, y)
        # άποικοι: γεμίζουν τις θέσεις του δακτυλίου με τη σειρά του corr_fill
        chosen = set(geo.SLOT_FILL[:people])
        for k, x, y in geo.corridor_slots(d, fw, fh):
            if k in chosen:
                blit(f"slot_{code}_{k}_p", geo.SLOT_W, geo.SLOT_H, False, x, y)
    return out


def font(size=12):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def make_sheet(entries, path, scale=2):
    F = font()
    PAD, LABEL_H, HEAD_H, MARGIN, LIMIT = 12, 16, 24, 14, 1400
    groups = []
    for category, name, pens in entries:
        if not groups or groups[-1][0] != category:
            groups.append((category, []))
        groups[-1][1].append((name, pens))

    tiles = {n: render(p, scale, grid=True) for _, g in groups for n, p in g}
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cell = {n: max(im.width, int(probe.textlength(n, font=F)) + 4) for n, im in tiles.items()}

    layout, total_h, sheet_w = [], MARGIN, 0
    for category, members in groups:
        total_h += HEAD_H
        rows, cur, cur_w = [], [], 0
        for name, _ in members:
            w = cell[name] + PAD
            if cur and cur_w + w > LIMIT:
                rows.append(cur)
                cur, cur_w = [], 0
            cur.append(name)
            cur_w += w
        if cur:
            rows.append(cur)
        for r in rows:
            total_h += max(tiles[n].height for n in r) + LABEL_H + PAD
            sheet_w = max(sheet_w, sum(cell[n] + PAD for n in r))
        layout.append((category, rows))
        total_h += PAD

    img = Image.new("RGB", (sheet_w + 2 * MARGIN, total_h + MARGIN), (24, 24, 32))
    d = ImageDraw.Draw(img)
    y = MARGIN
    for category, rows in layout:
        d.text((MARGIN, y), category, fill=(255, 210, 120), font=F)
        y += HEAD_H
        for r in rows:
            x, rh = MARGIN, max(tiles[n].height for n in r)
            for n in r:
                im = tiles[n]
                img.paste(im, (x, y))
                d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=(90, 90, 100))
                d.text((x, y + rh + 3), n, fill=(200, 200, 210), font=F)
                x += cell[n] + PAD
            y += rh + LABEL_H + PAD
        y += PAD
    img.save(path)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quads", choices=("all", "nw"), default="all",
                    help="all: και τα 4 τεταρτημόρια (γρήγορο). "
                         "nw: μόνο το nw, τα άλλα 3 παράγονται με το flip_mode0")
    ap.add_argument("--uniform-quads", action="store_true",
                    help="όλα τα μεγέθη σε τεταρτημόριο 32x64 (αλλιώς σφιχτό πλαίσιο ανά μέγεθος)")
    ap.add_argument("--out", default=os.path.join(root, "build", "sprites"))
    args = ap.parse_args()

    domes, rings, frames = build_domes(args.uniform_quads)
    corr, conns = build_corridors(), build_connectors()
    icon_sprites = build_icons()
    machines = build_machines()
    slots = build_corridor_slots(frames)
    plants = build_plants()
    structs = build_structures()

    try:
        verify(frames, domes, rings, corr, conns, icon_sprites, slots, machines,
               plants, structs, args.uniform_quads)
    except CheckFailed as e:
        print("ΑΠΟΤΥΧΙΑ ΕΠΑΛΗΘΕΥΣΗΣ: %s" % e, file=sys.stderr)
        return 1

    blob = build_blob(frames, domes, rings, corr, conns, icon_sprites, slots,
                      machines, plants, structs, args.quads)
    asm = emit_asm(blob, frames, args.uniform_quads, args.quads)
    binary = blob.data()

    from_asm = parse_asm_bytes(asm)
    if from_asm != binary:
        print("ΑΠΟΤΥΧΙΑ: sprites.asm (%d) != sprites.bin (%d)" % (len(from_asm), len(binary)),
              file=sys.stderr)
        return 1

    prev = os.path.join(args.out, "preview")
    os.makedirs(prev, exist_ok=True)
    for name, text in (("sprites.asm", asm), ("sprites_map.txt", emit_map(blob))):
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(text)
    with open(os.path.join(args.out, "sprites.bin"), "wb") as f:
        f.write(binary)

    # PNG ανά sprite + φύλλο, αποκωδικοποιημένα από τα bytes
    entries = []
    for label, data, sprite, category in blob.items:
        if sprite is None:
            continue
        pens = sprite_from_bytes(data, sprite.bw, sprite.h, sprite.masked)
        render(pens).save(os.path.join(prev, label + ".png"))
        entries.append((category, label, pens))
    make_sheet(entries, os.path.join(prev, "sheet.png"))

    for code, _ in geo.DOME_SIZES:
        render(composite_pens(blob, frames, code, 5, 5)).save(
            os.path.join(prev, "composite_%s.png" % code))
    render(composite_pens(blob, frames, "l", 5, 5)).save(os.path.join(prev, "composite.png"))

    # dump για το Aseprite: ΠΑΝΤΑ και τα 4 τεταρτημόρια, ακόμη και με --quads nw.
    # Τα .aseprite είναι το εικαστικό· τι αποθηκεύεται τελικά το λέει το sprites_map.txt.
    max_q = max((f[1] // 2, f[2] // 2) for f in frames.values())
    groups = [
        ("domes", max_q[0], max_q[1],
         [(s.name, pad_to(s.pens, *max_q)) for s in domes]),
        ("rings", max_q[0], max_q[1],
         [(s.name, pad_to(s.pens, *max_q)) for s in rings]),
        ("corridors", geo.DIAG_W, geo.DIAG_H,
         [(s.name, pad_to(s.pens, geo.DIAG_W, geo.DIAG_H)) for s in corr + conns]),
        *[("icons_%s" % c, icons.ICON_SIZES[c], icons.ICON_SIZES[c],
           [(s.name, s.pens) for s in icon_sprites if s.name.startswith("icon_%s_" % c)])
          for c, _ in geo.DOME_SIZES],
        ("slots", geo.SLOT_W, geo.SLOT_H, [(s.name, s.pens) for s in slots]),
        ("machines", geo.MACHINE_W, geo.MACHINE_H,
         [(s.name, s.pens) for s in machines]),
        ("plants", icons.PLANT_W, icons.PLANT_H, [(s.name, s.pens) for s in plants]),
        # όλες οι παραλλαγές στον ίδιο καμβά, μόνο για το Aseprite
        ("structures", st.SIZES_4[-1][1], st.SIZES_4[-1][2],
         [(s.name, pad_to(s.pens, st.SIZES_4[-1][1], st.SIZES_4[-1][2])) for s in structs]),
    ]
    with open(os.path.join(args.out, "aseprite_dump.txt"), "w", encoding="utf-8") as f:
        f.write(emit_aseprite_dump(groups))

    cats = {}
    for label, data, sprite, category in blob.items:
        if not data:
            continue
        n, tot = cats.get(category, (0, 0))
        cats[category] = (n + 1, tot + len(data))
    print("Γράφτηκαν στο %s" % args.out)
    print("Τεταρτημόρια: " + ", ".join(
        "%s %dx%d" % (c, frames[c][1] // 2, frames[c][2] // 2) for c, _ in geo.DOME_SIZES))
    print()
    print("  %-26s %6s %8s" % ("κατηγορία", "πλήθος", "bytes"))
    print("  " + "-" * 42)
    for c, (n, tot) in cats.items():
        print("  %-26s %6d %8d" % (c, n, tot))
    print("  " + "-" * 42)
    print("  %-26s %6d %8d  (%.1f KB)"
          % ("ΣΥΝΟΛΟ", sum(n for n, _ in cats.values()), len(binary), len(binary) / 1024))
    quad_bytes = sum(len(d) for l, d, sp, c in blob.items
                     if sp is not None and c in ("θόλοι", "δακτύλιοι"))
    if args.quads == "nw":
        print("  Αποθηκεύεται μόνο το nw (%d bytes)· τα ne/sw/se παράγονται με το"
              % quad_bytes)
        print("  flip_mode0. Με --quads all θα ήταν %d bytes (σύνολο %.1f KB)."
              % (quad_bytes * 4, (len(binary) + quad_bytes * 3) / 1024))
    else:
        print("  Τα τεταρτημόρια είναι %d bytes από αυτά. Με --quads nw κρατιέται"
              % quad_bytes)
        print("  μόνο το nw: %d bytes, σύνολο %.1f KB."
              % (quad_bytes // 4, (len(binary) - quad_bytes * 3 // 4) / 1024))
    print()
    print("  Όλες οι επαληθεύσεις (1-9) πέρασαν.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
