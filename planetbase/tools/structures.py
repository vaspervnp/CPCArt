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
# Το xl (32x64) του ηλιακού αφαιρέθηκε: 2.048 bytes που η τράπεζα 7 δεν είχε.
# Ο πίνακας struct_dims κρατά 4 θέσεις ανά δομή, οπότε η τέταρτη μένει 0,0.
SIZES_4 = [("s", 8, 16), ("m", 16, 32), ("l", 24, 48)]
SIZES_3 = [("s", 8, 16), ("m", 16, 32), ("l", 24, 48)]
SIZES_1 = [("", 32, 64)]            # δομές που έχουν ένα μόνο μέγεθος
SIZES_1M = [("", 16, 32)]           # ... και οι μικρότερες από αυτές

# (όνομα, συνάρτηση, μεγέθη, μάσκα;, σχόλιο) — τα μεγέθη ακολουθούν το Planetbase.
# Σχεδόν όλες έχουν μάσκα· η πλατφόρμα όχι, γιατί είναι χτιστό δάπεδο που
# αντικαθιστά το έδαφος αντί να κάθεται πάνω του — και έτσι κοστίζει τα μισά.
STRUCTURES = [
    ("solar",     "solar_panel",     SIZES_4,  True,  "ηλιακό πάνελ — 3 μεγέθη"),
    ("turbine",   "wind_turbine",    SIZES_3,  True,  "ανεμογεννήτρια"),
    ("collector", "power_collector", SIZES_3,  True,  "συσσωρευτής ενέργειας"),
    ("extractor", "water_extractor", SIZES_3,  True,  "αντλία νερού"),
    ("mine",      "mine",            SIZES_1,  True,  "ορυχείο — ένα μέγεθος"),
    ("airlock",   "airlock",         SIZES_1M, True,  "αεροθάλαμος — ένα μέγεθος"),
    ("pad",       "landing_pad",     SIZES_1,  False, "πλατφόρμα — ΑΔΙΑΦΑΝΗΣ"),
    ("ship",      "ship",            SIZES_1M, True,  "σκάφος — κάτοψη"),
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


def airlock(w, h):
    """Αεροθάλαμος: θάλαμος με δύο αντικριστές πόρτες και ζώνη κινδύνου.

    Συμμετρικός πάνω-κάτω, ώστε να κουμπώνει με διάδρομο από όποια πλευρά
    χρειαστεί· στο Planetbase ο αεροθάλαμος συνδέεται με ΜΙΑ εσωτερική δομή.
    Οι ρίγες κινδύνου είναι τα ίδια χρώματα με το εικονίδιο δωματίου `airlock`,
    ώστε να διαβάζεται αμέσως τι είναι.
    """
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            oct_d = max(max(abs(vx), abs(vy)), (abs(vx) + abs(vy)) * 0.78)
            door = abs(vx) <= R * 0.30 and abs(vy) > abs(vx)
            if oct_d > R:
                row.append(PEN_OUTSIDE)
            elif oct_d > R - 2:
                # το άνοιγμα της πόρτας κόβει τον εξωτερικό τοίχο
                row.append(PEN_CORR_FLOOR if door else PEN_CORR_EDGE)
            elif oct_d > R - 5:
                # ζώνη κινδύνου: ρίγες 1 px x 2 γραμμές, οπτικά τετράγωνες
                row.append(PEN_CORR_FLOOR if door
                           else (PEN_RED if ((x + y // 2) & 1) else PEN_YELLOW))
            elif oct_d > R - 6:
                row.append(PEN_CORR_EDGE)
            else:
                row.append(PEN_DOME_FLOOR)      # ο θάλαμος, υπό πίεση
        pens.append(row)
    return pens


def landing_pad(w, h):
    """Πλατφόρμα προσγείωσης: τετράγωνο χτιστό δάπεδο με βαμμένο οκτάγωνο.

    **Αδιαφανής** — η μόνη δομή χωρίς μάσκα. Είναι χτιστό δάπεδο που
    ΑΝΤΙΚΑΘΙΣΤΑ το έδαφος αντί να κάθεται πάνω του, οπότε δεν χρειάζεται να
    φαίνεται τίποτα από κάτω. Κοστίζει έτσι 1.024 bytes αντί για 2.048.

    Οι γωνίες δεν μπορούν να μιμηθούν έδαφος — τα pens του εδάφους αλλάζουν ανά
    πλανήτη — οπότε είναι ανώμαλο τσιμέντο με dither, και το οκτάγωνο είναι
    βαμμένο πάνω στο τετράγωνο. Το κεντρικό σημάδι είναι σταυρός, που στην
    κάτοψη διαβάζεται ως σημείο επαφής ανεξάρτητα από τον προσανατολισμό.
    """
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            # 1/sqrt(2) = 0.707 δίνει ΚΑΝΟΝΙΚΟ οκτάγωνο: στην κορυφή
            # (a, a*tan22.5) ισχύει |x|+|y| = a*sqrt(2). Μεγαλύτερος
            # συντελεστής κόβει τις γωνίες και το σχήμα γίνεται ρόμβος·
            # μικρότερος το ισιώνει προς τετράγωνο.
            oct_d = max(max(abs(vx), abs(vy)), (abs(vx) + abs(vy)) * 0.707)
            # σταυρός στο κέντρο: μπράτσα 2 px φαρδιά, οπτικά 4
            cross = (abs(vx) <= 2 and abs(vy) <= R * 0.42) or \
                    (abs(vy) <= 2 and abs(vx) <= R * 0.42)
            if oct_d > R:
                # Έξω από το βαμμένο οκτάγωνο συνεχίζει η ίδια πλάκα: μία
                # χυτή επιφάνεια με το οκτάγωνο ζωγραφισμένο πάνω της. Dither
                # εδώ θα ανταγωνιζόταν τα σημάδια· μόνο το χείλος της πλάκας
                # είναι σκούρο, ώστε να ορίζεται πάνω στο έδαφος.
                edge = x == 0 or x == w - 1 or y < 2 or y >= h - 2
                row.append(PEN_SHADOW if edge else PEN_CORR_FLOOR)
            elif oct_d > R - 2:
                # χείλος με φώτα προσέγγισης στις τέσσερις διαγωνίους
                lit = abs(abs(vx) - abs(vy)) < 3
                row.append(PEN_YELLOW if lit else PEN_CORR_EDGE)
            elif oct_d > R - 4:
                row.append(PEN_SHADOW)              # σκοτεινή ζώνη ασφαλείας
            elif cross:
                row.append(PEN_YELLOW)
            elif oct_d > R - 6:
                # ρίγες πρόσδεσης, 1 px x 2 γραμμές ώστε να είναι οπτικά τετράγωνες
                row.append(PEN_CORR_EDGE if ((x + y // 2) & 1) else PEN_CORR_FLOOR)
            else:
                row.append(PEN_CORR_FLOOR)          # το δάπεδο
        pens.append(row)
    return pens


def ship(w, h):
    """Σκάφος σε κάτοψη: άτρακτος, δύο πτέρυγες, δύο κινητήρες.

    Μισό πλάτος από την πλατφόρμα, ώστε να κάθεται μέσα στο οκτάγωνο και να
    φαίνεται ότι προσγειώθηκε και δεν το σκεπάζει. Η μύτη δείχνει πάνω· όταν
    χρειαστεί άλλη κατεύθυνση, το flip_mode0 δίνει τις άλλες τρεις.
    """
    R = h / 2
    pens = []
    for y in range(h):
        row = []
        for x in range(w):
            vx, vy = _visual(x, y, w, h)
            t = (vy + R) / (2 * R)                  # 0 στη μύτη, 1 στην ουρά
            body = abs(vx) <= 3 + 4.5 * t           # άτρακτος που ανοίγει προς τα πίσω
            wing = 0.45 < t < 0.72 and abs(vx) <= R * 0.92
            engine = t > 0.88 and 3 < abs(vx) <= 9
            if engine:
                row.append(PEN_RED if t > 0.94 else PEN_RED_DARK)
            elif body and t < 0.15:
                row.append(PEN_CORR_EDGE)           # μύτη
            elif body and 0.20 < t < 0.45:
                row.append(PEN_DOME_FLOOR)          # πιλοτήριο
            elif body:
                row.append(PEN_CYAN)
            elif wing:
                row.append(PEN_CYAN if abs(vx) < R * 0.66 else PEN_DOME_EDGE)
            else:
                row.append(PEN_OUTSIDE)
        pens.append(row)
    return pens


BUILDERS = {
    "mine": mine,
    "landing_pad": landing_pad,
    "ship": ship,
    "airlock": airlock,
    "solar_panel": solar_panel,
    "wind_turbine": wind_turbine,
    "power_collector": power_collector,
    "water_extractor": water_extractor,
}


def build(name):
    """[(όνομα sprite, pens)] για όλα τα μεγέθη μιας δομής."""
    for key, fn, sizes, _, _ in STRUCTURES:
        if key == name:
            return [(f"{key}_{code}" if code else key, BUILDERS[fn](w, h))
                    for code, w, h in sizes]
    raise KeyError(name)


def is_masked(name):
    """Αν η δομή αποθηκεύεται με μάσκα ή αδιαφανής."""
    for key, _, _, masked, _ in STRUCTURES:
        if key == name:
            return masked
    raise KeyError(name)
