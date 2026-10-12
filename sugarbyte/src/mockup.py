"""Μία πλήρης οθόνη CPC 160x200: ταμπλό 8x8 αριστερά, HUD δεξιά.

Υπάρχει για να κριθεί το σύνολο, όχι τα κομμάτια: αν τα έξι χρώματα δεν
ξεχωρίζουν σε μία οθόνη, δεν ξεχωρίζουν πουθενά.
"""
from cpcgfx import CW, CH, HW, HH, PEN_GREY, PEN_HI, PEN_JELLY, PEN_LINE, \
                   PEN_MASK, blank, stamp

# Οθόνη overscan 192x248 σε σελίδα 32 KB (CRTC R1=48, R6=31).
#   y   0.. 31  ο τίτλος, 192x32
#   y  32..223  το παιχνίδι: 16 pixels μπορντούρα, 160 παιχνίδι, 16 μπορντούρα
#   y 224..247  το πόδι, 192x24
# Τα 192 γραμμές του παιχνιδιού είναι ακριβώς 8 πλακάκια μπορντούρας των 24.
SCREEN_W, SCREEN_H = 192, 248
COLS, ROWS = 8, 8
TITLE_H, FOOT_H = 32, 24
BORDER_W = 16
BOARD_X, BOARD_Y = BORDER_W, TITLE_H    # 8 x 12 = 96 pixels, 8 x 24 = 192 γραμμές
HUD_X = BOARD_X + COLS * CW             # 112 -> μένουν 64 pixels για το HUD
HUD_Y, HUD_H = BOARD_Y, ROWS * CH

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


def _by_name(*sets):
    """Όνομα καρέ -> εικόνα, ενωμένα από όσα σετ δοθούν."""
    out = {}
    for s in sets:
        out.update({n: s.frames[i] for i, n in enumerate(s.names)})
    return out


def _by_set(sets):
    """Σύντομο όνομα σετ -> σετ. Τα σετ είναι πια εννιά και σε δύο blobs,
    οπότε η θέση τους στη λίστα δεν είναι συμβόλαιο — το όνομα είναι."""
    return {s.name.split('_')[0]: s for s in sets}


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


# Το πεζό 'x' είναι το σύμβολο του πολλαπλασιασμού, το κεφαλαίο 'X' το γράμμα:
# στο HUD γράφουμε «x12» και στο μενού «EXIT», και τα δύο με την ίδια ρουτίνα.
SYMBOL_NAMES = {':': 'colon', '/': 'slash', 'x': 'times', '+': 'plus'}


def hud_text(img, text, x, y, hud_glyphs):
    """Γράφει ψηφία, κεφαλαία και σύμβολα με τα κελιά 4x8 του HUD."""
    for ch in text:
        if ch != ' ':
            if ch.isdigit():
                key = 'digit_' + ch
            elif ch.isupper():
                key = 'letter_' + ch
            else:
                key = SYMBOL_NAMES.get(ch)
            if key and key in hud_glyphs:
                stamp(img, hud_glyphs[key], x, y)
        x += HW
    return x


def text_w(text):
    return len(text) * HW


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


def draw_border(img, title, border):
    """Ο τίτλος πάνω, κορδόνι ζαχαρωτού γύρω, ζαχαρωτά στις δύο κάτω γωνίες."""
    bd = _by_name(border)
    stamp(img, title.frames[0], 0, 0)
    for i in range(HUD_H // border.h):
        stamp(img, bd['edge_left'], 0, BOARD_Y + i * border.h)
        stamp(img, bd['edge_right'], SCREEN_W - BORDER_W, BOARD_Y + i * border.h)
    foot = SCREEN_H - FOOT_H
    stamp(img, bd['corner'], 0, foot)
    stamp(img, bd['corner'], SCREEN_W - BORDER_W, foot)
    for k in range((SCREEN_W - 2 * BORDER_W) // border.w):
        stamp(img, bd['edge_bottom'], BORDER_W + k * border.w, foot)
    return img


def _rule(img, glyph, x0, x1, y):
    for x in range(x0, x1, HW):
        stamp(img, glyph, x, y)


def draw_hud(img, candy, hud, text, icons):
    glyphs, ic = _by_name(hud, text), _by_name(icons)

    for y in range(HUD_Y, HUD_Y + HUD_H):          # φόντο ταμπλό HUD
        for x in range(HUD_X, HUD_X + 64):
            img[y][x] = PEN_LINE
        img[y][HUD_X] = PEN_GREY                   # η ραφή με το ταμπλό

    stamp(img, ic['score'], HUD_X + 3, HUD_Y + 6)  # πόντοι
    hud_text(img, '028450', HUD_X + 13, HUD_Y + 10, glyphs)

    stamp(img, ic['moves'], HUD_X + 3, HUD_Y + 28)  # κινήσεις
    hud_text(img, '24', HUD_X + 13, HUD_Y + 32, glyphs)
    stamp(img, ic['time'], HUD_X + 35, HUD_Y + 28)  # χρόνος
    hud_text(img, '1:40', HUD_X + 45, HUD_Y + 32, glyphs)

    _rule(img, glyphs['rule'], HUD_X + 2, HUD_X + 62, HUD_Y + 48)

    goals = [('red', 'plain', '12'), ('green', 'plain', '08'),
             ('blue', 'striped_h', '03')]
    for i, (colour, tag, count) in enumerate(goals):      # στόχοι πίστας
        y = HUD_Y + 58 + i * 30
        idx = candy.frames_of(tag)[COLOUR_KEY[colour[0] if colour != 'green' else 'g']]
        stamp(img, candy.frames[idx], HUD_X + 4, y)
        hud_text(img, 'x' + count, HUD_X + 20, y + 8, glyphs)

    _rule(img, glyphs['rule'], HUD_X + 2, HUD_X + 62, HUD_Y + 150)

    for i in range(3):                              # τα τρία αστέρια της πίστας
        stamp(img, ic['star_on' if i < 2 else 'star_off'],
              HUD_X + 6 + i * 20, HUD_Y + 158)

    bar = HUD_X + 4                                 # σωλήνας προόδου
    stamp(img, glyphs['bar_l'], bar, HUD_Y + 178)
    for k in range(13):
        stamp(img, glyphs['bar_f' if k < 8 else 'bar_e'],
              bar + HW * (k + 1), HUD_Y + 178)
    stamp(img, glyphs['bar_r'], bar + HW * 14, HUD_Y + 178)
    return img


def screen(*sets):
    S = _by_set(sets)
    img = blank(SCREEN_W, SCREEN_H, PEN_MASK)
    draw_border(img, S['title'], S['border'])
    draw_board(img, S['candy'], S['cells'], S['overlay'])
    draw_hud(img, S['candy'], S['hud'], S['text'], S['icons'])
    return img


# --------------------------------------------------------------- το μενού

MENU_ITEMS = ['PLAY', 'LEVELS', 'SOUND', 'SCORES']
MENU_TILES = 6                                  # πλάτος πιάτου σε πλακάκια
MENU_Y0, MENU_STEP = 48, 40


def menu_screen(*sets):
    """Η οθόνη του μενού: ίδιος τίτλος, ίδια μπορντούρα, πιάτα από ζαχαρωτό."""
    S = _by_set(sets)
    candy, menu = S['candy'], S['menu']
    img = blank(SCREEN_W, SCREEN_H, PEN_MASK)
    draw_border(img, S['title'], S['border'])
    glyphs, mn = _by_name(S['hud'], S['text']), _by_name(menu)

    plate_w = MENU_TILES * menu.w
    x0 = BOARD_X + (COLS * CW + 64 - plate_w) // 2
    for i, label in enumerate(MENU_ITEMS):
        y = MENU_Y0 + i * MENU_STEP
        for k in range(MENU_TILES):
            name = 'plate_l' if k == 0 else \
                   'plate_r' if k == MENU_TILES - 1 else 'plate_m'
            stamp(img, mn[name], x0 + k * menu.w, y)
        hud_text(img, label, x0 + (plate_w - text_w(label)) // 2, y + 8, glyphs)
        if i == 0:
            stamp(img, mn['pointer1'], x0 - menu.w - 8, y)

    # Μια σειρά από candies κάτω, για να μη μένει άδειο το κάτω μέρος.
    row = MENU_Y0 + len(MENU_ITEMS) * MENU_STEP + 4
    for i in range(6):
        stamp(img, candy.frames[candy.frames_of('plain')[i]],
              BOARD_X + 20 + i * (CW + 8), row)
    return img
