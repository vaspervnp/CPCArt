"""Πόσο κοστίζει η σμικρυμένη πηγή; Μετρημένο, όχι υποτιθέμενο.

    python3 src/cost_of_thumb.py

Εννιά από τα δέκα φύλλα έφτασαν σμικρυμένα στα 347 px. Το `lighthouse` έφτασε
ολόκληρο, οπότε μπορούμε να το **σμικρύνουμε εμείς** με τον ίδιο τρόπο και να
συγκρίνουμε την έξοδο με αυτήν της καθαρής πηγής. Είναι η μόνη ειλικρινής
απάντηση στο «αξίζει να βρεθούν τα πλήρη φύλλα;».

Βγάζει και PNG σύγκρισης στο /tmp.

ΤΟ ΑΠΟΤΕΛΕΣΜΑ, ΚΑΙ ΓΙΑΤΙ ΕΙΝΑΙ ΑΝΑΠΟΔΟ ΑΠΟ ΤΟ ΑΝΑΜΕΝΟΜΕΝΟ

Περίμενα το Mode 0 να τη γλιτώσει, επειδή με 16 στήλες χρειάζεται λιγότερη
οριζόντια πληροφορία από όση σώζεται στα 347 px. Βγαίνει το αντίθετο: το
Mode 0 αλλάζει ΠΙΟ ΠΟΛΥ. Οι 16 πένες του διακρίνουν αποχρώσεις που το θόλωμα
κατέστρεψε, ενώ οι 4 του Mode 1 είναι τόσο χοντρές που η μετατόπιση
στρογγυλεύει πίσω στην ίδια πένα.

Επίσης μετρημένο: η σμίκρυνση ΔΕΝ ξεθωριάζει τα χρώματα (κορεσμός -5%,
φωτεινότητα αμετάβλητη). Η ζημιά είναι χωρική, στις ακμές και στη λεπτομέρεια.
Γι' αυτό μια «ενίσχυση κορεσμού» ως διόρθωση δεν έχει νόημα — δοκιμάστηκε και
απορρίφθηκε με βάση αυτή τη μέτρηση.
"""
import colorsys
import copy
import os
import sys

from PIL import Image, ImageDraw

import cpcimg
import make_icons as M
import packs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
TMP = os.environ.get('TMPDIR', '/tmp')
THUMB_W = 347          # το πλάτος στο οποίο έφτασαν τα εννιά
PICK = [0, 6, 9, 18, 19, 22, 24, 34, 37, 43, 44, 54, 56, 63]


def make_thumb(pack, path):
    im = Image.open(os.path.join(OUT, pack.src)).convert('RGB')
    w, h = im.size
    im.resize((THUMB_W, int(round(h * THUMB_W / float(w)))),
              Image.LANCZOS).save(path)


def main():
    pack = packs.BY_KEY['lighthouse']
    assert pack.kind == 'full', 'το πείραμα θέλει πλήρη πηγή'
    thumb_path = os.path.join(TMP, 'lighthouse_thumb.png')
    make_thumb(pack, thumb_path)

    worse = copy.copy(pack)
    worse.src = os.path.relpath(thumb_path, OUT)
    worse.kind = 'thumb'

    clean, blur = M.extract(pack), M.extract(worse)
    is_c, is_b = M.make_is_bg(pack), M.make_is_bg(worse)

    # 1. Τι κάνει στα ίδια τα χρώματα
    cs = cl = ts = tl = 0.0
    n = same = 0
    for (_, gc), (_, gt) in zip(clean, blur):
        for rc, rt in zip(gc, gt):
            for pc, pt in zip(rc, rt):
                if is_c(pc):
                    continue
                _, l1, s1 = colorsys.rgb_to_hls(*[v / 255.0 for v in pc])
                _, l2, s2 = colorsys.rgb_to_hls(*[v / 255.0 for v in pt])
                cs += s1; cl += l1; ts += s2; tl += l2; n += 1
                same += pc == pt
    print('%d pixels τέχνης, ίδια ακριβώς %d (%.1f%%)' % (n, same, 100.0 * same / n))
    print('  κορεσμός     %.3f -> %.3f  (x%.3f)' % (cs / n, ts / n, ts / cs))
    print('  φωτεινότητα  %.3f -> %.3f  (x%.3f)' % (cl / n, tl / n, tl / cl))

    # 2. Τι κάνει στην ΕΞΟΔΟ, που είναι αυτό που μετράει
    Z = 5
    rows = []
    for mode, width in ((0, 16), (1, 32)):
        pal = tuple(cpcimg.FW_RGB[i] for i in pack.palettes[mode])
        diff = tot = 0
        for tag, icons, isb in (('A', clean, is_c), ('B', blur, is_b)):
            pens = [M.quantise(icons[i][1], pal, width, isb, mode, M.DITHER)
                    for i in PICK]
            rows.append(('M%d %s' % (mode, tag), tag, pal, width, pens))
        for (_, gc), (_, gt) in zip(clean, blur):
            a = M.quantise(gc, pal, width, is_c, mode, M.DITHER)
            b = M.quantise(gt, pal, width, is_b, mode, M.DITHER)
            for ra, rb in zip(a, b):
                for x, y in zip(ra, rb):
                    tot += 1
                    diff += x != y
        print('Mode %d: %d/%d pens διαφέρουν (%.1f%%)'
              % (mode, diff, tot, 100.0 * diff / tot))

    cw = 32 * Z + 6
    im = Image.new('RGB', (44 + len(PICK) * cw, 40 + len(rows) * (32 * Z + 22)),
                   (18, 18, 24))
    d = ImageDraw.Draw(im)
    d.text((8, 8), 'lighthouse: πλήρης πηγή 1540px (A) έναντι σμικρυμένης '
                   '%dpx (B)' % THUMB_W, fill=(255, 206, 92))
    for r, (label, tag, pal, width, pens) in enumerate(rows):
        oy = 34 + r * (32 * Z + 22)
        d.text((6, oy + 60), label,
               fill=(255, 206, 92) if tag == 'A' else (150, 150, 165))
        sx = Z * 32 // width
        for c, pg in enumerate(pens):
            ox = 44 + c * cw
            for y in range(32):
                for x in range(width):
                    d.rectangle([ox + x * sx, oy + y * Z,
                                 ox + x * sx + sx - 1, oy + y * Z + Z - 1],
                                fill=pal[pg[y][x]])
            if tag == 'B':
                d.text((ox, oy + 32 * Z + 4), clean[PICK[c]][0][:14],
                       fill=(205, 205, 215))
    path = os.path.join(TMP, 'clean_vs_thumb.png')
    im.save(path)
    print(path)


if __name__ == '__main__':
    main()
