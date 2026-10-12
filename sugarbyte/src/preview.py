"""Προεπισκοπήσεις: ό,τι βλέπουμε, το βλέπουμε σε αναλογία 2:1 όπως στο CPC."""
from cpcgfx import Canvas, RGB

BG    = (20, 20, 28)
CARD  = (38, 38, 50)
GRID  = (64, 64, 84)
LABEL = (214, 214, 226)
TITLE = (255, 206, 92)


def catalogue(sets_rows, path, scale=3, title=None, cols_max=1180, backdrop=None):
    """sets_rows: [(τίτλος ομάδας, [(ετικέτα, εικόνα)])]. 2 pixels φάρδος : 1 ύψος."""
    sx, sy = 2 * scale, scale
    pad, lab = 12, 7 * 2 + 4

    # πέρασμα διάταξης
    items, x, y, row_h = [], pad, pad, 0
    if title:
        y += 7 * 3 + pad
    for gtitle, entries in sets_rows:
        items.append(('group', gtitle, pad, y))
        y += 7 * 2 + 6
        x, row_h = pad, 0
        for label, img in entries:
            w, h = len(img[0]) * sx, len(img) * sy
            box = max(w, len(label) * 4 * 2) + pad
            if x + box > cols_max - pad and x != pad:
                x, y, row_h = pad, y + row_h + pad, 0
            items.append(('cell', label, x, y, img))
            x += box
            row_h = max(row_h, lab + h)
        y += row_h + pad + 6
    cv = Canvas(cols_max, y, BG)
    if title:
        cv.text(title, pad, pad, 3, TITLE)
    for it in items:
        if it[0] == 'group':
            cv.text(it[1], it[2], it[3], 2, TITLE)
            continue
        _, label, x, y, img = it
        cv.text(label, x, y, 2, LABEL)
        w, h = len(img[0]) * sx, len(img) * sy
        gy = y + lab
        cv.rect(x, gy, w, h, backdrop if backdrop else CARD)
        cv.frame(x - 1, gy - 1, w + 2, h + 2, GRID)
        cv.blit_pens(img, x, gy, sx, sy)
    cv.save(path)
    return cv


def set_catalogue(s, path, scale=3, title=None, backdrop=None):
    groups = []
    for tag, a, b in s.tag_ranges():
        groups.append((tag, [(s.names[i], s.frames[i]) for i in range(a, b + 1)]))
    return catalogue(groups, path, scale, title or s.name, backdrop=backdrop)


def sheet_png_preview(s, path, cols=8, scale=3):
    """Όλα τα καρέ με τον δείκτη τους — ο κατάλογος που κοιτάς όταν γράφεις κώδικα."""
    sx, sy = 2 * scale, scale
    fw, fh = s.w * sx, s.h * sy
    gap, lab = 8, 16
    rows = (len(s.frames) + cols - 1) // cols
    cv = Canvas(cols * (fw + gap) + gap, rows * (fh + gap + lab) + gap, BG)
    for i, f in enumerate(s.frames):
        x = gap + (i % cols) * (fw + gap)
        y = gap + (i // cols) * (fh + gap + lab)
        cv.text('%d %s' % (i, s.names[i][:9]), x, y, 2, LABEL)
        cv.rect(x, y + lab, fw, fh, CARD)
        cv.blit_pens(f, x, y + lab, sx, sy)
    cv.save(path)


def palette_strip(path, palette, scale=4):
    """Η παλέτα: pen, firmware number, χρήση."""
    cell = 26 * scale
    cv = Canvas(cell + 420, 16 * (cell // 2) + 16, BG)
    for i, p in enumerate(palette):
        y = 8 + i * (cell // 2)
        cv.rect(8, y, cell, cell // 2 - 2, RGB[i])
        cv.frame(8, y, cell, cell // 2 - 2, GRID)
        cv.text('%2d  FW%2d  %s' % (i, p[2], p[4]), cell + 20, y + 4, 2, LABEL)
    cv.save(path)
