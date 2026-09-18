"""Η παλέτα Mode 0 του colony sim — ορίζεται εδώ και μόνο εδώ.

Κάθε pen έχει: όνομα, firmware colour number (για SCR SET INK / Gate Array),
RGB για τις προεπισκοπήσεις PNG, και έναν χαρακτήρα για το ASCII art.
"""

# (pen, όνομα CPC, FW #, RGB, χαρακτήρας ASCII, χρήση)
PALETTE = [
    ( 0, "Black",        0, (0x00, 0x00, 0x00), " ", "φόντο / έδαφος"),
    ( 1, "Blue",         1, (0x00, 0x00, 0x80), "b", "σκιές"),
    ( 2, "Sky blue",    11, (0x00, 0x80, 0xFF), ".", "δάπεδο θόλου"),
    ( 3, "Pastel cyan", 23, (0x80, 0xFF, 0xFF), "c", "περίγραμμα θόλου"),
    ( 4, "White",       13, (0x80, 0x80, 0x80), ",", "δάπεδο διαδρόμου"),
    ( 5, "Bright white",26, (0xFF, 0xFF, 0xFF), "W", "περίγραμμα διαδρόμου"),
    ( 6, "Bright yellow",24,(0xFF, 0xFF, 0x00), "Y", "άποικοι"),
    ( 7, "Orange",      15, (0xFF, 0x80, 0x00), "O", "εικονίδια"),
    ( 8, "Bright red",   6, (0xFF, 0x00, 0x00), "R", "συναγερμός / εικονίδια"),
    ( 9, "Bright green",18, (0x00, 0xFF, 0x00), "G", "εικονίδια (θερμοκήπιο)"),
    (10, "Cyan",        10, (0x00, 0x80, 0x80), "C", "εικονίδια"),
    (11, "Mauve",        5, (0x80, 0x00, 0xFF), "M", "εικονίδια"),
    (12, "Pastel yellow",25,(0xFF, 0xFF, 0x80), "y", "εικονίδια"),
    (13, "Red",          3, (0x80, 0x00, 0x00), "r", "εικονίδια"),
    (14, "Sea green",   19, (0x00, 0xFF, 0x80), "S", "εικονίδια"),
    (15, "Pink",        16, (0xFF, 0x80, 0x80), "P", "εικονίδια"),
]

NAMES     = [e[1] for e in PALETTE]
FW        = [e[2] for e in PALETTE]
RGB       = [e[3] for e in PALETTE]
PEN_CHARS = [e[4] for e in PALETTE]
USAGE     = [e[5] for e in PALETTE]

# χαρακτήρας -> pen (η αντίστροφη αντιστοίχιση για το ASCII art)
CHAR_PENS = {c: i for i, c in enumerate(PEN_CHARS)}

# Ρόλοι — ο κώδικας γεωμετρίας αναφέρεται σε αυτά, όχι σε γυμνούς αριθμούς.
PEN_OUTSIDE    = 0
PEN_SHADOW     = 1
PEN_DOME_FLOOR = 2
PEN_DOME_EDGE  = 3
PEN_CORR_FLOOR = 4
PEN_CORR_EDGE  = 5
PEN_COLONIST   = 6

assert len(PALETTE) == 16
assert len(set(PEN_CHARS)) == 16, "κάθε pen χρειάζεται μοναδικό χαρακτήρα"
assert all(e[0] == i for i, e in enumerate(PALETTE))


def pens_to_ascii(pens):
    """Σειρά από pens -> συμβολοσειρά ASCII (για τα σχόλια του .asm)."""
    return "".join(PEN_CHARS[p] for p in pens)
