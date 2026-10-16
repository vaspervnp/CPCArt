"""Τα 75 εικονίδια steampunk -> εκδόσεις Mode 0 και Mode 1 του Amstrad CPC.

    python3 src/make_icons.py

Η πηγή (`steampunk.png`) είναι **contact sheet**, όχι τα αυθεντικά αρχεία: τα
εικονίδια είναι ζωγραφισμένα ×3,5 μέσα σε κάρτες 141×141 με ετικέτες από κάτω.
Η μεγέθυνση είναι «πλησιέστερου γείτονα», άρα δειγματοληψία στο κέντρο κάθε
κελιού επιστρέφει **ακριβώς** το αυθεντικό pixel — το επαληθεύει ο έλεγχος
παρακάτω, που μετράει πόσα χρώματα βγαίνουν ανά εικονίδιο (πρέπει να είναι
λίγα· σε θολωμένη πηγή θα ήταν εκατοντάδες).

ΟΙ ΔΥΟ ΓΕΩΜΕΤΡΙΕΣ

    Mode 1  32x32 pixels, 4 pens,  4 pixels/byte  -> 8 bytes x 32 = 256
    Mode 0  16x32 pixels, 16 pens, 2 pixels/byte  -> 8 bytes x 32 = 256

Και τα δύο βγαίνουν **τετράγωνα στην οθόνη** και πιάνουν **ίδια bytes**. Το
Mode 0 είναι 16 pixels φαρδύ και όχι 32 επειδή το pixel του είναι διπλάσια
φαρδύ από ψηλό: 16 x 2 = 32 μονάδες, όσο και οι 32 γραμμές.
"""
import json
import os

from PIL import Image, ImageDraw

import cpcimg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.join(OUT, 'steampunk.png')

# Η γεωμετρία του contact sheet, μετρημένη και όχι υποτιθέμενη.
CARD0, CARD_STEP, CARD_IN, SCALE = (24, 90), 150, 14, 3.5
GRID_W, GRID_H, SIZE = 10, 8, 32
DITHER = True
DITHER_BAND = 0.30

NAMES = """
gear_copper gear_brass gear_iron gear_gold gear_silver gear_bronze
gear_small_copper gear_small_brass gear_pair gear_trio
cog_rim spring piston pipe_straight pipe_elbow pipe_tee valve pressure_gauge
boiler chimney
steam_cloud rivet_plate chain pulley cogwheel_crown wrench hammer screwdriver
pliers spanner_double
oil_can blowtorch welding_mask toolbox measuring_tape calipers magnifying_lens
compass_brass telescope sextant
hourglass_brass goggles_brass top_hat bowler_hat aviator_cap leather_gloves
corset_vest boots_riveted pocket_watch monocle
cravat umbrella mechanical_arm jetpack wings_clockwork airship hot_air_balloon
locomotive train_wheel submarine
automaton clockwork_key music_box telegraph typewriter phonograph lamp_gas
lightning_coil tesla_orb energy_core
crystal_fuel coal_lump coal_bucket blueprint wooden_crate_brass
""".split()

# Το φόντο της κάρτας. Δεν είναι μέρος των εικονιδίων — γίνεται pen 0.
CARD_RGB = (0x38, 0x4C, 0x60)

# Οι παλέτες, σε firmware numbers. ΕΠΙΛΕΓΜΕΝΕΣ, όχι υπολογισμένες.
#
# Ο αυτόματος διαλέκτης (choose_palette) βρίσκει παλέτα με ελάχιστα μικρότερο
# σφάλμα — 107 έναντι 109 στο Mode 0 — αλλά ξοδεύει τέσσερα pens σε μωβ,
# πράσινο και παστέλ μπλε που μαζί καλύπτουν 0,9% των pixels, και αυτά τα
# ελάχιστα pixels πέφτουν σκόρπια πάνω στα περιγράμματα σαν σκόνη. Με 239
# χρώματα πηγής και κύβο 27 χρωμάτων, η ομοιόμορφη κατανομή ΕΙΝΑΙ βέλτιστη
# αριθμητικά και χειρότερη οπτικά. Τον κρατάμε για να μετράμε πόσο μακριά
# είμαστε από το αριθμητικό βέλτιστο.
PALETTES = {
    # Το λεξιλόγιο του steampunk: μπρούντζος, χαλκός, σίδερο, γυαλί, κρύσταλλο.
    0: [0,    # μαύρο — φόντο και περιγράμματα
        1,    # μπλε νύχτας — σκούρα σκιά
        3,    # μπορντό — σκούρος χαλκός
        12,   # λαδί — σκούρος μπρούντζος
        9,    # σκούρο πράσινο — κρύσταλλο
        10,   # σκούρο κυανό — γυαλί
        13,   # γκρι — σίδερο
        15,   # πορτοκαλί — χαλκός
        6,    # έντονο κόκκινο — βαμμένα μέρη
        24,   # έντονο κίτρινο — χρυσός
        18,   # έντονο πράσινο — κρύσταλλο
        20,   # έντονο κυανό — τέσλα, γυαλί
        11,   # γαλάζιο — σχέδιο
        16,   # ροζ — ζεστό φως
        25,   # χλωμό κίτρινο — ανταύγεια μπρούντζου
        26],  # λευκό — ανταύγειες, ασήμι
    # Με τέσσερα pens πρέπει να διαλέξεις ΤΙ ξεχωρίζει. Μπρούντζος από σίδερο
    # από ανταύγεια. Η αυτόματη έδινε μαύρο/μπορντό/γκρι/χλωμό χρυσό με σφάλμα
    # 127 έναντι 134, αλλά έβγαζε τα πάντα σκουριά: χωρίς πορτοκαλί δεν υπάρχει
    # μπρούντζος, και ο μπρούντζος είναι το μισό πακέτο.
    1: [0,    # μαύρο — φόντο και περιγράμματα
        15,   # πορτοκαλί — κάθε ζεστό μέταλλο και ξύλο
        13,   # γκρι — κάθε κρύο μέταλλο
        26],  # λευκό — ανταύγειες
}

# Βάρη για την απόσταση χρωμάτων: το μάτι βλέπει πιο πολύ το πράσινο.
WEIGHT = (2.0, 4.0, 3.0)


def dist(a, b):
    """Σταθμισμένη ΕΥΚΛΕΙΔΕΙΑ απόσταση, όχι τετραγωνική.

    Με τετραγωνική, τέσσερα pens πήγαιναν σε μωβ, πράσινο και παστέλ μπλε που
    μαζί κάλυπταν 0,9% των pixels: το τετράγωνο κυνηγάει τις ακραίες τιμές και
    αγοράζει «ασφάλεια» για λίγα παράξενα pixels αντί να πυκνώσει εκεί που
    είναι η μάζα — καφέ, μπρούντζος και γκρι.
    """
    return sum(w * (p - q) ** 2 for w, p, q in zip(WEIGHT, a, b)) ** 0.5


# ------------------------------------------------------------- εξαγωγή

def extract():
    im = Image.open(SRC).convert('RGB')
    px = im.load()
    icons = []
    for idx, name in enumerate(NAMES):
        r, c = divmod(idx, GRID_W)
        x0 = CARD0[0] + CARD_STEP * c + CARD_IN
        y0 = CARD0[1] + CARD_STEP * r + CARD_IN
        grid = [[px[x0 + int(SCALE * i + SCALE / 2), y0 + int(SCALE * j + SCALE / 2)]
                 for i in range(SIZE)] for j in range(SIZE)]
        icons.append((name, grid))
    return icons


# ------------------------------------------------------------- παλέτα

def histogram(icons):
    hist = {}
    for _, grid in icons:
        for row in grid:
            for p in row:
                if p != CARD_RGB:
                    hist[p] = hist.get(p, 0) + 1
    return hist


def choose_palette(hist, n, forced=(0,)):
    """Τα n καλύτερα firmware χρώματα για αυτά τα pixels.

    Άπληστη επιλογή και μετά τοπική αναζήτηση με ανταλλαγές: με 27 υποψήφιους
    η εξαντλητική είναι εκτός συζήτησης (C(27,16) ~ 13 εκατομμύρια) αλλά η
    ανταλλαγή συγκλίνει σε λίγα περάσματα.
    """
    cand = list(range(27))
    items = list(hist.items())

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
    cell = m[(y // (2 // (mode + 1))) % n][x % n] if mode == 0 else m[y % n][x % n]
    return (cell + 0.5) / (n * n)


def _dither_pen(src, pal_rgb, t):
    """Διαλέγει ανάμεσα στις δύο κοντινότερες πένες με ordered dither.

    Χωρίς αυτό, ένα μεσαίο καφέ όπως το #7A4A2C πέφτει ολόκληρο είτε στο
    #800000 είτε στο #FF8000 και το χαλκό γίνεται ή αίμα ή πορτοκάλι. Με τις
    δύο ανακατεμένες, το μάτι βλέπει το ενδιάμεσο.
    """
    order = sorted(range(len(pal_rgb)), key=lambda i: dist(src, pal_rgb[i]))
    a, b = order[0], order[1]
    pa, pb = pal_rgb[a], pal_rgb[b]
    ab = sum((q - p) ** 2 for p, q in zip(pa, pb))
    if ab == 0:
        return a
    # προβολή του src στο ευθύγραμμο τμήμα pa->pb
    f = sum((s - p) * (q - p) for s, p, q in zip(src, pa, pb)) / ab
    f = min(1.0, max(0.0, f))
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


def quantise(grid, pal_rgb, width, mode=None, dither=False):
    """32x32 RGB -> width x 32 pens. Για width 16 κάθε pixel εξόδου καλύπτει
    δύο της πηγής και διαλέγεται η πένα που ελαχιστοποιεί το ΑΘΡΟΙΣΜΑ των δύο
    σφαλμάτων — όχι ο μέσος όρος τους, που θα έφτιαχνε χρώματα που δεν υπάρχουν.
    """
    step = SIZE // width
    out = []
    for y, row in enumerate(grid):
        line = []
        for x in range(width):
            src = [row[x * step + k] for k in range(step)]
            if all(p == CARD_RGB for p in src):
                line.append(0)
                continue
            src = [p for p in src if p != CARD_RGB] or src
            mix = tuple(sum(p[c] for p in src) / len(src) for c in range(3))
            if dither:
                line.append(_dither_pen(mix, pal_rgb, _threshold(mode, x, y)))
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


ASM_HEAD = """; icons_mode%d.asm — Steampunk, Amstrad CPC Mode %d
; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από src/make_icons.py — μην το πειράζεις με το χέρι.
;
; %d εικονίδια, %d x %d pixels το καθένα (%d x 32 μονάδες οθόνης — τετράγωνα),
; %d bytes ανά γραμμή, %d bytes ανά εικονίδιο. Δεδομένα γραμμικά, γραμμή-γραμμή,
; ΟΧΙ στη διάταξη της μνήμης οθόνης. Αδιαφανή: το pen 0 είναι το φόντο, οπότε
; μάσκα βγαίνει με ένα πέρασμα αν τη χρειαστείς.
;
;       διεύθυνση = icons_gfx + δείκτης * ICON_SZ
;
; Η παλέτα είναι στο palette_mode%d.gpl και στο icons.json· τα firmware numbers
; μπαίνουν με SCR SET INK ή κατευθείαν στον Gate Array.
"""


def write_asm_bin(mode, icons_pens, w, h):
    row_bytes = w // cpcimg.MODES[mode]['px_per_byte']
    size = row_bytes * h
    blob = bytearray()
    lines = [ASM_HEAD % (mode, mode, len(icons_pens), w, h,
                         w * cpcimg.MODES[mode]['aspect'], row_bytes, size, mode),
             '',
             'ICON_W         equ %-5d ; bytes ανά γραμμή' % row_bytes,
             'ICON_H         equ %-5d ; γραμμές' % h,
             'ICON_SZ        equ %-5d ; bytes ανά εικονίδιο' % size,
             'ICON_N         equ %-5d ; εικονίδια' % len(icons_pens), '']
    for i, (name, _) in enumerate(icons_pens):
        lines.append('ico_%-18s equ %d' % (name, i))
    lines += ['', 'icons_gfx:']
    for i, (name, pens) in enumerate(icons_pens):
        data = cpcimg.encode(pens, mode)
        assert len(data) == size
        blob += data
        lines.append('  ; %3d %s' % (i, name))
        for r in range(0, len(data), 16):
            lines.append('  db ' + ','.join('#%02X' % b for b in data[r:r + 16]))
    lines.append('')
    with open(os.path.join(OUT, 'icons_mode%d.bin' % mode), 'wb') as f:
        f.write(blob)
    with open(os.path.join(OUT, 'icons_mode%d.asm' % mode), 'w') as f:
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


def write_gpl(mode, sel):
    out = ['GIMP Palette', 'Name: Steampunk CPC Mode %d' % mode, 'Columns: 4',
           '# Τα %d pens του Mode %d, από τα 27 χρώματα του firmware.' % (len(sel), mode),
           '# Η στήλη FW είναι ο αριθμός για SCR SET INK / Gate Array.', '#']
    for pen, fw in enumerate(sel):
        r, g, b = cpcimg.FW_RGB[fw]
        out.append('%3d %3d %3d\tpen %02d  FW %02d  %s' % (r, g, b, pen, fw, cpcimg.FW_NAMES[fw]))
    with open(os.path.join(OUT, 'palette_mode%d.gpl' % mode), 'w') as f:
        f.write('\n'.join(out) + '\n')


def main():
    icons = extract()
    colours = {len({p for row in g for p in row}) for _, g in icons}
    assert max(colours) <= 40, \
        'η εξαγωγή βγάζει ώς %d χρώματα ανά εικονίδιο — το πλέγμα δεν κουμπώνει' % max(colours)
    print('εξήχθησαν %d εικονίδια 32x32, ώς %d χρώματα το καθένα' % (len(icons), max(colours)))

    hist = histogram(icons)
    print('%d διαφορετικά χρώματα, %d pixels τέχνης' % (len(hist), sum(hist.values())))

    doc = {'source': 'steampunk.png (contact sheet x3.5)',
           'count': len(icons), 'names': [n for n, _ in icons], 'modes': {}}

    for mode, width in ((0, 16), (1, 32)):
        npens = cpcimg.MODES[mode]['pens']
        sel = PALETTES[mode]
        assert len(sel) == npens and len(set(sel)) == npens
        pal_rgb = [cpcimg.FW_RGB[i] for i in sel]
        pens = [(n, quantise(g, pal_rgb, width, mode, DITHER)) for n, g in icons]
        err = sum(w * min(dist(p, q) for q in pal_rgb) for p, w in hist.items())
        rms = err / sum(hist.values()) / sum(WEIGHT) ** 0.5

        sheet_png(os.path.join(OUT, 'steampunk_mode%d_sheet.png' % mode),
                  pens, width, SIZE, pal_rgb)
        preview_png(os.path.join(OUT, 'preview_mode%d.png' % mode), pens, width, SIZE,
                    pal_rgb, cpcimg.MODES[mode]['aspect'], 3,
                    'Steampunk — Amstrad CPC Mode %d, %d pens, %dx%d pixels'
                    % (mode, npens, width, SIZE))
        blob = write_asm_bin(mode, pens, width, SIZE)
        write_gpl(mode, sel)
        bad = verify(mode, pens, width, SIZE, blob)
        assert bad == 0, 'Mode %d: %d pixels δεν γύρισαν σωστά' % (mode, bad)

        doc['modes'][str(mode)] = {
            'pixels': {'w': width, 'h': SIZE},
            'screen_units': {'w': width * cpcimg.MODES[mode]['aspect'], 'h': SIZE},
            'pens': npens, 'bytes_per_icon': len(blob) // len(icons),
            'total_bytes': len(blob),
            'palette': [{'pen': p, 'firmware': fw, 'name': cpcimg.FW_NAMES[fw],
                         'rgb': '#%02X%02X%02X' % cpcimg.FW_RGB[fw]}
                        for p, fw in enumerate(sel)],
        }
        auto = [cpcimg.FW_RGB[i] for i in choose_palette(hist, npens)]
        aerr = sum(w * min(dist(p, q) for q in auto) for p, w in hist.items())
        print('Mode %d: %2d pens, %2dx%d pixels, %3d bytes/εικονίδιο, %5d σύνολο, '
              'μέσο σφάλμα %.1f/255 (αριθμητικό βέλτιστο %.1f)'
              % (mode, npens, width, SIZE, len(blob) // len(icons), len(blob),
                 rms, aerr / sum(hist.values()) / sum(WEIGHT) ** 0.5))

    with open(os.path.join(OUT, 'icons.json'), 'w') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    main()
