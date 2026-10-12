"""Ξαναχτίζει ολόκληρο το γραφικό πακέτο του Sugar Byte.

    python3 src/make_all.py

Γράφει στον γονικό φάκελο: φύλλα PNG σε αυθεντικά pixels Mode 0, πίνακες JSON,
προεπισκοπήσεις 2:1, μία πλήρη οθόνη, την παλέτα, και το έτοιμο για τον
assembler ζευγάρι sprites.bin / sprites.asm.

Τα .aseprite χτίζονται από τα dumps στο build/aseprite/ με το make_aseprite.lua:
    aseprite -b --script-param in=<dump> --script-param out=<x.aseprite> \
             --script-param mode=frames --script src/make_aseprite.lua
"""
import json
import os
import subprocess

import cpcgfx as g
import mockup as mk
import preview as pv
import sprites as sp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
BUILD = os.path.join(OUT, 'build')
DUMPS = os.path.join(BUILD, 'aseprite')
ASE = os.environ.get('ASEPRITE', '')
LUA = os.path.join(HERE, 'make_aseprite.lua')
SHEET_COLS = 7


def hexdump(frame):
    return ''.join('%x' % (0 if p is None else p) for row in frame for p in row)


def write_dump(path, s):
    """Το ενδιάμεσο κείμενο που διαβάζει το make_aseprite.lua."""
    with open(path, 'w') as f:
        f.write('name %s\n' % s.name)
        f.write('size %d %d\n' % (s.w, s.h))
        if s.masked:
            f.write('transparent\n')
        f.write('pal ' + ' '.join('%02X%02X%02X' % c for c in g.RGB) + '\n')
        for tag, a, b in s.tag_ranges():
            f.write('tag %s %d %d\n' % (tag, a, b))
        for frame, name in zip(s.frames, s.names):
            f.write('tile %s %s\n' % (name, hexdump(frame)))


def write_sheet(s):
    img = s.sheet(SHEET_COLS)
    g.write_indexed_png(os.path.join(OUT, s.name + '_sheet.png'), img,
                        transparent_pen0=s.masked)
    rows = (len(s.frames) + SHEET_COLS - 1) // SHEET_COLS
    doc = {
        'name': s.name,
        'note': s.note,
        'cell': {'w': s.w, 'h': s.h},
        'masked': s.masked,
        'bytes_per_frame': s.bytes_per_frame(),
        'total_bytes': s.total_bytes(),
        'sheet': {'cols': SHEET_COLS, 'rows': rows,
                  'w': SHEET_COLS * s.w, 'h': rows * s.h},
        'tags': [{'name': t, 'from': a, 'to': b} for t, a, b in s.tag_ranges()],
        'frames': [{'index': i, 'name': n, 'tag': t,
                    'x': (i % SHEET_COLS) * s.w, 'y': (i // SHEET_COLS) * s.h}
                   for i, (n, t) in enumerate(zip(s.names, s.tags))],
    }
    with open(os.path.join(OUT, s.name + '_sheet.json'), 'w') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    return doc


ASM_HEAD = """; sprites.asm — Sugar Byte, Amstrad CPC Mode 0
; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από src/make_all.py — μην το πειράζεις με το χέρι.
;
; Δεδομένα γραμμικά (γραμμή-γραμμή), ΟΧΙ στη διάταξη της μνήμης οθόνης.
;
; Τα candies και οι επικαλύψεις έχουν ΜΑΣΚΑ, σε μορφή «mask, data, mask, data…»
; ανά γραμμή. ΠΡΟΣΟΧΗ: οι σταθερές _W δίνουν bytes ΔΕΔΟΜΕΝΩΝ ανά γραμμή — σε
; sprite με μάσκα η γραμμή πιάνει 2x αυτό:
;       ld a,(hl) : inc hl : and (de) : ld b,a
;       ld a,(hl) : inc hl : or b     : ld (de),a : inc de
; Τα κελιά του ταμπλό και τα κελιά του HUD είναι αδιαφανή (μόνο data): σκέτο LDI.
;
; Όλα τα καρέ ενός σετ έχουν ίδιο μέγεθος, άρα δεν χρειάζεται πίνακας δεικτών:
;       διεύθυνση = <set>_gfx + καρέ * <SET>_SZ
;
"""


def write_asm_bin(sets):
    """Ένα ενιαίο sprites.bin και το sprites.asm που το περιγράφει."""
    blob = bytearray()
    lines = [ASM_HEAD]
    offsets = []

    for s in sets:
        key = s.name.split('_')[0].upper()
        lines.append('%-14s equ %-5d ; bytes ΔΕΔΟΜΕΝΩΝ ανά γραμμή%s'
                     % (key + '_W', s.w // 2,
                        ' (η γραμμή είναι 2x: mask+data)' if s.masked else ''))
        lines.append('%-14s equ %-5d ; γραμμές' % (key + '_H', s.h))
        lines.append('%-14s equ %-5d ; bytes ανά καρέ' % (key + '_SZ', s.bytes_per_frame()))
        lines.append('%-14s equ %-5d ; καρέ' % (key + '_N', len(s.frames)))
        for tag, a, b in s.tag_ranges():
            lines.append('%-14s equ %-5d ; %d καρέ' % (key + '_' + tag.upper(), a, b - a + 1))
        lines.append('')

    for s in sets:
        label = s.name.split('_')[0] + '_gfx'
        offsets.append((label, len(blob), s.total_bytes()))
        lines.append('%s:   ; %s' % (label, s.note))
        enc = g.encode_masked if s.masked else g.encode_opaque
        for i, (frame, name, tag) in enumerate(zip(s.frames, s.names, s.tags)):
            data = enc(frame)
            blob += data
            lines.append('  ; %3d %s/%s' % (i, tag, name))
            for r in range(0, len(data), 16):
                lines.append('  db ' + ','.join('#%02X' % b for b in data[r:r + 16]))
        lines.append('')

    with open(os.path.join(OUT, 'sprites.bin'), 'wb') as f:
        f.write(blob)
    with open(os.path.join(OUT, 'sprites.asm'), 'w') as f:
        f.write('\n'.join(lines))
    return blob, offsets


def write_map(sets, offsets):
    out = ['Sugar Byte — χάρτης του sprites.bin',
           '=' * 60, '']
    for s, (label, off, size) in zip(sets, offsets):
        out.append('%s  @ %5d (#%04X)  %d bytes  %s'
                   % (label, off, off, size, s.note))
        out.append('    %d x %d pixels, %s, %d bytes/καρέ'
                   % (s.w, s.h, 'με μάσκα' if s.masked else 'αδιαφανές',
                      s.bytes_per_frame()))
        for i, (n, t) in enumerate(zip(s.names, s.tags)):
            out.append('      %3d  %-14s %-11s @ %5d'
                       % (i, n, t, off + i * s.bytes_per_frame()))
        out.append('')
    out.append('ΣΥΝΟΛΟ %d bytes' % sum(x[2] for x in offsets))
    with open(os.path.join(OUT, 'sprites_map.txt'), 'w') as f:
        f.write('\n'.join(out) + '\n')


def write_palette():
    gpl = ['GIMP Palette', 'Name: Sugar Byte CPC Mode 0', 'Columns: 4',
           '# Amstrad CPC Mode 0 — 16 pens από τα 27 χρώματα του firmware.',
           '# Η στήλη FW είναι ο αριθμός για το SCR SET INK / τον Gate Array.', '#']
    for i, p in enumerate(g.PALETTE):
        r, gg, b = p[3]
        gpl.append('%3d %3d %3d\tpen %02d  FW %02d  %s — %s'
                   % (r, gg, b, i, p[2], p[1], p[4]))
    with open(os.path.join(OUT, 'palette.gpl'), 'w') as f:
        f.write('\n'.join(gpl) + '\n')
    pv.palette_strip(os.path.join(OUT, 'preview_palette.png'), g.PALETTE)


def main():
    os.makedirs(DUMPS, exist_ok=True)
    sets = sp.all_sets()
    docs = []

    for s in sets:
        docs.append(write_sheet(s))
        write_dump(os.path.join(DUMPS, s.name + '.txt'), s)
        pv.sheet_png_preview(s, os.path.join(OUT, 'preview_' + s.name.split('_')[0] + '.png'),
                             cols=SHEET_COLS if s.w > 8 else 10,
                             scale=3 if s.w > 8 else 6)
        if ASE:
            subprocess.run([ASE, '-b',
                            '--script-param', 'in=' + os.path.join(DUMPS, s.name + '.txt'),
                            '--script-param', 'out=' + os.path.join(OUT, s.name + '.aseprite'),
                            '--script-param', 'mode=frames', '--script', LUA], check=True)

    candy, cells, overlay, hud = sets
    screen = mk.screen(candy, cells, overlay, hud)
    g.write_indexed_png(os.path.join(OUT, 'mockup_screen.png'), screen)
    cv = g.Canvas(mk.SCREEN_W * 6, mk.SCREEN_H * 3, (0, 0, 0))
    cv.blit_pens(screen, 0, 0, 6, 3)
    cv.save(os.path.join(OUT, 'mockup_screen_2x1.png'))

    write_palette()
    blob, offsets = write_asm_bin(sets)
    write_map(sets, offsets)

    manifest = {
        'project': 'Sugar Byte',
        'machine': 'Amstrad CPC, Mode 0, 160x200, 16 pens, αναλογία pixel 2:1',
        'board': {'cols': mk.COLS, 'rows': mk.ROWS,
                  'cell': {'w': g.CW, 'h': g.CH},
                  'origin': {'x': mk.BOARD_X, 'y': mk.BOARD_Y},
                  'pixels': {'w': mk.COLS * g.CW, 'h': mk.ROWS * g.CH},
                  'hud_x': mk.HUD_X, 'hud_cell': {'w': g.HW, 'h': g.HH}},
        'palette': [{'pen': i, 'firmware': p[2],
                     'rgb': '#%02X%02X%02X' % p[3], 'name': p[1], 'use': p[4]}
                    for i, p in enumerate(g.PALETTE)],
        'candy_colours': [{'index': i, 'name': n, 'base': b, 'shade': s_,
                           'shape': sh}
                          for i, ((n, b, s_), sh) in
                          enumerate(zip(g.CANDY_PENS,
                                        __import__('shapes').SHAPE_NAMES))],
        'sets': docs,
        'binary': {'file': 'sprites.bin', 'bytes': len(blob),
                   'blocks': [{'label': l, 'offset': o, 'bytes': n}
                              for l, o, n in offsets]},
    }
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write('\n')

    print('%-22s %-8s %5s %10s' % ('σετ', 'κελί', 'καρέ', 'bytes'))
    for s in sets:
        print('%-22s %-8s %5d %10d' % (s.name, '%dx%d' % (s.w, s.h),
                                       len(s.frames), s.total_bytes()))
    print('%-22s %-8s %5d %10d  (%.1f KB)' % ('ΣΥΝΟΛΟ', '', 
          sum(len(s.frames) for s in sets), len(blob), len(blob) / 1024.0))


if __name__ == '__main__':
    main()
