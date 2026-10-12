"""Το HUD: εικονίδια 8x16 με θέμα, και τα χρώμια 4x8.

Ο χωρισμός είναι σκόπιμος. Τα **4x8** είναι η τυπογραφία και τα σιδερικά —
ψηφία, σύμβολα, πλαίσιο, χάρακας, μπάρα· επαναλαμβάνονται και πρέπει να είναι
μικρά. Τα **8x16** είναι η εικονογραφία: 16x16 μονάδες οθόνης, αρκετά για να
φαίνεται ότι είναι βάζο με καραμέλες και όχι μια μουτζούρα. Στα 4x8 (8x8
μονάδες, τέσσερις στήλες) ένα γλειφιτζούρι δεν διαβάζεται με τίποτα.

Τα εικονίδια είναι ΑΔΙΑΦΑΝΗ με φόντο το μπλε του ταμπλό HUD: κάθονται πάντα
πάνω του, άρα η μάσκα θα ήταν διπλάσια bytes για το τίποτα.
"""
from cpcgfx import HW, HH, PEN_GREY, PEN_HI, PEN_LINE, PEN_MASK, \
                   SpriteSet, blank, parse_art

ICON_W, ICON_H = 8, 16


# Το '-' είναι το φόντο του ταμπλό HUD, το '.' είναι πραγματικό μαύρο.
ICONS = {
    # Βάζο με καραμέλες — οι πόντοι.
    'score': """
    --WWWW--
    --GGGG--
    -WWWWWW-
    -W....W-
    -WrrggW-
    -WrrggW-
    -W....W-
    -WyybbW-
    -WyybbW-
    -W....W-
    -WmmooW-
    -WmmooW-
    -W....W-
    -WWWWWW-
    -GGGGGG-
    --------
    """,
    # Διπλό βέλος με κορμό από ζαχαρωτό — οι κινήσεις που απομένουν.
    # Δύο βέλη που δείχνουν αντίθετα — η ανταλλαγή, άρα οι κινήσεις.
    # Κάθετο διπλό βέλος ΔΕΝ δουλεύει στα 8x16: με pixels 2:1 η μύτη βγαίνει
    # 16 μονάδες φαρδιά και 4 ψηλή, και διαβάζεται σαν παπιγιόν.
    'moves': """
    --------
    --------
    --W-----
    -WW-----
    WWrrWWrr
    -WW-----
    --W-----
    --------
    --------
    -----W--
    -----WW-
    rrWWrrWW
    -----WW-
    -----W--
    --------
    --------
    """,
    # Κλεψύδρα με ζάχαρη — ο χρόνος.
    'time': """
    WWWWWWWW
    WWWWWWWW
    -WyyyyW-
    -WyyyyW-
    --WyyW--
    --WyyW--
    ---WW---
    ---WW---
    ---WW---
    --WyyW--
    --WyyW--
    -WyyyyW-
    -WyyyyW-
    -WyyyyW-
    WWWWWWWW
    WWWWWWWW
    """,
    # Γλειφιτζούρι — ο στόχος της πίστας.
    'goal': """
    --rrrr--
    -rrrrrr-
    -rWWWWr-
    rWWrrWWr
    rWrrrrWr
    rWrWWrWr
    rWrWWrWr
    rWrrrrWr
    rWWrrWWr
    -rWWWWr-
    -rrrrrr-
    --rrrr--
    ---WW---
    ---WW---
    ---WW---
    ---WW---
    """,
    # Ζελέ — ο στόχος «καθάρισε το ζελέ».
    'jelly': """
    --------
    --CCCC--
    -CCCCCC-
    CCCCCCCC
    CCWWCCCC
    CCWWCCCC
    CCCCCCCC
    CCCCCCCC
    CCCCCCCC
    CCCCCCCC
    -CCCCCC-
    -CCCCCC-
    --CCCC--
    --------
    --------
    --------
    """,
    # Τα τρία αστέρια της πίστας, κερδισμένο και άδειο.
    'star_on': """
    --------
    ---yy---
    ---yy---
    --yyyy--
    --yyyy--
    -yyyyyy-
    yyyyyyyy
    yyyyyyyy
    -yyyyyy-
    --yyyy--
    --yyyy--
    -yyyyyy-
    -yy--yy-
    -yy--yy-
    -y----y-
    --------
    """,
    'star_off': """
    --------
    ---GG---
    ---GG---
    --G..G--
    --G..G--
    -G....G-
    G......G
    G......G
    -G....G-
    --G..G--
    --G..G--
    -G....G-
    -GG--GG-
    -GG--GG-
    -G----G-
    --------
    """,
    # Λουκέτο — κλειδωμένη πίστα.
    'lock': """
    --------
    --GGGG--
    -GG--GG-
    -GG--GG-
    -GG--GG-
    yyyyyyyy
    yyyyyyyy
    yyy..yyy
    yyy..yyy
    yyy..yyy
    yyyyyyyy
    yyyyyyyy
    yyyyyyyy
    --------
    --------
    --------
    """,
}

# Κεφαλαία 3x5 — οι ίδιες μορφές με τη γραμματοσειρά 4px του planetbase.
# Δεν ξανασχεδιάστηκαν: στις τρεις στήλες το N, το M και το W είναι λυμένα
# εκεί και δοκιμασμένα σε αληθινή οθόνη, και δύο διαφορετικά αλφάβητα στο ίδιο
# repo θα ήταν δύο πράγματα να συντηρηθούν.
#
# Πέντε γραμμές, στοιχισμένες στη ΒΑΣΗ των ψηφίων (γραμμή 6), γι' αυτό
# ξεκινούν από τη γραμμή 2 ενώ τα ψηφία από τη γραμμή 1.
LETTERS = """
A:.W. W.W WWW W.W W.W
B:WW. W.W WW. W.W WW.
C:.WW W.. W.. W.. .WW
D:WW. W.W W.W W.W WW.
E:WWW W.. WW. W.. WWW
F:WWW W.. WW. W.. W..
G:.WW W.. W.W W.W .WW
H:W.W W.W WWW W.W W.W
I:WWW .W. .W. .W. WWW
J:..W ..W ..W W.W .W.
K:W.W W.W WW. W.W W.W
L:W.. W.. W.. W.. WWW
M:W.W WWW W.W W.W W.W
N:W.W WW. W.W .WW W.W
O:.W. W.W W.W W.W .W.
P:WW. W.W WW. W.. W..
Q:.W. W.W W.W WW. .WW
R:WW. W.W WW. W.W W.W
S:.WW W.. .W. ..W WW.
T:WWW .W. .W. .W. .W.
U:W.W W.W W.W W.W WWW
V:W.W W.W W.W .W. .W.
W:W.W W.W W.W WWW W.W
X:W.W W.W .W. W.W W.W
Y:W.W W.W .W. .W. .W.
Z:WWW ..W .W. W.. WWW
"""

ICON_ORDER = ['score', 'moves', 'time', 'goal', 'jelly',
              'star_on', 'star_off', 'lock']


def icons():
    s = SpriteSet('icons_cpc_mode0', ICON_W, ICON_H, masked=False,
                  note='εικονίδια HUD 8x16 αδιαφανή — βάζο, βέλη, κλεψύδρα, '
                       'γλειφιτζούρι, ζελέ, αστέρια, λουκέτο')
    for name in ICON_ORDER:
        art = parse_art(ICONS[name])
        img = [[PEN_LINE if p is None else p for p in row] for row in art]
        assert len(img) == ICON_H and all(len(r) == ICON_W for r in img), name
        s.add(img, name, 'icon')
    return s


# ------------------------------------------------------------ χρώμια 4x8

def rule_tile():
    """Χάρακας: κορδόνι ζαχαρωτού που επαναλαμβάνεται οριζόντια.

    Περίοδος ρίγας 4 pixels σε x — όσο ακριβώς και το πλακάκι, άρα δεν
    φαίνεται ραφή όσο κι αν το επαναλάβεις.
    """
    img = blank(HW, HH, PEN_MASK)
    for y in range(2, 6):
        for x in range(HW):
            img[y][x] = (PEN['r'], PEN_HI)[((x - y // 2) // 2) % 2]
    for x in range(HW):
        img[2][x] = PEN_LINE
        img[5][x] = PEN['R']
    return img


BAR = {
    # Σωλήνας που γεμίζει ζάχαρη — η πρόοδος προς το επόμενο αστέρι.
    'bar_l': """
    ----
    -GGG
    G...
    G...
    G...
    G...
    -GGG
    ----
    """,
    'bar_e': """
    ----
    GGGG
    ....
    ....
    ....
    ....
    GGGG
    ----
    """,
    'bar_f': """
    ----
    GGGG
    yyyy
    yyoo
    yyoo
    oooo
    GGGG
    ----
    """,
    'bar_r': """
    ----
    GGG-
    ...G
    ...G
    ...G
    ...G
    GGG-
    ----
    """,
}

from cpcgfx import PEN  # noqa: E402  (χρειάζεται μετά τον ορισμό των πινάκων)


def bar_frames():
    out = []
    for name in ('bar_l', 'bar_e', 'bar_f', 'bar_r'):
        art = parse_art(BAR[name])
        img = [[PEN_LINE if p is None else p for p in row] for row in art]
        assert len(img) == HH and all(len(r) == HW for r in img), name
        out.append((name, img))
    return out
