"""Catalogue previews: pieces drawn at 2:1 pixel aspect with labels."""
from cpcgfx import Canvas, compose, TW, TH

BG = (28, 28, 36)
GRID = (60, 60, 76)
LABEL = (220, 220, 230)
GROUP = (255, 200, 90)


def catalogue(bank, groups, path, scale=2, max_w=1400, title=None):
    """groups: [(group title, [(label, grid of tile idx)])]. Each Mode 0 pixel = 2s x s."""
    sx, sy = 2 * scale, scale
    tw, th = TW * sx, TH * sy                    # on-screen tile size (square)
    pad, lab = 10, 8 * scale
    # layout pass
    items, x, y, row_h = [], pad, pad, 0
    if title:
        y += 7 * scale + pad
    for gtitle, entries in groups:
        if x != pad:
            x, y, row_h = pad, y + row_h + pad, 0
        items.append(('group', gtitle, x, y))
        y += 7 * scale + 4
        for label, grid in entries:
            w, h = len(grid[0]) * tw, len(grid) * th
            box_w = max(w, (len(label) * 4 - 1) * max(1, scale // 2 + 1) // 1)
            if x + box_w > max_w - pad and x != pad:
                x, y, row_h = pad, y + row_h + pad, 0
            items.append(('piece', label, x, y, grid))
            x += box_w + pad * 2
            row_h = max(row_h, lab + h)
        x, y, row_h = pad, y + row_h + pad * 2, 0
    total_h = y + pad
    cv = Canvas(max_w, total_h, BG)
    if title:
        cv.text(title, pad, pad, scale + 1, GROUP)
    ls = max(1, scale // 2 + 1)
    for it in items:
        if it[0] == 'group':
            cv.text(it[1], it[2], it[3], scale, GROUP)
            continue
        _, label, x, y, grid = it
        cv.text(label, x, y, ls, LABEL)
        img = compose(bank, grid)
        gy = y + lab
        cv.rect(x - 1, gy - 1, len(grid[0]) * tw + 2, len(grid) * th + 2, GRID)
        cv.blit_pens(img, x, gy, sx, sy)
    cv.save(path)
    return cv


def tile_sheet_preview(bank, path, cols=8, scale=3, gap=2):
    """Every tile with its index, 2:1 aspect."""
    sx, sy = 2 * scale, scale
    tw, th = TW * sx, TH * sy
    n = len(bank.tiles)
    rows = (n + cols - 1) // cols
    gap = max(gap, 6)
    cell_w, cell_h = tw + gap, th + gap + 12
    cv = Canvas(cols * cell_w + gap, rows * cell_h + gap, BG)
    for i, t in enumerate(bank.tiles):
        x = gap + (i % cols) * cell_w
        y = gap + (i // cols) * cell_h
        cv.text(str(i), x, y, 2, LABEL)
        cv.blit_pens([list(r) for r in t], x, y + 12, sx, sy)
    cv.save(path)
