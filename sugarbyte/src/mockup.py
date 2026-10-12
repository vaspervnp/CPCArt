"""Μία πλήρης οθόνη CPC 160x200: ταμπλό 8x8 αριστερά, HUD δεξιά.

Υπάρχει για να κριθεί το σύνολο, όχι τα κομμάτια: αν τα έξι χρώματα δεν
ξεχωρίζουν σε μία οθόνη, δεν ξεχωρίζουν πουθενά.
"""
from cpcgfx import CW, CH, HW, HH, PEN_GREY, PEN_HI, PEN_JELLY, PEN_LINE, \
                   PEN_MASK, blank, stamp

SCREEN_W, SCREEN_H = 160, 200
COLS, ROWS = 8, 8
BOARD_X, BOARD_Y = 0, 4                 # 8 x 12 = 96 pixels, 8 x 24 = 192 γραμμές
HUD_X = BOARD_X + COLS * CW             # 96 -> μένουν 64 pixels για το HUD

COLOUR_KEY = {'r': 0, 'o': 1, 'y': 2, 'g': 3, 'b': 4, 'p': 5}

# Το χρώμα κάθε candy. Η τελεία είναι άδειο κελί — στα μπλοκαρισμένα κελιά
# (γλάσο, σοκολάτα, γλυκόριζα) ΔΕΝ κάθεται candy, όπως στο Candy Crush.
COLOUR = """
royg..ro
ygbproyg
bpyoryg.
gybproy.
oygb..p.
pryg.oyb
gbp.oygb
ygbproyg
"""

# Η μορφή του: κανονικό, ριγέ, περιτύλιγμα, βόμβα, υλικά.
FORM = """
...h....
..w.....
........
....v...
........
........
..*.....
.c....n.
"""

# Το κελί κάτω από το candy. Η τελεία παίρνει τη σκακιέρα μόνη της.
CELLS = """
........
..JJ....
..JK...3
..KK...2
....CC.1
.....C..
...L....
........
"""
CELL_KEY = {'J': 'jelly1', 'K': 'jelly2', '1': 'icing1', '2': 'icing2',
            '3': 'icing3', 'C': 'chocolate', 'L': 'licorice', 'o': 'hole'}

# Ό,τι μπαίνει ΠΑΝΩ από το candy.
OVER = """
....23..
.......m
..G.....
.+......
........
HHHHH...
........
.......s
"""
OVER_KEY = {'G': 'cage', 'm': 'marmalade', '+': 'cursor1',
            'H': 'beam_h1', 'V': 'beam_v1', '1': 'pop1', '2': 'pop2',
            '3': 'pop3', '4': 'pop4', 's': 'star2'}


def _grid(text):
    return [ln.strip() for ln in text.strip('\n').splitlines()]


def _by_name(s):
    return {n: s.frames[i] for i, n in enumerate(s.names)}


def _candy_name(colour_ch, form_ch):
    """(χρώμα, μορφή) -> (δείκτης tag, όνομα καρέ) του candy sheet."""
    if form_ch == '*':
        return 'bomb', 'colour_bomb'
    if form_ch == 'c':
        return 'ingredient', 'cherry'
    if form_ch == 'n':
        return 'ingredient', 'nut'
    tag = {'.': 'plain', 'h': 'striped_h', 'v': 'striped_v',
           'w': 'wrapped'}[form_ch]
    return tag, None


def hud_text(img, text, x, y, hud_glyphs):
    """Γράφει ψηφία και σύμβολα με τα κελιά 4x8 του HUD."""
    names = {':': 'colon', '/': 'slash', 'x': 'times', '+': 'plus'}
    for ch in text:
        if ch != ' ':
            key = 'digit_' + ch if ch.isdigit() else names.get(ch)
            if key and key in hud_glyphs:
                stamp(img, hud_glyphs[key], x, y)
        x += HW
    return x


def draw_board(img, candy, cells, overlay):
    cand, cell, over = _by_name(candy), _by_name(cells), _by_name(overlay)
    gc, gf, gl, go = _grid(COLOUR), _grid(FORM), _grid(CELLS), _grid(OVER)
    for ry in range(ROWS):
        for rx in range(COLS):
            px, py = BOARD_X + rx * CW, BOARD_Y + ry * CH

            key = gl[ry][rx]
            if key in CELL_KEY:
                name = CELL_KEY[key]
            else:
                name = 'plain' if (rx + ry) % 2 == 0 else 'plain_alt'
            stamp(img, cell[name], px, py)

            cch, fch = gc[ry][rx], gf[ry][rx]
            if cch != '.' or fch in '*cn':
                tag, frame = _candy_name(cch, fch)
                if frame is None:
                    idx = candy.frames_of(tag)[COLOUR_KEY[cch]]
                    frame = candy.names[idx]
                    stamp(img, candy.frames[idx], px, py)
                else:
                    stamp(img, cand[frame], px, py)

            if go[ry][rx] in OVER_KEY:
                stamp(img, over[OVER_KEY[go[ry][rx]]], px, py)
    return img


def draw_hud(img, candy, hud):
    glyphs, cand = _by_name(hud), _by_name(candy)
    x0, w = HUD_X, SCREEN_W - HUD_X

    for y in range(SCREEN_H):                       # φόντο ταμπλό HUD
        for x in range(x0, SCREEN_W):
            img[y][x] = PEN_LINE
    for y in range(SCREEN_H):                       # η ραφή με το ταμπλό
        img[y][x0] = PEN_GREY
    for x in range(x0, SCREEN_W):
        img[2][x] = img[SCREEN_H - 3][x] = PEN_GREY

    stamp(img, glyphs['star'], x0 + 3, 8)           # πόντοι
    hud_text(img, '028450', x0 + 11, 8, glyphs)

    stamp(img, glyphs['moves'], x0 + 3, 22)         # κινήσεις
    hud_text(img, '24', x0 + 11, 22, glyphs)
    stamp(img, glyphs['time'], x0 + 35, 22)
    hud_text(img, '1:40', x0 + 43, 22, glyphs)

    for x in range(x0 + 3, SCREEN_W - 3):           # χωρίστρα
        img[36][x] = PEN_GREY

    goals = [('red', 'plain', '12'), ('green', 'plain', '08'),
             ('blue', 'striped_h', '03')]
    for i, (colour, tag, count) in enumerate(goals):      # στόχοι πίστας
        y = 42 + i * 30
        idx = candy.frames_of(tag)[COLOUR_KEY[colour[0] if colour != 'green' else 'g']]
        stamp(img, candy.frames[idx], x0 + 4, y)
        hud_text(img, 'x' + count, x0 + 20, y + 8, glyphs)

    for x in range(x0 + 3, SCREEN_W - 3):
        img[136][x] = PEN_GREY
    for i in range(3):                              # τα τρία αστέρια του πίστας
        g = glyphs['star'] if i < 2 else glyphs['goal']
        stamp(img, g, x0 + 10 + i * 16, 144)
    hud_text(img, '04/08', x0 + 10, 160, glyphs)
    return img


def screen(candy, cells, overlay, hud):
    img = blank(SCREEN_W, SCREEN_H, PEN_MASK)
    draw_board(img, candy, cells, overlay)
    draw_hud(img, candy, hud)
    return img
