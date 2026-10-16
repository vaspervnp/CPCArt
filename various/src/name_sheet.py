"""Φύλλο ονοματοδοσίας: τα εξαγμένα εικονίδια, μεγεθυσμένα και αριθμημένα.

    python3 src/name_sheet.py pirate

Οι ετικέτες των σμικρυμένων φύλλων είναι ~3 pixels ψηλές και δεν διαβάζονται
με κανένα φίλτρο. Τα ονόματα για αυτά τα πακέτα βγαίνουν από την ΤΕΧΝΗ, και
αυτό εδώ είναι το εργαλείο που τη δείχνει αρκετά μεγάλη για να κριθεί.

Δεν γράφει τίποτα στα πακέτα — μόνο ένα PNG στο /tmp.
"""
import copy
import os
import sys

from PIL import Image, ImageDraw

import make_icons as M
import packs

TMP = os.environ.get('TMPDIR', '/tmp')
ZOOM = 4


def main():
    key = sys.argv[1]
    part = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    rows_per = int(sys.argv[3]) if len(sys.argv) > 3 else 99
    # Αντίγραφο: γεμίζουμε ΟΛΑ τα κελιά του πλέγματος με ονόματα-θέσεις, ακόμα
    # κι αν τα ονόματα του pack δεν συμφωνούν ακόμα σε πλήθος — αυτή ακριβώς
    # είναι η στιγμή που τρέχεις αυτό το εργαλείο. Το αντίγραφο υπάρχει για να
    # μη δει κανένα άλλο εργαλείο τα ψεύτικα ονόματα.
    pack = copy.copy(packs.BY_KEY[key])
    pack.names = ['%03d' % i for i in range(pack.rows * packs.GRID_W)]
    icons = M.extract(pack)

    cell = packs.SIZE * ZOOM
    cw, ch = cell + 8, cell + 20
    cols = packs.GRID_W
    r0 = part * rows_per
    rows = [r for r in range(r0, min(pack.rows, r0 + rows_per))]
    im = Image.new('RGB', (cols * cw + 8, len(rows) * ch + 26), (18, 18, 24))
    d = ImageDraw.Draw(im)
    d.text((8, 8), '%s — θέσεις %d..%d' % (pack.title, r0 * cols,
                                           (rows[-1] + 1) * cols - 1),
           fill=(255, 206, 92))
    for ri, r in enumerate(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(icons):
                continue
            _, g = icons[idx]
            ox, oy = 8 + c * cw, 26 + ri * ch
            for y in range(packs.SIZE):
                for x in range(packs.SIZE):
                    d.rectangle([ox + x * ZOOM, oy + y * ZOOM,
                                 ox + x * ZOOM + ZOOM - 1,
                                 oy + y * ZOOM + ZOOM - 1], fill=g[y][x])
            d.text((ox + 2, oy + cell + 4), '%d' % idx, fill=(255, 206, 92))
    path = os.path.join(TMP, 'names_%s_%d.png' % (key, part))
    im.save(path)
    print(path)


if __name__ == '__main__':
    main()
