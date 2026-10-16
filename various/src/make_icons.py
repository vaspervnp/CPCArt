"""Τα δέκα πακέτα εικονιδίων -> εκδόσεις Mode 0 και Mode 1 του Amstrad CPC.

    python3 src/make_icons.py            # όλα
    python3 src/make_icons.py pirate     # ένα

Η γεωμετρία, τα ονόματα και οι παλέτες είναι στο `packs.py`. Εδώ είναι μόνο η
μηχανή: εξαγωγή, κβαντισμός, κωδικοποίηση, επαλήθευση, έξοδος.

ΟΙ ΔΥΟ ΓΕΩΜΕΤΡΙΕΣ ΕΞΟΔΟΥ

    Mode 1  32x32 pixels, 4 pens,  4 pixels/byte  -> 8 bytes x 32 = 256
    Mode 0  16x32 pixels, 16 pens, 2 pixels/byte  -> 8 bytes x 32 = 256

Και τα δύο βγαίνουν **τετράγωνα στην οθόνη** και πιάνουν **ίδια bytes**. Το
Mode 0 είναι 16 pixels φαρδύ και όχι 32 επειδή το pixel του είναι διπλάσια
φαρδύ από ψηλό: 16 x 2 = 32 μονάδες, όσο και οι 32 γραμμές. Στα 32 θα έβγαινε
εικονίδιο διπλάσιου πλάτους από ύψος.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import cpcimg
import packs
from packs import CARD_RGB, PAGE_RGB, CARD0, CARD_STEP, CARD_IN, SCALE
from packs import GRID_W, SIZE, FULL_W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)

DITHER = True
DITHER_BAND = 0.30

# Πόσο μακριά από το χρώμα της κάρτας μετράει ακόμα για φόντο. Στα πλήρη φύλλα
# η σύγκριση είναι ακριβής· στα σμικρυμένα το φόντο έχει θολώσει σε δεκάδες
# αποχρώσεις και χρειάζεται ανοχή — αλλά μικρή, αλλιώς τρώει τα σκούρα μπλε
# του ίδιου του εικονιδίου.
BG_TOL = 42.0

# Βάρη για την απόσταση χρωμάτων: το μάτι βλέπει πιο πολύ το πράσινο.
WEIGHT = (2.0, 4.0, 3.0)


def dist(a, b):
    """Σταθμισμένη ΕΥΚΛΕΙΔΕΙΑ απόσταση, όχι τετραγωνική.

    Με τετραγωνική, pens φεύγουν σε αποχρώσεις που καλύπτουν κλάσματα του τοις
    εκατό: το τετράγωνο κυνηγάει τις ακραίες τιμές και αγοράζει «ασφάλεια» για
    λίγα παράξενα pixels αντί να πυκνώσει εκεί που είναι η μάζα.
    """
    return sum(w * (p - q) ** 2 for w, p, q in zip(WEIGHT, a, b)) ** 0.5


# ------------------------------------------------------------- εξαγωγή

def extract(pack):
    """-> [(όνομα, πλέγμα 32x32 από RGB)].

    Για `full` η μεγέθυνση είναι «πλησιέστερου γείτονα», οπότε δειγματοληψία
    στο κέντρο κάθε κελιού επιστρέφει ΑΚΡΙΒΩΣ το αυθεντικό pixel. Για `thumb`
    το αυθεντικό δεν υπάρχει πια: παίρνουμε μέσο όρο επιφάνειας, που είναι ό,τι
    καλύτερο βγαίνει από 25 θολά pixels για 32 θέσεις.
    """
    im = Image.open(os.path.join(OUT, pack.src)).convert('RGB')
    s = 1.0 if pack.kind == 'full' else im.size[0] / float(FULL_W)
    x0b, y0b = CARD0[0] * s, CARD0[1] * s
    step, inset, sc = CARD_STEP * s, CARD_IN * s, SCALE * s
    px = im.load() if pack.kind == 'full' else None
    icons = []
    for idx, name in enumerate(pack.names):
        r, c = divmod(idx, GRID_W)
        ox, oy = x0b + step * c + inset, y0b + step * r + inset
        if pack.kind == 'full':
            ox, oy = int(round(ox)), int(round(oy))
            grid = [[px[ox + int(sc * i + sc / 2), oy + int(sc * j + sc / 2)]
                     for i in range(SIZE)] for j in range(SIZE)]
        else:
            box = (ox, oy, ox + SIZE * sc, oy + SIZE * sc)
            cell = im.resize((SIZE, SIZE), Image.BOX, box=box)
            cp = cell.load()
            grid = [[cp[i, j] for i in range(SIZE)] for j in range(SIZE)]
        icons.append((name, grid))
    return icons


def make_is_bg(pack):
    if pack.kind == 'full':
        return lambda p: p == CARD_RGB or p == PAGE_RGB
    return lambda p: min(dist(p, CARD_RGB), dist(p, PAGE_RGB)) < BG_TOL


# ------------------------------------------------------------- παλέτα

def histogram(icons, is_bg):
    hist = {}
    for _, grid in icons:
        for row in grid:
            for p in row:
                if not is_bg(p):
                    hist[p] = hist.get(p, 0) + 1
    return hist


def bucket(hist, step=32):
    """Στρογγυλοποιεί τα χρώματα σε πλέγμα `step` ανά κανάλι.

    Μόνο για την ΑΝΑΖΗΤΗΣΗ παλέτας. Μια σμικρυμένη πηγή βγάζει 15.000+
    διαφορετικά χρώματα επειδή το θόλωμα γέμισε τα ενδιάμεσα, και ο διαλέκτης
    γίνεται δεκάδες φορές πιο αργός χωρίς να αλλάζει απάντηση: τα 27 χρώματα
    του firmware απέχουν 128 μεταξύ τους. Το σφάλμα που ΑΝΑΦΕΡΕΤΑΙ μετριέται
    πάντα στο πραγματικό ιστόγραμμα, όχι σε αυτό.

    Το 32 είναι μετρημένο, όχι μαντεμένο (πακέτο `candy`, 12.967 χρώματα):

        βήμα  8   3371 ομάδες   68,3 s   βέλτιστο 35,50
        βήμα 16   1156 ομάδες   29,5 s   βέλτιστο 35,50
        βήμα 32    270 ομάδες    7,6 s   βέλτιστο 35,53   <-- εδώ
        βήμα 48    132 ομάδες    2,0 s   βέλτιστο 35,88

    Στο 48 αρχίζει να ξεφεύγει. Στο 32 η διαφορά είναι 0,03 σε έναν αριθμό που
    είναι ούτως ή άλλως διαγνωστικός, για εννιαπλάσια ταχύτητα.
    """
    out = {}
    for (r, g, b), w in hist.items():
        k = (r // step * step, g // step * step, b // step * step)
        out[k] = out.get(k, 0) + w
    return out


def choose_palette(hist, n, forced=(0,)):
    """Τα n καλύτερα firmware χρώματα για αυτά τα pixels.

    Άπληστη επιλογή και μετά τοπική αναζήτηση με ανταλλαγές: με 27 υποψήφιους η
    εξαντλητική είναι εκτός συζήτησης (C(27,16) ~ 13 εκατομμύρια) αλλά η
    ανταλλαγή συγκλίνει σε λίγα περάσματα. ΔΕΝ αποφασίζει αυτή την παλέτα που
    γράφεται στο δίσκο — μετράει μόνο πόσο μακριά είναι η επιλεγμένη από το
    αριθμητικό βέλτιστο. Το γιατί είναι στο `packs.py`.
    """
    cand = list(range(27))
    items = list(bucket(hist).items())

    def cost(sel):
        pal = [cpcimg.FW_RGB[i] for i in sel]
        return sum(w * min(dist(p, q) for q in pal) for p, w in items)

    sel = list(forced)
    while len(sel) < n:
        sel.append(min((i for i in cand if i not in sel),
                       key=lambda i: cost(sel + [i])))
    improved = True
    while improved:
        improved = False
        base = cost(sel)
        for k in range(len(forced), len(sel)):
            for i in cand:
                if i in sel:
                    continue
                trial = sel[:k] + [i] + sel[k + 1:]
                c = cost(trial)
                if c < base - 1e-9:
                    sel, base, improved = trial, c, True
    return sorted(sel, key=lambda i: sum(cpcimg.FW_RGB[i]))


# ------------------------------------------------------- κβαντισμός

# Ο dither του Mode 0 ΠΡΕΠΕΙ να έχει κελί 1 pixel x 2 γραμμές: το pixel του
# είναι διπλάσια φαρδύ από ψηλό, οπότε έτσι βγαίνει τετράγωνο στην οθόνη και
# δεν τρεμοπαίζει στην τηλεόραση. Στο Mode 1 τα pixels είναι ήδη τετράγωνα.
BAYER = {
    0: ((0, 2), (3, 1)),                      # 2x2, κελί 1px x 2 γραμμές
    1: ((0, 8, 2, 10), (12, 4, 14, 6),        # 4x4, κελί 1px x 1 γραμμή
        (3, 11, 1, 9), (15, 7, 13, 5)),
}


def _threshold(mode, x, y):
    m = BAYER[mode]
    n = len(m)
    cell = m[(y // 2) % n][x % n] if mode == 0 else m[y % n][x % n]
    return (cell + 0.5) / (n * n)


def _pair(src, pal_rgb, memo):
    """(κοντινότερη, δεύτερη, θέση του src ανάμεσά τους) — με μνήμη.

    Είναι το ακριβό κομμάτι: ταξινόμηση 16 πενών ανά pixel, 692 εικονίδια επί
    δύο τρόπους. Τα χρώματα όμως επαναλαμβάνονται πολύ, οπότε η μνήμη το κόβει
    σε κλάσμα. Το κλειδί είναι στρογγυλεμένο στο 1/256 — δεν χάνεται τίποτα,
    οι τιμές εισόδου είναι ήδη μέσοι όροι ακεραίων.

    Η μνήμη δίνεται απ' έξω, ΑΝΑ ΠΑΛΕΤΑ (`memo_for`). Πρώτη εκδοχή είχε μία
    μνήμη με την παλέτα μέσα στο κλειδί· σωστό, αλλά κατακερμάτιζε 16 τριάδες
    σε κάθε pixel και η κατασκευή έγινε τρεις φορές πιο αργή. Ένα αναγνωριστικό
    παλέτας αντί για την ίδια την παλέτα θα ήταν παγίδα: το `try_palettes.py`
    δοκιμάζει δεκάδες παλέτες στη σειρά και θα μοιράζονταν αποτελέσματα.
    """
    key = (round(src[0]), round(src[1]), round(src[2]))
    hit = memo.get(key)
    if hit is not None:
        return hit
    order = sorted(range(len(pal_rgb)), key=lambda i: dist(src, pal_rgb[i]))
    a, b = order[0], order[1]
    pa, pb = pal_rgb[a], pal_rgb[b]
    ab = sum((q - p) ** 2 for p, q in zip(pa, pb))
    if ab == 0:
        out = (a, a, 0.0)
    else:
        f = sum((s - p) * (q - p) for s, p, q in zip(src, pa, pb)) / ab
        out = (a, b, min(1.0, max(0.0, f)))
    memo[key] = out
    return out


_MEMOS = {}


def memo_for(pal_rgb):
    """Η μνήμη αυτής της παλέτας. Κατακερματίζεται μία φορά ανά εικονίδιο."""
    m = _MEMOS.get(pal_rgb)
    if m is None:
        m = _MEMOS[pal_rgb] = {}
    return m


def _dither_pen(src, pal_rgb, t, memo):
    """Διαλέγει ανάμεσα στις δύο κοντινότερες πένες με ordered dither.

    Χωρίς αυτό, ένα μεσαίο καφέ όπως το #7A4A2C πέφτει ολόκληρο είτε στο
    #800000 είτε στο #FF8000 και ο χαλκός γίνεται ή αίμα ή πορτοκάλι.
    """
    a, b, f = _pair(src, pal_rgb, memo)
    if a == b:
        return a
    # ΠΟΤΕ dither μέσα ή έξω από το pen 0. Το pen 0 δεν είναι μια απόχρωση σαν
    # τις άλλες: είναι ΚΑΙ το φόντο. Ανακατεύοντάς το με μια διπλανή σκούρα
    # πένα, ο dither τρυπάει την τέχνη — τα περιγράμματα γέμιζαν στίγματα και
    # τα σκούρα αντικείμενα (οψιδιανός, μαύρη κόμπρα) διαλύονταν σε σκόνη.
    # Το κοντινότερο pen ολόκληρο δίνει συμπαγές σκοτάδι, που είναι το σωστό.
    if a == 0 or b == 0:
        return a
    # Ανακάτεμα ΜΟΝΟ στη μεσαία ζώνη. Χωρίς αυτό ο dither έπιανε και τα
    # περιγράμματα και τις μονοπίξελες ανταύγειες: τα εικονίδια γίνονταν
    # σκακιέρα και η σιλουέτα τους χανόταν. Σε 32x32 το μάτι δεν «σβήνει» τον
    # θόρυβο όπως σε μια μεγάλη εικόνα.
    if f <= DITHER_BAND:
        return a
    if f >= 1.0 - DITHER_BAND:
        return b
    g = (f - DITHER_BAND) / (1.0 - 2.0 * DITHER_BAND)
    return b if g > t else a


def quantise(grid, pal_rgb, width, is_bg, mode=None, dither=False):
    """32x32 RGB -> width x 32 pens.

    Για width 16 κάθε pixel εξόδου καλύπτει δύο της πηγής και διαλέγεται η πένα
    που ελαχιστοποιεί το ΑΘΡΟΙΣΜΑ των δύο σφαλμάτων — όχι ο μέσος όρος τους,
    που θα έφτιαχνε χρώματα που δεν υπάρχουν πουθενά στην πηγή.
    """
    # Η παλέτα μπαίνει στο κλειδί της μνήμης του `_pair`, άρα πρέπει να είναι
    # hashable. Μία φορά εδώ, όχι σε κάθε pixel.
    pal_rgb = tuple(pal_rgb)
    memo = memo_for(pal_rgb)
    step = SIZE // width
    out = []
    for y, row in enumerate(grid):
        line = []
        for x in range(width):
            src = [row[x * step + k] for k in range(step)]
            if all(is_bg(p) for p in src):
                line.append(0)
                continue
            src = [p for p in src if not is_bg(p)] or src
            mix = tuple(sum(p[c] for p in src) / len(src) for c in range(3))
            if dither:
                line.append(_dither_pen(mix, pal_rgb,
                                        _threshold(mode, x, y), memo))
            else:
                line.append(min(range(len(pal_rgb)),
                                key=lambda i: sum(dist(p, pal_rgb[i]) for p in src)))
        out.append(line)
    return out


# ------------------------------------------------------------- έξοδος

def sheet_png(path, icons_pens, w, h, pal_rgb, cols=GRID_W):
    rows = (len(icons_pens) + cols - 1) // cols
    im = Image.new('P', (cols * w, rows * h))
    flat = []
    for rgb in pal_rgb:
        flat += list(rgb)
    im.putpalette(flat + [0] * (768 - len(flat)))
    px = im.load()
    for i, (_, pens) in enumerate(icons_pens):
        ox, oy = (i % cols) * w, (i // cols) * h
        for y in range(h):
            for x in range(w):
                px[ox + x, oy + y] = pens[y][x]
    im.save(path)


def preview_png(path, icons_pens, w, h, pal_rgb, aspect, scale, title):
    sx, sy = aspect * scale, scale
    cw, ch = w * sx + 14, h * sy + 20
    cols = GRID_W
    rows = (len(icons_pens) + cols - 1) // cols
    im = Image.new('RGB', (cols * cw + 10, rows * ch + 34), (20, 20, 28))
    d = ImageDraw.Draw(im)
    d.text((10, 10), title, fill=(255, 206, 92))
    for i, (name, pens) in enumerate(icons_pens):
        ox = 10 + (i % cols) * cw
        oy = 30 + (i // cols) * ch
        d.rectangle([ox - 1, oy - 1, ox + w * sx, oy + h * sy], outline=(60, 60, 76))
        for y in range(h):
            for x in range(w):
                d.rectangle([ox + x * sx, oy + y * sy,
                             ox + x * sx + sx - 1, oy + y * sy + sy - 1],
                            fill=pal_rgb[pens[y][x]])
        d.text((ox, oy + h * sy + 3), name[:16], fill=(205, 205, 215))
    im.save(path)


ASM_HEAD = """; %s_mode%d.asm — %s, Amstrad CPC Mode %d
; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από src/make_icons.py — μην το πειράζεις με το χέρι.
;
; %d εικονίδια, %d x %d pixels το καθένα (%d x 32 μονάδες οθόνης — τετράγωνα),
; %d bytes ανά γραμμή, %d bytes ανά εικονίδιο. Δεδομένα γραμμικά, γραμμή-γραμμή,
; ΟΧΙ στη διάταξη της μνήμης οθόνης. Αδιαφανή: το pen 0 είναι το φόντο, οπότε
; μάσκα βγαίνει με ένα πέρασμα αν τη χρειαστείς.
;
;       διεύθυνση = %s_gfx + δείκτης * ICON_SZ
;
; Η παλέτα είναι στο palette_mode%d.gpl και στο icons.json· τα firmware numbers
; μπαίνουν με SCR SET INK ή κατευθείαν στον Gate Array.
"""


def write_asm_bin(pack, mode, icons_pens, w, h, outdir):
    row_bytes = w // cpcimg.MODES[mode]['px_per_byte']
    size = row_bytes * h
    blob = bytearray()
    key = pack.key
    lines = [ASM_HEAD % (key, mode, pack.title, mode, len(icons_pens), w, h,
                         w * cpcimg.MODES[mode]['aspect'], row_bytes, size,
                         key, mode),
             '',
             'ICON_W         equ %-5d ; bytes ανά γραμμή' % row_bytes,
             'ICON_H         equ %-5d ; γραμμές' % h,
             'ICON_SZ        equ %-5d ; bytes ανά εικονίδιο' % size,
             'ICON_N         equ %-5d ; εικονίδια' % len(icons_pens), '']
    for i, (name, _) in enumerate(icons_pens):
        lines.append('ico_%-22s equ %d' % (name, i))
    lines += ['', '%s_gfx:' % key]
    for i, (name, pens) in enumerate(icons_pens):
        data = cpcimg.encode(pens, mode)
        assert len(data) == size
        blob += data
        lines.append('  ; %3d %s' % (i, name))
        for r in range(0, len(data), 16):
            lines.append('  db ' + ','.join('#%02X' % b for b in data[r:r + 16]))
    lines.append('')
    with open(os.path.join(outdir, '%s_mode%d.bin' % (key, mode)), 'wb') as f:
        f.write(blob)
    with open(os.path.join(outdir, '%s_mode%d.asm' % (key, mode)), 'w') as f:
        f.write('\n'.join(lines))
    return blob


def verify(mode, icons_pens, w, h, blob):
    """Αποκωδικοποιεί ολόκληρο το blob πίσω σε pens και το συγκρίνει.

    Οι ισχυρισμοί του cpcimg δένουν ήδη κωδικοποιητή και αποκωδικοποιητή· αυτό
    εδώ πιάνει τα ΑΛΛΑ λάθη — λάθος βήμα γραμμής, λάθος σειρά εικονιδίων,
    μισό καρέ γραμμένο δύο φορές.
    """
    unpack = cpcimg.mode0_pens if mode == 0 else cpcimg.mode1_pens
    n = cpcimg.MODES[mode]['px_per_byte']
    row_bytes, bad, off = w // n, 0, 0
    for _, pens in icons_pens:
        for y in range(h):
            got = []
            for b in blob[off + y * row_bytes:off + (y + 1) * row_bytes]:
                got += list(unpack(b))
            bad += sum(1 for a, c in zip(got, pens[y]) if a != c)
        off += row_bytes * h
    assert off == len(blob), 'καταναλώθηκαν %d από %d bytes' % (off, len(blob))
    return bad


def write_gpl(pack, mode, sel, outdir):
    out = ['GIMP Palette', 'Name: %s CPC Mode %d' % (pack.title, mode),
           'Columns: 4',
           '# Τα %d pens του Mode %d, από τα 27 χρώματα του firmware.'
           % (len(sel), mode),
           '# Η στήλη FW είναι ο αριθμός για SCR SET INK / Gate Array.', '#']
    for pen, fw in enumerate(sel):
        r, g, b = cpcimg.FW_RGB[fw]
        out.append('%3d %3d %3d\tpen %02d  FW %02d  %s'
                   % (r, g, b, pen, fw, cpcimg.FW_NAMES[fw]))
    with open(os.path.join(outdir, 'palette_mode%d.gpl' % mode), 'w') as f:
        f.write('\n'.join(out) + '\n')


# --------------------------------------------------------------- οδήγηση

def build(pack):
    outdir = os.path.join(OUT, pack.key)
    os.makedirs(outdir, exist_ok=True)
    is_bg = make_is_bg(pack)

    icons = extract(pack)
    colours = [len({p for row in g for p in row}) for _, g in icons]
    if pack.kind == 'full':
        # Σε σωστό πλέγμα πάνω σε πηγή «πλησιέστερου γείτονα» κάθε εικονίδιο
        # βγάζει λίγα χρώματα. Αν ξεφύγει, το πλέγμα δεν κουμπώνει.
        assert max(colours) <= 48, \
            '%s: ώς %d χρώματα ανά εικονίδιο — το πλέγμα δεν κουμπώνει' \
            % (pack.key, max(colours))

    hist = histogram(icons, is_bg)
    tot = sum(hist.values())
    doc = {'source': pack.src, 'source_kind': pack.kind,
           'title': pack.title, 'count': len(icons),
           'names': [n for n, _ in icons], 'modes': {}}
    if pack.kind == 'thumb':
        doc['source_warning'] = (
            'Η πηγή είναι σμικρυμένη στο 0,2253 του αυθεντικού φύλλου: το '
            '32x32 σώζεται σε ~25x25 θολά pixels. Με το φύλλο των 1540 px το '
            'αποτέλεσμα βγαίνει καθαρότερο — άλλαξε μόνο το kind σε full.')

    report = []
    for mode, width in ((0, 16), (1, 32)):
        npens = cpcimg.MODES[mode]['pens']
        sel = pack.palettes[mode]
        assert len(sel) == npens
        pal_rgb = tuple(cpcimg.FW_RGB[i] for i in sel)
        pens = [(n, quantise(g, pal_rgb, width, is_bg, mode, DITHER))
                for n, g in icons]
        err = sum(w * min(dist(p, q) for q in pal_rgb) for p, w in hist.items())
        rms = err / tot / sum(WEIGHT) ** 0.5

        sheet_png(os.path.join(outdir, '%s_mode%d_sheet.png' % (pack.key, mode)),
                  pens, width, SIZE, pal_rgb)
        preview_png(os.path.join(outdir, 'preview_mode%d.png' % mode),
                    pens, width, SIZE, pal_rgb, cpcimg.MODES[mode]['aspect'], 3,
                    '%s — Amstrad CPC Mode %d, %d pens, %dx%d pixels'
                    % (pack.title, mode, npens, width, SIZE))
        blob = write_asm_bin(pack, mode, pens, width, SIZE, outdir)
        write_gpl(pack, mode, sel, outdir)
        bad = verify(mode, pens, width, SIZE, blob)
        assert bad == 0, '%s Mode %d: %d pixels δεν γύρισαν σωστά' \
                         % (pack.key, mode, bad)

        auto = [cpcimg.FW_RGB[i] for i in choose_palette(hist, npens)]
        aerr = sum(w * min(dist(p, q) for q in auto) for p, w in hist.items())
        arms = aerr / tot / sum(WEIGHT) ** 0.5

        # Εικονίδια που μένουν σχεδόν κενά. Το pen 0 είναι ΚΑΙ το φόντο, οπότε
        # ένα μαύρο αντικείμενο (οψιδιανός, μαύρη κόμπρα, σκιά) γίνεται τρύπα.
        # Στο Mode 1 με 4 πένες συμβαίνει πιο συχνά. Δεν είναι λάθος — είναι
        # όριο — αλλά ο χρήστης πρέπει να το ξέρει πριν τα βάλει σε παιχνίδι.
        faint = [n for n, pg in pens
                 if sum(1 for r in pg for p in r if p) < 0.10 * width * SIZE]

        doc['modes'][str(mode)] = {
            'faint': faint,
            'pixels': {'w': width, 'h': SIZE},
            'screen_units': {'w': width * cpcimg.MODES[mode]['aspect'], 'h': SIZE},
            'pens': npens, 'bytes_per_icon': len(blob) // len(icons),
            'total_bytes': len(blob),
            'mean_error_255': round(rms, 1),
            'numeric_optimum_255': round(arms, 1),
            'palette': [{'pen': p, 'firmware': fw, 'name': cpcimg.FW_NAMES[fw],
                         'rgb': '#%02X%02X%02X' % cpcimg.FW_RGB[fw]}
                        for p, fw in enumerate(sel)],
        }
        report.append((mode, npens, width, len(blob) // len(icons), len(blob),
                       rms, arms))

    with open(os.path.join(outdir, 'icons.json'), 'w') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    return len(icons), len(hist), tot, max(colours), report


def main():
    want = sys.argv[1:]
    chosen = [packs.BY_KEY[k] for k in want] if want else packs.PACKS
    grand = 0
    for pack in chosen:
        n, ncol, tot, worst, report = build(pack)
        print('%s — %s, %d εικονίδια, πηγή %s' %
              (pack.key, pack.title, n, pack.kind))
        print('   %d διαφορετικά χρώματα, %d pixels τέχνης, ώς %d ανά εικονίδιο'
              % (ncol, tot, worst))
        for mode, npens, width, per, total, rms, arms in report:
            print('   Mode %d: %2d pens, %2dx%d, %3d bytes/εικονίδιο, %6d σύνολο,'
                  ' σφάλμα %.1f/255 (βέλτιστο %.1f)'
                  % (mode, npens, width, SIZE, per, total, rms, arms))
            grand += total
    print('\nσύνολο %d bytes σε %d πακέτα' % (grand, len(chosen)))


if __name__ == '__main__':
    main()
