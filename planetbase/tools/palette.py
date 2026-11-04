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
    ( 2, "Pastel cyan", 23, (0x80, 0xFF, 0xFF), ".", "δάπεδο θόλου — το γυαλί"),
    ( 3, "Sky blue",    11, (0x00, 0x80, 0xFF), "c", "χείλος θόλου και λωρίδα του γυαλιού"),
    ( 4, "White",       13, (0x80, 0x80, 0x80), ",", "άκρες και αρμοί του μετάλλου (γκρι)"),
    ( 5, "Bright white",26, (0xFF, 0xFF, 0xFF), "W", "σώμα διαδρόμων και δομών (λευκό μέταλλο)"),
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

# Τα ονόματα του firmware για τους ίδιους 27 αριθμούς (εγχειρίδιο του 6128).
FW_NAMES = [
    "Black", "Blue", "Bright blue", "Red", "Magenta", "Mauve", "Bright red",
    "Purple", "Bright magenta", "Green", "Cyan", "Sky blue", "Yellow", "White",
    "Pastel blue", "Orange", "Pink", "Pastel magenta", "Bright green",
    "Sea green", "Bright cyan", "Lime", "Pastel green", "Pastel cyan",
    "Bright yellow", "Pastel yellow", "Bright white",
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
# Βήμα 178 (το στυλ «λευκό μέταλλο», φως από πάνω): το σώμα των διαδρόμων, των
# δακτυλίων και των δομών είναι λευκό και οι άκρες γκρι — ως τότε ανάποδα. Τα
# θεμέλια και η πλατφόρμα μένουν γκρι τσιμέντο: εκεί τα pens είναι ρητά.
PEN_GREY       = 4
PEN_WHITE      = 5
PEN_CORR_FLOOR = PEN_WHITE
PEN_CORR_EDGE  = PEN_GREY
PEN_COLONIST   = 6
PEN_TERRAIN    = 7      # βάση εδάφους
PEN_TER_DARK   = 11     # σκούρο εδάφους
PEN_TER_HIGH   = 12     # φωτεινό εδάφους
PEN_WATER      = 14     # νερό / πάγος — το pen που κυκλώνει η μηχανή

assert len(PALETTE) == 16
assert len(set(PEN_CHARS)) == 16, "κάθε pen χρειάζεται μοναδικό χαρακτήρα"
assert all(e[0] == i for i, e in enumerate(PALETTE))
# Το όνομα και το RGB κάθε pen είναι αντίγραφα του αριθμού FW· να μη φύγουν.
assert all(e[1] == FW_NAMES[e[2]] and e[3] == FW_RGB[e[2]] for e in PALETTE), \
    "όνομα ή RGB pen που δεν ταιριάζει με τον αριθμό firmware του"
# Το palette_fw ΕΙΝΑΙ ο πρώτος πλανήτης: εκεί ξεκινά το παιχνίδι, και το
# palette.gpl (χωρίς όνομα πλανήτη) λέει ότι είναι αυτός.
assert [FW[p] for p in TERRAIN_PENS] == PLANETS[0][1], \
    "το έδαφος του palette_fw δεν είναι του πρώτου πλανήτη"


def pens_to_ascii(pens):
    """Σειρά από pens -> συμβολοσειρά ASCII (για τα σχόλια του .asm)."""
    return "".join(PEN_CHARS[p] for p in pens)
