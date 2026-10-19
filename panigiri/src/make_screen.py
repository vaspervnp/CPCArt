"""Μια φωτογραφία -> ολόκληρη οθόνη Mode 0 του Amstrad CPC 6128.

    python3 src/make_screen.py                 # με τις επιλεγμένες ρυθμίσεις
    python3 src/make_screen.py --compare       # φύλλο σύγκρισης dither στο /tmp

ΤΟ ΜΕΓΕΘΟΣ

    Mode 0: 160 x 200 pixels, 16 pens, 2 pixels το byte, αναλογία pixel 2:1

Το pixel του Mode 0 είναι **διπλάσια φαρδύ από ψηλό**, οπότε 160 x 2 = 320
μονάδες επί 200 γραμμές — λόγος 1,600. Η πηγή είναι 2000x1250, λόγος επίσης
**1,600**. Κουμπώνει ακριβώς: σμίκρυνση σε 160x200 χωρίς κόψιμο και χωρίς
παραμόρφωση. (Η σμίκρυνση ΦΑΙΝΕΤΑΙ να στριμώχνει την εικόνα στο μισό πλάτος —
δεν στριμώχνει· η οθόνη την ξαναπλαταίνει.)

Η ΜΝΗΜΗ ΟΘΟΝΗΣ

Δεν είναι γραμμική. Οι 200 γραμμές είναι πλεγμένες σε οκτάδες:

    offset = (y & 7) * #800  +  (y >> 3) * 80  +  (x >> 1)

Δηλαδή η γραμμή 0 στο #0000, η 1 στο #0800, ... η 7 στο #3800, και μετά η 8
ξαναπιάνει από το #0050. Τα τελευταία 48 bytes κάθε μπλοκ 2K δεν φαίνονται:
16384 bytes συνολικά, 16336 χρησιμοποιούμενα.
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter

import cpcimg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
TMP = os.environ.get('TMPDIR', '/tmp')

ROW_BYTES = 80                       # και στους δύο τρόπους
SCREEN = 0x4000                      # 16384 bytes, #C000-#FFFF

# Και οι δύο τρόποι γεμίζουν ΤΗΝ ΙΔΙΑ οθόνη 16K με 80 bytes τη γραμμή. Αλλάζει
# μόνο πόσα pixels χωράνε στο byte, και άρα πόσο φαρδύ είναι το pixel:
#
#   Mode 0  160x200 pixels, 16 pens, 2 px/byte, pixel 2:1
#   Mode 1  320x200 pixels,  4 pens, 4 px/byte, pixel 1:1
#   Mode 2  640x200 pixels,  2 pens, 8 px/byte, pixel 1:2 (μισό πλάτος)
#
# Η ΟΘΟΝΗ βγαίνει ίδια και στους δύο: 320x200 μονάδες, λόγος 1,600.
MODES = {
    0: dict(w=160, pens=16, ppb=2, aspect=2, pack=cpcimg.mode0_byte,
            unpack=cpcimg.mode0_pens),
    1: dict(w=320, pens=4, ppb=4, aspect=1, pack=cpcimg.mode1_byte,
            unpack=cpcimg.mode1_pens),
    2: dict(w=640, pens=2, ppb=8, aspect=0.5, pack=cpcimg.mode2_byte,
            unpack=cpcimg.mode2_pens),
}
H = 200

# Βάρη για την απόσταση χρωμάτων: το μάτι βλέπει πιο πολύ το πράσινο.
WEIGHT = (2.0, 4.0, 3.0)

# ΟΙ ΔΥΟ ΕΠΙΛΟΓΕΣ, ΚΑΙ ΠΩΣ ΚΡΙΘΗΚΑΝ
#
# Και τις δύο τις πήρα πρώτα με το μάτι και τις δύο τις γύρισε η μέτρηση.
# Το μέτρο είναι η `perceived()` παρακάτω: θολώνει ΚΑΙ την πηγή ΚΑΙ το
# αποτέλεσμα πριν τα συγκρίνει. Ο dither ανταλλάσσει τοπική ακρίβεια για
# ακρίβεια επιφάνειας, οπότε σύγκριση pixel-προς-pixel τιμωρεί ακριβώς αυτό
# που κάνει σωστά.
#
#   παλέτα        ένταση   σφάλμα   νεκρές πένες
#   αυτόματη       0,35     15,36        0     <-- εδώ
#   αυτόματη       1,00      3,08        0
#   σχεδιασμένη    0,35     15,12        2
#   σχεδιασμένη    1,00      3,43        0
#
# ΠΡΟΣΟΧΗ: η ένταση ΔΕΝ διαλέγεται από τον πίνακα. Το 1,00 είναι πενταπλάσια
# πιο πιστό και ήταν η αρχική επιλογή· ο κάτοχος του repo το είδε και ζήτησε
# λιγότερο dither. Η πιστότητα μετριέται, η εμφάνιση κρίνεται — και η δεύτερη
# είναι δική του. Ο μοχλός είναι αυτή η μία γραμμή· 0,00 σβήνει τον dither
# εντελώς και αφήνει καθαρές επίπεδες περιοχές με ορατές ζώνες.
#
# ΠΑΛΕΤΑ. Στα εικονίδια 32x32 η σχεδιασμένη παλέτα κερδίζει πάντα: ο
# διαλέκτης ξοδεύει pens σε αποχρώσεις που πέφτουν σκόρπιες πάνω στα
# περιγράμματα σαν σκόνη. Εδώ ΟΧΙ. Δεν υπάρχουν περιγράμματα ενός pixel,
# υπάρχουν μεγάλες επιφάνειες που ο dither ανακατεύει, και ό,τι καλύπτει
# επιφάνεια αξίζει pen. Δοκίμασα σχεδιασμένη — πρόσθεσα Mauve «για τα
# βουνά» — και το Mauve βγήκε να χρησιμοποιείται σε ΜΗΔΕΝ pixels: το
# #8000FF είναι βιολετί, τα βουνά είναι σταχτο-λιλά, και η κοντινότερη πένα
# τους είναι το γκρι. Πέντε από τις δεκαέξι πένες μου ήταν ουσιαστικά νεκρές.
#
# ΕΝΤΑΣΗ. Με το μάτι προτιμούσα 0,35: οι επίπεδες περιοχές έμεναν καθαρές
# και φαινόταν «γνήσια οθόνη CPC». Αλλά «καθαρό» δεν είναι «πιστό» — στο
# 0,35 τα βουνά βγαίνουν ΕΠΙΠΕΔΑ ΓΚΡΙ και τα πρόσωπα χάνουν τον όγκο τους.
# Στο 1,00 το μοβ των βουνών εμφανίζεται επιτέλους, επειδή προκύπτει από
# ανακάτεμα γκρι με παστέλ μπλε — χρώμα που η παλέτα ΔΕΝ έχει αυτούσιο.
# Σε CRT, όπου το pixel του Mode 0 είναι διπλάσια φαρδύ και το φωσφόρο
# απλώνει, ανακατεύει ακόμα καλύτερα από ό,τι σε οθόνη LCD.
DITHER = 'fs'
FS_STRENGTH = 0.35

# Οι παλέτες είναι υπολογισμένες από το `choose_palette` και γραμμένες εδώ
# για να μην ξανατρέχει 40 δευτερόλεπτα σε κάθε build. Το `--check-palette`
# τις ξαναβγάζει και επιβεβαιώνει ότι δεν ξέφυγαν.
#
# Οι δύο εικόνες είναι η ΙΔΙΑ σκηνή με μία αλλαγή (ο χορευτής έγινε drone),
# οπότε οι παλέτες τους βγαίνουν ανεξάρτητα και συγκρίνονται: αν διαφέρουν,
# η διαφορά είναι πραγματική και όχι τύχη του διαλέκτη.
PICTURES = {
    # Ασπρόμαυρη. Οι ΜΟΝΟΙ ουδέτεροι τόνοι του CPC είναι αυτοί οι τρεις:
    # #000000, #808080, #FFFFFF. Τέταρτος δεν υπάρχει — ό,τι κι αν βάλεις
    # έχει ορατή απόχρωση (#8080FF μπλε, #FFFF80 κίτρινο). Το Mode 1 σηκώνει
    # τέσσερις πένες· η τέταρτη μένει αχρησιμοποίητη και παίρνει μαύρο.
    'panigiri': dict(
        src='panigiri_source.jpg', mode=2, grey=True,
        palette=[0, 26], dither='fs', strength=1.0,
    ),
    'panigiri_drone': dict(
        src='panigiri_drone_source.jpg', mode=0,
        palette=[0, 1, 3, 4, 9, 10, 12, 13, 14, 15, 16, 17, 22, 23, 25, 26],
    ),
}


def dist(a, b):
    return sum(w * (p - q) ** 2 for w, p, q in zip(WEIGHT, a, b)) ** 0.5


# ------------------------------------------------------- μνήμη οθόνης

def offset(x, y, mode):
    return (y & 7) * 0x800 + (y >> 3) * ROW_BYTES + x // MODES[mode]['ppb']


assert offset(0, 0, 0) == 0
assert offset(0, 1, 0) == 0x800, 'η επόμενη γραμμή είναι +#800'
assert offset(0, 8, 0) == ROW_BYTES, 'κάθε 8 γραμμές γυρνάει στην αρχή +80'
assert offset(159, 199, 0) == 16335, 'Mode 0: η τελευταία ορατή θέση'
assert offset(319, 199, 1) == 16335, 'Mode 1: η ίδια τελευταία θέση'
assert offset(1, 0, 0) == 0 and offset(2, 0, 0) == 1, 'Mode 0: 2 pixels το byte'
assert offset(3, 0, 1) == 0 and offset(4, 0, 1) == 1, 'Mode 1: 4 pixels το byte'
assert offset(639, 199, 2) == 16335, 'Mode 2: η ίδια τελευταία θέση'
assert offset(7, 0, 2) == 0 and offset(8, 0, 2) == 1, 'Mode 2: 8 pixels το byte'


# ---------------------------------------------------------- εξαγωγή

# Πόσο ανεβαίνει η ΤΟΠΙΚΗ αντίθεση πριν τον κβαντισμό.
#
# Χωρίς αυτό, τα πρόσωπα εξαφανίζονται. Δεκαπέντε κεφάλια στη σειρά, το καθένα
# ~20 pixels φαρδύ, και όλα τους σε παρόμοιο μεσαίο τόνο: ο κβαντισμός τα
# ισοπεδώνει σε μία γκρι μάζα και η σκηνή χάνει το θέμα της. Το unsharp mask
# ανεβάζει τη διαφορά ΑΝΑΜΕΣΑ σε γειτονικά pixels χωρίς να πειράζει τη
# συνολική φωτεινότητα, οπότε μάτια, μουστάκια και περιγράμματα επιβιώνουν.
#
# Καθολική αντίθεση (ImageEnhance.Contrast) ΔΕΝ κάνει τη δουλειά: ανοίγει τα
# φώτα και κλείνει τις σκιές, αλλά τα πρόσωπα είναι όλα στον ίδιο μεσαίο τόνο
# και μένουν ίδια μεταξύ τους.
# Όσο λιγότερες πένες, τόσο πιο δυνατό πρέπει να είναι. Σε 1 bit (Mode 2) ένα
# πρόσωπο είναι ~12 pixels ψηλό και ο μεσαίος τόνος του γίνεται πεδίο θορύβου
# 50/50 — εκεί που ο dither κάνει τον χειρότερο θόρυβο. Το unsharp το σπρώχνει
# μακριά από το 50% και τα χαρακτηριστικά επιβιώνουν.
UNSHARP = {
    0: dict(radius=1.6, percent=160, threshold=2),
    1: dict(radius=1.6, percent=160, threshold=2),
    2: dict(radius=2.5, percent=260, threshold=1),
}

# Καθολική αντίθεση, ΜΕΤΑ το unsharp. Στο 1 bit βοηθάει επιπλέον: απλώνει τους
# μεσαίους τόνους προς τα άκρα, όπου ο dither έχει λιγότερο να επινοήσει.
CONTRAST = {0: 1.0, 1: 1.0, 2: 1.4}


def load(src, mode=0, grey=False, sharpen=True):
    """Η πηγή σε 160x200 RGB.

    LANCZOS: η εικόνα σμικρύνεται 12,5 φορές και χρειάζεται φίλτρο που κρατάει
    ακμές. Με BOX οι λεπτομέρειες (πρόσωπα, σημαία, γράμματα) γίνονταν λάσπη.
    """
    im = Image.open(os.path.join(OUT, src)).convert('RGB')
    w = MODES[mode]['w']
    assert abs(im.size[0] / im.size[1] - 320.0 / H) < 0.02, \
        'η πηγή %s δεν έχει τον λόγο της οθόνης (%.3f)' % (im.size, 320.0 / H)
    small = im.resize((w, H), Image.LANCZOS)
    if sharpen:
        small = small.filter(ImageFilter.UnsharpMask(**UNSHARP[mode]))
    if grey:
        # Πρώτα σε φωτεινότητα, ΜΕΤΑ κβαντισμός. Αν αφήσεις το χρώμα και
        # αφήσεις την απόσταση να διαλέξει ανάμεσα σε γκρι, το κόκκινο και το
        # μπλε του ίδιου τόνου καταλήγουν σε διαφορετικό γκρι: η φωτογραφία
        # βγαίνει με λάθος τόνους εκεί που η πηγή είχε κορεσμένα χρώματα.
        # Τα βάρη είναι τα φωτομετρικά, όχι ο μέσος όρος.
        small = small.convert('L')
        if CONTRAST[mode] != 1.0:
            small = ImageEnhance.Contrast(small).enhance(CONTRAST[mode])
        small = small.convert('RGB')
    return [[small.getpixel((x, y)) for x in range(w)] for y in range(H)]


# ----------------------------------------------------------- παλέτα

def bucket(hist, step=16):
    out = {}
    for (r, g, b), w in hist.items():
        k = (r // step * step, g // step * step, b // step * step)
        out[k] = out.get(k, 0) + w
    return out


def choose_palette(pix, n=16):
    """Τα n καλύτερα firmware χρώματα για αυτή την εικόνα.

    ΔΕΝ αποφασίζει την παλέτα που γράφεται στο δίσκο — μετράει μόνο πόσο
    μακριά είναι η επιλεγμένη από το αριθμητικό βέλτιστο. Το γιατί είναι στο
    σχόλιο του `PALETTE` παραπάνω: περίμενα ότι εδώ, με μεγάλες επιφάνειες
    αντί για εικονίδια 32x32, ο διαλέκτης θα ήταν το σωστό εργαλείο. Δεν
    ήταν — ξοδεύει τέσσερις πένες σε χρώματα που δεν εξυπηρετούν κανένα pixel.
    """
    hist = {}
    for row in pix:
        for p in row:
            hist[p] = hist.get(p, 0) + 1
    items = list(bucket(hist).items())
    cand = list(range(27))

    def cost(sel):
        pal = [cpcimg.FW_RGB[i] for i in sel]
        return sum(w * min(dist(p, q) for q in pal) for p, w in items)

    sel = []
    while len(sel) < n:
        sel.append(min((i for i in cand if i not in sel),
                       key=lambda i: cost(sel + [i])))
    improved = True
    while improved:
        improved = False
        base = cost(sel)
        for k in range(len(sel)):
            for i in cand:
                if i in sel:
                    continue
                trial = sel[:k] + [i] + sel[k + 1:]
                c = cost(trial)
                if c < base - 1e-9:
                    sel, base, improved = trial, c, True
    # Ταξινόμηση κατά ΑΡΙΘΜΟ firmware, όχι κατά φωτεινότητα: πολλά χρώματα
    # του CPC έχουν ίδιο άθροισμα RGB (#800000, #008000, #000080 ...) και η
    # ταξινόμηση κατά φωτεινότητα τα έβγαζε σε αυθαίρετη σειρά. Η σειρά ΕΙΝΑΙ
    # τα δεδομένα — ορίζει ποιος αριθμός πένας γράφεται σε κάθε pixel.
    return sorted(sel), hist


# -------------------------------------------------------- κβαντισμός

# Ο ordered dither του Mode 0 ΠΡΕΠΕΙ να έχει κελί 1 pixel x 2 γραμμές: το pixel
# του είναι διπλάσια φαρδύ από ψηλό, οπότε έτσι βγαίνει τετράγωνο στην οθόνη
# και δεν τρεμοπαίζει στην τηλεόραση.
BAYER = ((0, 2), (3, 1))


def nearest(p, pal):
    return min(range(len(pal)), key=lambda i: dist(p, pal[i]))


def quant_none(pix, pal, strength=0.0):
    return [[nearest(p, pal) for p in row] for row in pix]


def quant_ordered(pix, pal, strength=1.0):
    out = []
    for y, row in enumerate(pix):
        line = []
        for x, p in enumerate(row):
            t = (BAYER[(y // 2) % 2][x % 2] + 0.5) / 4.0
            order = sorted(range(len(pal)), key=lambda i: dist(p, pal[i]))
            a, b = order[0], order[1]
            pa, pb = pal[a], pal[b]
            ab = sum((q - u) ** 2 for u, q in zip(pa, pb))
            if ab == 0:
                line.append(a)
                continue
            f = sum((s - u) * (q - u) for s, u, q in zip(p, pa, pb)) / ab
            line.append(b if min(1.0, max(0.0, f)) > t else a)
        out.append(line)
    return out


def quant_fs(pix, pal, strength=FS_STRENGTH):
    """Floyd-Steinberg με φιδωτή σάρωση.

    Η διάχυση σφάλματος κερδίζει καθαρά σε ολόκληρη εικόνα: δεν έχει σταθερό
    μοτίβο, οπότε οι βαθμίδες (ουρανός, βουνά) βγαίνουν ομαλές αντί για
    ρίγες. Η φιδωτή σάρωση σβήνει το «σύρσιμο» προς τα δεξιά που αφήνει η
    μονόδρομη.

    Το `strength` κόβει λίγο τη διάχυση. Στο 1,0 το σφάλμα ταξιδεύει μακριά και
    σπέρνει μεμονωμένα φωτεινά pixels σε σκοτεινές περιοχές — σε 160x200 που
    θα το δεις μεγεθυσμένο x2 οριζόντια, φαίνονται. Στο 0,85 σβήνουν χωρίς να
    χαθούν οι βαθμίδες.
    """
    buf = [[list(map(float, p)) for p in row] for row in pix]
    w = len(pix[0])
    out = []
    for y in range(H):
        line = [0] * w
        xs = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        step = 1 if y % 2 == 0 else -1
        for x in xs:
            old = buf[y][x]
            i = nearest(old, pal)
            line[x] = i
            err = [(o - n) * strength for o, n in zip(old, pal[i])]
            for dx, dy, f in ((step, 0, 7 / 16), (-step, 1, 3 / 16),
                              (0, 1, 5 / 16), (step, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and ny < H:
                    for c in range(3):
                        buf[ny][nx][c] += err[c] * f
        out.append(line)
    return out


def quant_atkinson(pix, pal, strength=1.0):
    """Atkinson: σκορπάει μόνο τα 6/8 του σφάλματος, σε έξι γείτονες.

    Φτιάχτηκε για ασπρόμαυρες οθόνες ενός bit και είναι ακόμα ό,τι καλύτερο
    γι' αυτές. Κρατώντας το ένα τέταρτο του σφάλματος για τον εαυτό του, δεν
    «σέρνει» τους τόνους: τα λευκά μένουν λευκά και τα μαύρα μαύρα, οπότε τα
    πρόσωπα και τα περιγράμματα δεν λιώνουν σε ομοιόμορφο γκρι. Σε αντάλλαγμα
    χάνει λίγη πιστότητα στις μεγάλες βαθμίδες.
    """
    buf = [[list(map(float, p)) for p in row] for row in pix]
    w = len(pix[0])
    out = []
    for y in range(H):
        line = [0] * w
        for x in range(w):
            old = buf[y][x]
            i = nearest(old, pal)
            line[x] = i
            err = [(o - n) * strength / 8.0 for o, n in zip(old, pal[i])]
            for dx, dy in ((1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and ny < H:
                    for c in range(3):
                        buf[ny][nx][c] += err[c]
        out.append(line)
    return out


QUANT = {'none': quant_none, 'ordered': quant_ordered, 'fs': quant_fs,
         'atkinson': quant_atkinson}


# ------------------------------------------------------------- έξοδος

def to_screen(pens, mode):
    """pens -> 16384 bytes στη διάταξη της μνήμης οθόνης."""
    m = MODES[mode]
    ppb, pack = m['ppb'], m['pack']
    buf = bytearray(SCREEN)
    for y in range(H):
        row = pens[y]
        for x in range(0, m['w'], ppb):
            buf[offset(x, y, mode)] = pack(*row[x:x + ppb])
    return bytes(buf)


def verify(pens, scr, mode):
    """Διαβάζει ΟΛΗ την οθόνη πίσω σε pens και τη συγκρίνει.

    Οι ισχυρισμοί του cpcimg δένουν ήδη κωδικοποιητή και αποκωδικοποιητή· αυτό
    εδώ πιάνει το άλλο λάθος που κάνει κανείς εδώ — λάθος τύπο διεύθυνσης.
    """
    m = MODES[mode]
    ppb, unpack = m['ppb'], m['unpack']
    bad = 0
    for y in range(H):
        row = pens[y]
        for x in range(0, m['w'], ppb):
            got = unpack(scr[offset(x, y, mode)])
            bad += sum(1 for k in range(ppb) if got[k] != row[x + k])
    return bad


def preview(path, pens, pal_rgb, aspect=2, zoom=2):
    """PNG με ΣΩΣΤΗ αναλογία: κάθε pixel 2 φορές φαρδύτερο από ψηλό.

    Το zoom είναι 2 και όχι 4 επίτηδες. Στο 4 κάθε pixel του CPC γίνεται
    συμπαγές πλακίδιο 8x4 και ο dither φαίνεται σαν θόρυβος — κάτι που ΔΕΝ
    συμβαίνει ούτε στην πραγματική κλίμακα ούτε σε CRT. Με προειδοποίησε: στο
    x4 ήμουν έτοιμος να ρίξω την ένταση του dither για να «καθαρίσει» μια
    εικόνα που δεν ήταν βρόμικη.
    """
    # Όλοι οι τρόποι γεμίζουν την ΙΔΙΑ οθόνη. Σχεδιάζοντας πάντα σε 640x400,
    # κάθε pixel βγαίνει (640/w) x 2 και κανένα δεν χάνεται: Mode 0 -> 4x2,
    # Mode 1 -> 2x2, Mode 2 -> 1x2. Έτσι οι τρεις συγκρίνονται δίκαια.
    w = len(pens[0])
    im = Image.new('RGB', (w, H))
    im.putdata([pal_rgb[p] for row in pens for p in row])
    im.resize((640, 400), Image.NEAREST).save(path)


def preview_crt(path, pens, pal_rgb, aspect=2):
    """Πώς δείχνει σε οθόνη καθοδικού σωλήνα, κατά προσέγγιση.

    Το φωσφόρο απλώνει και το pixel του Mode 0 είναι διπλάσια φαρδύ, οπότε ο
    dither ανακατεύεται πολύ περισσότερο από ό,τι σε LCD. Δεν είναι
    προσομοίωση — είναι υπενθύμιση ότι η σκληρή εικόνα του LCD δεν είναι ο
    προορισμός.
    """
    w = len(pens[0])
    im = Image.new('RGB', (w, H))
    im.putdata([pal_rgb[p] for row in pens for p in row])
    im.resize((1280, 800), Image.NEAREST) \
      .resize((640, 400), Image.LANCZOS).save(path)


def sheet(path, pens, pal_rgb):
    """Το ακατέργαστο 160x200 με παλέτα, για Aseprite."""
    w = len(pens[0])
    im = Image.new('P', (w, H))
    flat = []
    for rgb in pal_rgb:
        flat += list(rgb)
    im.putpalette(flat + [0] * (768 - len(flat)))
    px = im.load()
    for y in range(H):
        for x in range(w):
            px[x, y] = pens[y][x]
    im.save(path)


def write_palette(key, sel, mode=0):
    lines = ['GIMP Palette', 'Name: %s CPC Mode %d' % (key, mode), 'Columns: 4',
             '# Τα %d pens, από τα 27 χρώματα του firmware.' % len(sel),
             '# Η στήλη FW είναι ο αριθμός για INK / SCR SET INK.', '#']
    for pen, fw in enumerate(sel):
        r, g, b = cpcimg.FW_RGB[fw]
        lines.append('%3d %3d %3d\tpen %02d  FW %02d  %s'
                     % (r, g, b, pen, fw, cpcimg.FW_NAMES[fw]))
    with open(os.path.join(OUT, key + '_palette.gpl'), 'w') as f:
        f.write('\n'.join(lines) + '\n')

    # Εναλλακτικός δρόμος χωρίς assembler: η ίδια οθόνη από BASIC.
    basic = ['10 MODE %d' % mode, '20 BORDER %d' % sel[0]]
    n = 30
    for pen, fw in enumerate(sel):
        basic.append('%d INK %d,%d' % (n, pen, fw))
        n += 10
    basic += ['%d LOAD "%s.SCR",&C000' % (n, key[:8].upper()),
              '%d CALL &BB06' % (n + 10),
              '%d CALL &0000' % (n + 20)]
    with open(os.path.join(OUT, key + '_loader.bas.txt'), 'w') as f:
        f.write('\n'.join(basic) + '\n')


def write_asm(key, sel, mode=0):
    """Ο loader. Βάζει την παλέτα με SCR SET INK, που δέχεται αριθμούς FIRMWARE.

    ΟΧΙ απευθείας στον Gate Array. Οι τιμές υλικού είναι άλλος πίνακας και δεν
    τον επαλήθευσα ολόκληρο — πέντε σημεία του συμφωνούσαν με τις πηγές, αλλά
    πέντε στα είκοσι επτά δεν είναι επαλήθευση. Η κλήση firmware παίρνει τους
    ίδιους αριθμούς που γράφει το `palette.gpl` και το `icons`-στυλ json, άρα
    δεν υπάρχει δεύτερος πίνακας να ξεστρατίσει.
    """
    lines = [
        '; %s.asm — ολόκληρη οθόνη Mode %d για Amstrad CPC 6128' % (key, mode),
        '; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από src/make_screen.py — μην το πειράζεις.',
        ';',
        '; Δείχνει την εικόνα και περιμένει πλήκτρο. Τα δεδομένα είναι ήδη στη',
        '; διάταξη της μνήμης οθόνης, οπότε η εμφάνιση είναι ένα LDIR.',
        '',
        'SCR_SET_MODE  equ #BC0E',
        'SCR_SET_INK   equ #BC32',
        'SCR_SET_BORDER equ #BC38',
        'KM_WAIT_CHAR  equ #BB06',
        '',
        '    org #4000',
        '    run start',
        '',
        'start:',
        '    ld a,%d' % mode,
        '    call SCR_SET_MODE          ; Mode %d, %dx200, %d pens'
        % (mode, MODES[mode]['w'], MODES[mode]['pens']),
        '',
        '    ld hl,inks',
        '    ld e,0                     ; e = αριθμός pen',
        'ink_loop:',
        '    ld a,(hl)',
        '    ld b,a',
        '    ld c,a                     ; b=c -> σταθερό χρώμα, χωρίς flashing',
        '    ld a,e',
        '    push hl',
        '    push de',
        '    call SCR_SET_INK',
        '    pop de',
        '    pop hl',
        '    inc hl',
        '    inc e',
        '    ld a,e',
        '    cp %d' % len(sel),
        '    jr nz,ink_loop',
        '',
        '    ld a,(inks)                ; το border στο ίδιο με το pen 0',
        '    ld b,a',
        '    ld c,a',
        '    call SCR_SET_BORDER',
        '',
        '    ld hl,picture              ; η οθόνη, έτοιμη',
        '    ld de,#C000',
        '    ld bc,#4000',
        '    ldir',
        '',
        '    call KM_WAIT_CHAR          ; μένει ώσπου να πατήσεις πλήκτρο',
        '    jp #0000                   ; και μετά reset',
        '',
        'inks:',
        '    db ' + ','.join(str(f) for f in sel)
        + '   ; firmware numbers, pen 0..%d' % (len(sel) - 1),
        '',
        'picture:',
        '    incbin "%s.scr"' % key,
        '',
    ]
    with open(os.path.join(OUT, key + '.asm'), 'w') as f:
        f.write('\n'.join(lines))


# ------------------------------------------------------------ σύγκριση

def compare(pix, pal_rgb):
    """Τα τρία dither δίπλα-δίπλα, σε κομμάτι με ουρανό, πρόσωπα και γρασίδι."""
    x0, y0, w, h = 40, 40, 80, 100
    zoom = 3
    im = Image.new('RGB', (3 * w * 2 * zoom + 40, h * zoom + 20), (18, 18, 24))
    px = im.load()
    for k, name in enumerate(('none', 'ordered', 'fs')):
        pens = QUANT[name](pix, pal_rgb)
        ox = 10 + k * (w * 2 * zoom + 10)
        for y in range(h):
            for x in range(w):
                c = pal_rgb[pens[y0 + y][x0 + x]]
                for dy in range(zoom):
                    for dx in range(2 * zoom):
                        px[ox + x * 2 * zoom + dx, 10 + y * zoom + dy] = c
    path = os.path.join(TMP, 'dither_compare.png')
    im.save(path)
    print('χωρίς dither | ordered 1x2 | Floyd-Steinberg  ->', path)


def perceived(pix, pens, pal_rgb, radius=1.2):
    """Σφάλμα όπως το βλέπει το μάτι: θολώνει και τα δύο, μετά συγκρίνει.

    Χωρίς τη θόλωση κάθε μέτρηση λέει ότι ο dither είναι χειρότερος από το
    τίποτα, επειδή μετράει κάθε pixel χωριστά — ενώ ο dither δουλεύει ακριβώς
    στο ότι το μάτι ΔΕΝ τα μετράει χωριστά.
    """
    w = len(pens[0])
    a = Image.new('RGB', (w, H))
    a.putdata([p for row in pix for p in row])
    b = Image.new('RGB', (w, H))
    b.putdata([pal_rgb[p] for row in pens for p in row])
    a = a.filter(ImageFilter.GaussianBlur(radius))
    b = b.filter(ImageFilter.GaussianBlur(radius))
    pa, pb = a.load(), b.load()
    tot = sum(dist(pa[x, y], pb[x, y]) for y in range(H) for x in range(w))
    return tot / (w * H) / sum(WEIGHT) ** 0.5


def build(key, cfg):
    mode = cfg.get('mode', 0)
    m = MODES[mode]
    pix = load(cfg['src'], mode, cfg.get('grey', False))
    quant = QUANT[cfg.get('dither', DITHER)]
    strength = cfg.get('strength', FS_STRENGTH)
    sel = cfg['palette']
    pal_rgb = [cpcimg.FW_RGB[i] for i in sel]
    hist = {}
    for row in pix:
        for p in row:
            hist[p] = hist.get(p, 0) + 1
    tot = sum(hist.values())
    err = sum(w * min(dist(p, q) for q in pal_rgb)
              for p, w in hist.items()) / tot / sum(WEIGHT) ** 0.5

    pens = quant(pix, pal_rgb, strength)
    scr = to_screen(pens, mode)
    bad = verify(pens, scr, mode)
    assert bad == 0, '%d pixels δεν γύρισαν σωστά από τη μνήμη οθόνης' % bad
    assert len(scr) == SCREEN

    with open(os.path.join(OUT, key + '.scr'), 'wb') as f:
        f.write(scr)
    sheet(os.path.join(OUT, '%s_mode%d.png' % (key, mode)), pens, pal_rgb)
    preview(os.path.join(OUT, key + '_preview.png'), pens, pal_rgb, m['aspect'])
    preview_crt(os.path.join(OUT, key + '_preview_crt.png'), pens, pal_rgb,
                m['aspect'])
    write_palette(key, sel, mode)
    write_asm(key, sel, mode)

    cnt = {}
    for row in pens:
        for p in row:
            cnt[p] = cnt.get(p, 0) + 1
    # Η παλέτα επιτρέπεται να έχει ΛΙΓΟΤΕΡΕΣ πένες από όσες σηκώνει ο τρόπος:
    # σε ασπρόμαυρο ο CPC έχει ακριβώς τρεις ουδέτερους τόνους (#000000,
    # #808080, #FFFFFF) και τίποτα να βάλεις τέταρτο δεν είναι ουδέτερο.
    dead = [i for i in range(len(sel)) if not cnt.get(i)]
    assert not dead, '%s: νεκρές πένες %s' % (key, dead)

    print('%s — %s, Mode %d (%dx%d, %d pens)'
          % (key, cfg['src'], mode, m['w'], H, m['pens']))
    print('   %d διαφορετικά χρώματα σε %d pixels' % (len(hist), tot))
    print('   παλέτα (firmware): %s' % ', '.join(str(f) for f in sel))
    print('   dither %s %.2f — σφάλμα %.2f/255 πριν, %.2f μετά'
          % (cfg.get('dither', DITHER), strength, err,
             perceived(pix, pens, pal_rgb)))
    print('   %d/%d πένες σε χρήση, η πιο σπάνια %.2f%%, %d bytes οθόνης'
          % (len(cnt), m['pens'], 100.0 * min(cnt.values()) / (m['w'] * H),
             len(scr)))
    return sel


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    keys = want or list(PICTURES)

    if '--check-palette' in sys.argv:
        for key in keys:
            cfg = PICTURES[key]
            mode = cfg.get('mode', 0)
            auto, _ = choose_palette(load(cfg['src'], mode),
                                     MODES[mode]['pens'])
            if cfg['palette'] is None:
                print('%-16s %s   <-- γράψ' "'" 'το στο PICTURES' % (key, auto))
            else:
                assert auto == cfg['palette'], \
                    '%s: ο διαλέκτης βγάζει τώρα %s' % (key, auto)
                print('%-16s συμφωνεί με τον διαλέκτη' % key)
        return

    if '--compare' in sys.argv:
        key = keys[0]
        cfg = PICTURES[key]
        compare(load(cfg['src']),
                [cpcimg.FW_RGB[i] for i in cfg['palette']])
        return

    pals = {}
    for key in keys:
        pals[key] = build(key, PICTURES[key])
    if len(pals) > 1 and len({PICTURES[k].get('mode', 0) for k in pals}) == 1:
        a, b = list(pals.values())[:2]
        same = sorted(set(a) & set(b))
        print('\nοι δύο παλέτες μοιράζονται %d/16 πένες' % len(same))
        for k, v in pals.items():
            only = sorted(set(v) - set(same))
            if only:
                print('   μόνο στο %s: %s' % (k, ', '.join(
                    '%d (%s)' % (f, cpcimg.FW_NAMES[f]) for f in only)))


if __name__ == '__main__':
    main()
