"""Εξωτερικές δομές: ηλιακά, ανεμογεννήτριες, συσσωρευτές, αντλίες νερού.

Δεν είναι μηχανές μέσα σε θόλο — είναι αυτοτελή κτίσματα πάνω στο έδαφος, σε
κάτοψη όπως και οι θόλοι. Παράγονται παραμετρικά (όχι ASCII art): το μεγαλύτερο
μέγεθος είναι 32x64 pixels, δηλαδή οπτικά 64x64, και κάθε μικρότερο μέγεθος
είναι το ίδιο σχήμα σε μικρότερο πλαίσιο — άρα ένα σχέδιο καλύπτει όλες τις
παραλλαγές που έχει το Planetbase.

Όλα έχουν μάσκα: ό,τι είναι έξω από το σχήμα μένει pen 0 (διαφανές).
"""

import math

from palette import (PEN_OUTSIDE, PEN_SHADOW, PEN_DOME_FLOOR, PEN_DOME_EDGE,
                     PEN_CORR_FLOOR, PEN_CORR_EDGE, PEN_COLONIST)

# Τα pens 7, 11, 12, 14 ανήκουν στο έδαφος και αλλάζουν ανά πλανήτη· οι δομές
# δεν τα αγγίζουν, αλλιώς θα άλλαζαν χρώμα μαζί με τον πλανήτη.
PEN_PINK, PEN_CYAN, PEN_YELLOW, PEN_RED_DARK, PEN_RED = 15, 10, 6, 13, 8

# Τα μεγέθη κάθε δομής: (κωδικός, πλάτος σε pixels, γραμμές).
# Κάθε ένα είναι οπτικά τετράγωνο (πλάτος x2 == ύψος).
SIZES_4 = [("s", 8, 16), ("m", 16, 32), ("l", 24, 48), ("xl", 32, 64)]
SIZES_3 = [("s", 8, 16), ("m", 16, 32), ("l", 24, 48)]
SIZES_1 = [("", 32, 64)]            # δομές που έχουν ένα μόνο μέγεθος

# (όνομα, συνάρτηση, μεγέθη, σχόλιο)  — τα μεγέθη ακολουθούν το Planetbase
STRUCTURES = [
    ("solar",     "solar_panel",     SIZES_4, "ηλιακό πάνελ — 4 μεγέθη"),
    ("turbine",   "wind_turbine",    SIZES_3, "ανεμογεννήτρια"),
    ("collector", "power_collector", SIZES_3, "συσσωρευτής ενέργειας"),
    ("extractor", "water_extractor", SIZES_3, "αντλία νερού"),
    ("mine",      "mine",            SIZES_1, "ορυχείο — ένα μέγεθος"),
]


def _visual(x, y, w, h):
    """Οπτικές συντεταγμένες με κέντρο το μέσο του πλαισίου (διόρθωση 2:1)."""
    return (x + 0.5) * 2 - w, (y + 0.5) - h / 2


def solar_panel(w, h):
    """Συστοιχία πάνελ σε κάτοψη: γκρι πλαίσιο, σκούρα κελιά με κυανό πλέγμα."""
    cw = max(2, w // 4)                 # πλάτος κελιού σε pixels
    ch = max(4, h // 4)                 # ύψος κελιού σε γραμμές
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                row.append(PEN_CORR_FLOOR)                  # πλαίσιο
            elif (x - 1) % cw == cw - 1 or (y - 1) % ch == ch - 1:
                row.append(PEN_CYAN)                        # πλέγμα
            else:
                row.append(PEN_SHADOW)                      # κελί
        pens.append(row)
    return pens


def wind_turbine(w, h):
    """Τρία πτερύγια γύρω από πλήμνη, σε κάτοψη."""
    R = h / 2
    hub = R * 0.22
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            r = math.hypot(vx, vy)
            if r <= hub:
                row.append(PEN_CORR_EDGE)                   # πλήμνη
            elif r <= R:
                a = math.atan2(vy, vx)
                near = min(abs((a - b + math.pi) % (2 * math.pi) - math.pi)
                           for b in (math.radians(90), math.radians(210), math.radians(330)))
                # Το πτερύγιο λεπταίνει προς τα έξω, αλλά στα μικρά μεγέθη
                # ανοίγει: αλλιώς πέφτει κάτω από ένα pixel και χάνεται.
                half = (0.30 + 0.20 * (1 - min(R, 32) / 32)) * (1 - 0.50 * r / R)
                if near <= half:
                    row.append(PEN_CORR_EDGE if near > half * 0.55 else PEN_CORR_FLOOR)
                else:
                    row.append(PEN_OUTSIDE)
            else:
                row.append(PEN_OUTSIDE)
        pens.append(row)
    return pens


def power_collector(w, h):
    """Κυκλικός συσσωρευτής: γκρι στεφάνι και ομόκεντροι δακτύλιοι ενέργειας."""
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            r = math.hypot(vx, vy)
            if r > R:
                row.append(PEN_OUTSIDE)
            elif r > R - 2:
                row.append(PEN_CORR_FLOOR)                  # στεφάνι
            elif r > R - 3:
                row.append(PEN_CORR_EDGE)
            else:
                # κίτρινο εναλλάξ με κόκκινο — το παστέλ κίτρινο πήγε στο έδαφος
                band = int((R - r) / max(2, R / 5)) % 2
                row.append(PEN_YELLOW if band else PEN_RED)
        pens.append(row)
    return pens


def water_extractor(w, h):
    """Κεφαλή γεώτρησης: γκρι στεφάνι, νερό, και τέσσερις σωλήνες."""
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            r = math.hypot(vx, vy)
            if r > R:
                row.append(PEN_OUTSIDE)
                continue
            # ελάχιστο πάχος σωλήνα ~1 pixel, αλλιώς εξαφανίζεται στα μικρά
            pw = max(R * 0.12, 1.6)
            pipe = (abs(vx) <= pw or abs(vy) <= pw) and r > R * 0.32
            if r > R - 2:
                row.append(PEN_CORR_FLOOR)                  # στεφάνι
            elif pipe:
                row.append(PEN_CORR_EDGE)                   # σωλήνες
            elif r <= R * 0.32:
                row.append(PEN_SHADOW)                      # το φρέαρ
            else:
                row.append(PEN_DOME_FLOOR)                  # νερό
        pens.append(row)
    return pens


def mine(w, h):
    """Ορυχείο: οκταγωνικό κτίσμα με κεντρικό φρέαρ και ταινίες μεταφοράς.

    Οκτάγωνο επίτηδες — οι άλλες δομές είναι στρογγυλές, οπότε ξεχωρίζει αμέσως
    ακόμη και στο μικρότερο μέγεθος.
    """
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            oct_d = max(max(abs(vx), abs(vy)), (abs(vx) + abs(vy)) * 0.72)
            if oct_d > R:
                row.append(PEN_OUTSIDE)
                continue
            if oct_d > R - 2:
                row.append(PEN_CORR_FLOOR)                  # εξωτερικός τοίχος
                continue
            if oct_d > R - 3:
                row.append(PEN_CORR_EDGE)
                continue
            r = math.hypot(vx, vy)
            belt = max(R * 0.10, 1.4)
            if r <= R * 0.28:
                row.append(PEN_SHADOW)                      # το φρέαρ
            elif r <= R * 0.42:
                row.append(PEN_RED_DARK)                    # μετάλλευμα
            elif abs(vx) <= belt or abs(vy) <= belt:
                row.append(PEN_PINK)                      # ταινίες μεταφοράς
            else:
                row.append(PEN_CORR_FLOOR)
        pens.append(row)
    return pens


BUILDERS = {
    "mine": mine,
    "solar_panel": solar_panel,
    "wind_turbine": wind_turbine,
    "power_collector": power_collector,
    "water_extractor": water_extractor,
}


def build(name):
    """[(όνομα sprite, pens)] για όλα τα μεγέθη μιας δομής."""
    for key, fn, sizes, _ in STRUCTURES:
        if key == name:
            return [(f"{key}_{code}" if code else key, BUILDERS[fn](w, h))
                    for code, w, h in sizes]
    raise KeyError(name)
