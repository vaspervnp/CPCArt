"""Δοκιμαστήριο παλετών: βγάζει υποψήφιες δίπλα-δίπλα για να κριθούν με το μάτι.

    python3 src/try_palettes.py pirate 1

Δεν γράφει τίποτα στα πακέτα — μόνο ένα PNG σύγκρισης στο /tmp. Υπάρχει επειδή
το αριθμητικό σφάλμα ΔΕΝ αρκεί για να διαλέξεις παλέτα: στο Mode 1 με 4 pens η
διαφορά ανάμεσα σε «διαβάζεται» και «κομφετί» δεν φαίνεται στον αριθμό.

Ο κανόνας που βγήκε από τις δοκιμές: τα τρία pens πέρα από το μαύρο πρέπει να
καλύπτουν την ΤΟΝΙΚΗ κλίμακα — έναν σκούρο μεσαίο, έναν ανοιχτό μεσαίο, μια
ανταύγεια. Τρεις κορεσμένες αποχρώσεις (π.χ. κόκκινο/μπλε/λευκό) αφήνουν τους
ενδιάμεσους τόνους χωρίς στέγη και ο dither τους σκορπάει σε κομφετί.
"""
import os
import sys

from PIL import Image, ImageDraw

import cpcimg
import make_icons as M
import packs

TMP = os.environ.get('TMPDIR', '/tmp')

# Υποψήφιες για Mode 1. Το pen 0 είναι πάντα μαύρο: φόντο και περιγράμματα.
CAND1 = {
    'steampunk (ζεστό/ουδέτερο/φως)': [0, 15, 13, 26],
    'γκρι + ώχρα': [0, 13, 25, 26],
    'μπλε + ώχρα': [0, 10, 25, 26],
    'μπλε + γκρι': [0, 2, 13, 26],
    'κόκκινο + γκρι': [0, 6, 13, 26],
    'λαδί + ώχρα': [0, 12, 25, 26],
    'μπορντό + ώχρα': [0, 3, 25, 26],
    'κόκκινο + ώχρα': [0, 6, 25, 26],
    'πορτοκαλί + κίτρινο': [0, 15, 24, 26],
    'μπλε + πορτοκαλί': [0, 10, 15, 26],
    'σκούρο μπλε + γκρι': [0, 1, 13, 26],
    'κόκκινο/μπλε/λευκό': [0, 6, 2, 26],
}

CAND0 = {}


def main():
    key = sys.argv[1]
    mode = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    pack = packs.BY_KEY[key]
    is_bg = M.make_is_bg(pack)
    icons = M.extract(pack)
    hist = M.histogram(icons, is_bg)
    tot = sum(hist.values())
    width = 32 if mode == 1 else 16
    aspect = cpcimg.MODES[mode]['aspect']

    cands = dict(CAND1 if mode == 1 else CAND0)
    cands['ΤΩΡΑ'] = pack.palettes[mode]
    auto = M.choose_palette(hist, cpcimg.MODES[mode]['pens'])
    cands['ΑΥΤΟΜΑΤΗ'] = auto

    # Δείγμα: τα πρώτα 12 και 12 από τη μέση, για ποικιλία θεμάτων.
    half = len(icons) // 2
    sample = icons[:12] + icons[half:half + 12]

    scale = 3
    sx, sy = aspect * scale, scale
    cw, ch = width * sx + 6, SIZE_H * sy + 6
    rows = len(cands)
    im = Image.new('RGB', (260 + len(sample) * cw, 24 + rows * ch),
                   (18, 18, 24))
    d = ImageDraw.Draw(im)
    d.text((8, 8), '%s — Mode %d, υποψήφιες παλέτες' % (pack.title, mode),
           fill=(255, 206, 92))
    for r, (label, sel) in enumerate(sorted(
            cands.items(), key=lambda kv: _err(kv[1], hist, tot))):
        pal_rgb = [cpcimg.FW_RGB[i] for i in sel]
        e = _err(sel, hist, tot)
        oy = 24 + r * ch
        d.text((8, oy + 6), '%-28s %.1f' % (label[:28], e), fill=(205, 205, 215))
        for c, (_, g) in enumerate(sample):
            pens = M.quantise(g, pal_rgb, width, is_bg, mode, M.DITHER)
            ox = 256 + c * cw
            for y in range(SIZE_H):
                for x in range(width):
                    d.rectangle([ox + x * sx, oy + y * sy,
                                 ox + x * sx + sx - 1, oy + y * sy + sy - 1],
                                fill=pal_rgb[pens[y][x]])
    path = os.path.join(TMP, 'pal_%s_mode%d.png' % (key, mode))
    im.save(path)
    print(path)
    for label, sel in sorted(cands.items(), key=lambda kv: _err(kv[1], hist, tot)):
        print('  %6.1f  %-28s %s' % (_err(sel, hist, tot), label, sel))


SIZE_H = 32


def _err(sel, hist, tot):
    pal = [cpcimg.FW_RGB[i] for i in sel]
    return sum(w * min(M.dist(p, q) for q in pal)
               for p, w in hist.items()) / tot / sum(M.WEIGHT) ** 0.5


if __name__ == '__main__':
    main()
