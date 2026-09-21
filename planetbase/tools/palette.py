"""Η παλέτα Mode 0 του colony sim — ορίζεται εδώ και μόνο εδώ.

Κάθε pen έχει: όνομα, firmware colour number (για SCR SET INK / Gate Array),
RGB για τις προεπισκοπήσεις PNG, και έναν χαρακτήρα για το ASCII art.
"""

# (pen, όνομα CPC, FW #, RGB, χαρακτήρας ASCII, χρήση)
#
# Pens 0-6 είναι ΚΑΡΦΩΜΕΝΑ: οι μάσκες και κάθε δομικό sprite στηρίζονται πάνω
# τους, και το pen 0 πρέπει να μείνει το διαφανές χρώμα.
#
# Pens 7, 11, 12, 14 ανήκουν στο ΕΔΑΦΟΣ και αλλάζουν ανά πλανήτη (planet_pens).
# Ό,τι δεν είναι έδαφος δεν επιτρέπεται να τα χρησιμοποιεί — αλλιώς το εικονίδιο
# αλλάζει χρώμα όταν αλλάζει ο πλανήτης. Τα εικονίδια, οι μηχανές και τα φυτά
# έχουν τα 8, 9, 10, 13, 15 ως δικά τους, συν όσα από τα 1-6 διαβάζονται σωστά.
#
# Οι τιμές FW εδώ είναι του πλανήτη Desert — ο προεπιλεγμένος.
PALETTE = [
    ( 0, "Black",        0, (0x00, 0x00, 0x00), " ", "μαύρο / διαφανές"),
    ( 1, "Blue",         1, (0x00, 0x00, 0x80), "b", "σκιές, σώμα νερού"),
    ( 2, "Sky blue",    11, (0x00, 0x80, 0xFF), ".", "δάπεδο θόλου"),
    ( 3, "Pastel cyan", 23, (0x80, 0xFF, 0xFF), "c", "περίγραμμα θόλου"),
    ( 4, "White",       13, (0x80, 0x80, 0x80), ",", "δάπεδο διαδρόμου"),
    ( 5, "Bright white",26, (0xFF, 0xFF, 0xFF), "W", "περίγραμμα διαδρόμου"),
    ( 6, "Bright yellow",24,(0xFF, 0xFF, 0x00), "Y", "άποικοι, εικονίδια"),
    ( 7, "Orange",      15, (0xFF, 0x80, 0x00), "T", "ΕΔΑΦΟΣ — βάση"),
    ( 8, "Bright red",   6, (0xFF, 0x00, 0x00), "R", "συναγερμός / εικονίδια"),
    ( 9, "Bright green",18, (0x00, 0xFF, 0x00), "G", "εικονίδια (θερμοκήπιο)"),
    (10, "Cyan",        10, (0x00, 0x80, 0x80), "C", "εικονίδια"),
    (11, "Red",          3, (0x80, 0x00, 0x00), "D", "ΕΔΑΦΟΣ — σκούρο"),
    (12, "Pastel yellow",25,(0xFF, 0xFF, 0x80), "H", "ΕΔΑΦΟΣ — φωτεινό"),
    (13, "Red",          3, (0x80, 0x00, 0x00), "r", "εικονίδια"),
    (14, "Cyan",        10, (0x00, 0x80, 0x80), "w", "ΕΔΑΦΟΣ — νερό / πάγος"),
    (15, "Pink",        16, (0xFF, 0x80, 0x80), "P", "εικονίδια"),
]

# Τα τέσσερα pens του εδάφους, με τη σειρά που μπαίνουν στο planet_pens.
TERRAIN_PENS = [7, 11, 12, 14]

# Τα pens που ανήκουν αποκλειστικά σε εικονίδια/μηχανές/φυτά.
ICON_PENS = [8, 9, 10, 13, 15]

# Οι τέσσερις πλανήτες: firmware numbers για τα pens 7, 11, 12, 14.
# Κανένα δεν επαναλαμβάνει τα FW των pens 0-6 (0, 1, 11, 23, 13, 26, 24) —
# αλλιώς το έδαφος θα εξαφανιζόταν πάνω στις δομές που πατάνε επάνω του.
PLANETS = [
    ("desert", [15, 3, 25, 10], "άμμος και σκουριά"),
    ("ice",    [14, 2, 20, 22], "πάγος και χιόνι"),
    ("storm",  [12, 9, 21, 19], "λάσπη και βρύα"),
    ("barren", [10, 4, 14,  2], "γυμνός βράχος"),
]

# RGB προεπισκόπησης για κάθε firmware number του CPC (0-26).
FW_RGB = [
    (0x00,0x00,0x00), (0x00,0x00,0x80), (0x00,0x00,0xFF), (0x80,0x00,0x00),
    (0x80,0x00,0x80), (0x80,0x00,0xFF), (0xFF,0x00,0x00), (0xFF,0x00,0x80),
    (0xFF,0x00,0xFF), (0x00,0x80,0x00), (0x00,0x80,0x80), (0x00,0x80,0xFF),
    (0x80,0x80,0x00), (0x80,0x80,0x80), (0x80,0x80,0xFF), (0xFF,0x80,0x00),
    (0xFF,0x80,0x80), (0xFF,0x80,0xFF), (0x00,0xFF,0x00), (0x00,0xFF,0x80),
    (0x00,0xFF,0xFF), (0x80,0xFF,0x00), (0x80,0xFF,0x80), (0x80,0xFF,0xFF),
    (0xFF,0xFF,0x00), (0xFF,0xFF,0x80), (0xFF,0xFF,0xFF),
]


def planet_rgb(planet_index):
    """RGB των 16 pens για έναν πλανήτη — μόνο τα 4 του εδάφους αλλάζουν."""
    rgb = list(RGB)
    for pen, fw in zip(TERRAIN_PENS, PLANETS[planet_index][1]):
        rgb[pen] = FW_RGB[fw]
    return rgb

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
PEN_TERRAIN    = 7      # βάση εδάφους
PEN_TER_DARK   = 11     # σκούρο εδάφους
PEN_TER_HIGH   = 12     # φωτεινό εδάφους
PEN_WATER      = 14     # νερό / πάγος — το pen που κυκλώνει η μηχανή

assert len(PALETTE) == 16
assert len(set(PEN_CHARS)) == 16, "κάθε pen χρειάζεται μοναδικό χαρακτήρα"
assert all(e[0] == i for i, e in enumerate(PALETTE))


def pens_to_ascii(pens):
    """Σειρά από pens -> συμβολοσειρά ASCII (για τα σχόλια του .asm)."""
    return "".join(PEN_CHARS[p] for p in pens)
