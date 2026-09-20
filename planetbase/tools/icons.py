"""ASCII art: εικονίδια τύπου δωματίου (8x8) και φιγούρα αποίκου (3x6).

Οι χαρακτήρες είναι αυτοί της palette.PEN_CHARS, ώστε να διορθώνονται με το χέρι:
    '.' = pen 2 (δάπεδο θόλου, το αδιαφανές φόντο του εικονιδίου)
    'W' = pen 5   'C' = pen 10  'b' = pen 1   'y' = pen 12  'O' = pen 7
    'R' = pen 8   'G' = pen 9   'S' = pen 14  'r' = pen 13
"""

from palette import CHAR_PENS

ICON_W = ICON_H = 8

# Η σειρά είναι ίδια με το R_TYPE στο colony_data.asm.
ROOM_ICONS = [
    ("empty", [                 # 0 - κενό: μόνο δάπεδο
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
    ]),
    ("control", [               # 1 - έλεγχος: οθόνη με κεραία (pens 5, 10)
        "..W..W..",
        "...WW...",
        "WWWWWWWW",
        "WCCCCCCW",
        "WCCCCCCW",
        "WWWWWWWW",
        "...WW...",
        "..WWWW..",
    ]),
    ("quarters", [              # 2 - κοιτώνας: κρεβάτι από το πλάι (pens 5, 1)
        "........",
        "WW......",
        "WWWWWWWW",
        "WbbbbbbW",
        "WbbbbbbW",
        "WWWWWWWW",
        "W......W",
        "W......W",
    ]),
    ("canteen", [               # 3 - καντίνα: μπολ με ατμό (pens 12, 7)
        "..O..O..",
        ".O..O...",
        "..O..O..",
        "........",
        "yyyyyyyy",
        ".yyyyyy.",
        "..yyyy..",
        "........",
    ]),
    ("oxygen", [                # 4 - οξυγόνο: φούσκες (pens 5, 3)
        "........",
        "..cc....",
        ".cWWc...",
        ".cWWc.cc",
        "..cc..cc",
        "....cc..",
        "....cc..",
        "........",
    ]),
    ("greenhouse", [            # 5 - θερμοκήπιο: φυτό σε γλάστρα (pens 9, 14)
        "...GG...",
        "..GGGG..",
        ".GGGGGG.",
        ".GGGGGG.",
        "..GGGG..",
        "...SS...",
        ".SSSSSS.",
        ".SSSSSS.",
    ]),
    ("storage", [               # 6 - αποθήκη: κιβώτιο με τσέρκι (pens 7, 13)
        "OOOOOOOO",
        "OrrrrrrO",
        "OrrrrrrO",
        "OOOOOOOO",
        "OOOOOOOO",
        "OrrrrrrO",
        "OrrrrrrO",
        "OOOOOOOO",
    ]),
    ("airlock", [               # 7 - airlock: πόρτα με ρίγες κινδύνου (pens 8, 12)
        "RRRRRRRR",
        "RyyRRyyR",
        "RRyyRRyy",
        "yRRyyRRy",
        "yyRRyyRR",
        "RyyRRyyR",
        "RRyyRRyy",
        "RRRRRRRR",
    ]),
]

# Φιγούρα αποίκου 3x6. Τοπικό λεξικό: 'X' = pen 6, '.' = διαφανές.
COLONIST_W, COLONIST_H = 3, 6
COLONIST = [
    ".X.",
    ".X.",
    "XXX",
    "XXX",
    "X.X",
    "X.X",
]
COLONIST_LEGEND = {"X": 6, ".": None}   # None = μη σχεδιάζεται


def parse_art(lines, w, h, legend=None, what="art"):
    """ASCII art -> πίνακας [h][w] από pens (ή None για «μη σχεδιάζεται»).

    Αποτυγχάνει με σαφές μήνυμα αν οι διαστάσεις ή οι χαρακτήρες δεν ταιριάζουν.
    """
    if len(lines) != h:
        raise ValueError(f"{what}: {len(lines)} γραμμές αντί για {h}")
    out = []
    for i, line in enumerate(lines):
        if len(line) != w:
            raise ValueError(
                f"{what}: γραμμή {i} έχει {len(line)} χαρακτήρες αντί για {w}: {line!r}")
        row = []
        for j, ch in enumerate(line):
            if legend is not None:
                if ch not in legend:
                    raise ValueError(
                        f"{what}: άγνωστος χαρακτήρας {ch!r} στη γραμμή {i}, στήλη {j}")
                row.append(legend[ch])
            else:
                if ch not in CHAR_PENS:
                    raise ValueError(
                        f"{what}: άγνωστος χαρακτήρας {ch!r} στη γραμμή {i}, στήλη {j}")
                row.append(CHAR_PENS[ch])
        out.append(row)
    return out


# --------------------------------------------------------------------------
# Μηχανήματα
# --------------------------------------------------------------------------
# 8x12 pixels (οπτικά 16x12). Αδιαφανή: κάθονται πάνω στο δάπεδο του θόλου,
# οπότε το '.' είναι pen 2 όπως και στα εικονίδια.
#
# Το δεύτερο πεδίο λέει σε ποια μεγέθη θόλου επιτρέπεται το μηχάνημα.

MACHINE_W, MACHINE_H = 8, 12

MACHINES = [
    ("oxygen", "s", [               # ανακυκλωτής οξυγόνου — δεξαμενή με φούσκες
        "...cc...",
        "..cccc..",
        ".cWWWWc.",
        ".cWWWWc.",
        ".cWWWWc.",
        ".cWWWWc.",
        "..cccc..",
        "...WW...",
        ".WWWWWW.",
        ".W....W.",
        ".WWWWWW.",
        "..W..W..",
    ]),
    ("iron", "sml", [               # iron από ore — καμίνι με δύο καμινάδες
        "..,..,..",
        "..,..,..",
        ",,,,,,,,",
        ",......,",
        ",.RRRR.,",
        ",.RrrR.,",
        ",.RrrR.,",
        ",.RRRR.,",
        ",......,",
        ",,,,,,,,",
        ".,,,,,,.",
        "..,,,,..",
    ]),
    ("bioplastic", "sml", [         # bioplastic — δεξαμενή ζύμωσης
        "SSSSSSSS",
        "S......S",
        "S.GGGG.S",
        "S.GGGG.S",
        "S.GGGG.S",
        "S.GGGG.S",
        "S......S",
        "SSSSSSSS",
        ".S,,,,S.",
        ".S,,,,S.",
        ".SSSSSS.",
        "..SSSS..",
    ]),
    ("weapons", "sml", [            # όπλα — κιβώτιο με πυρομαχικά
        ",,,,,,,,",
        ",.R..R.,",
        ",.R..R.,",
        ",.R..R.,",
        ",.R..R.,",
        ",.R..R.,",
        ",.R..R.,",
        ",......,",
        ",,,,,,,,",
        ".,,,,,,.",
        ".,....,.",
        ".,,,,,,.",
    ]),
    ("processors", "sml", [         # επεξεργαστές — ολοκληρωμένο με ακροδέκτες
        ".,.,.,.,",
        "CCCCCCCC",
        "C......C",
        "C.yyyy.C",
        "C.y..y.C",
        "C.y..y.C",
        "C.yyyy.C",
        "C......C",
        "CCCCCCCC",
        ".,.,.,.,",
        ".,,,,,,.",
        "..,,,,..",
    ]),
    ("robots", "sml", [             # ρομπότ — κεφάλι και κορμός σε βάση
        "..WWWW..",
        ".WMWWMW.",
        ".WWWWWW.",
        "..W..W..",
        ".WWWWWW.",
        ".W.MM.W.",
        ".W.MM.W.",
        ".WWWWWW.",
        "..W..W..",
        "..W..W..",
        ".WW..WW.",
        "........",
    ]),
    ("food", "sml", [               # φαγητό — καλλιέργεια και δίσκος επεξεργασίας
        "...GG...",
        "..GGGG..",
        ".GGGGGG.",
        "..GGGG..",
        "...GG...",
        "yyyyyyyy",
        "y......y",
        "y.OOOO.y",
        "y.OOOO.y",
        "y......y",
        "yyyyyyyy",
        "..y..y..",
    ]),
]
