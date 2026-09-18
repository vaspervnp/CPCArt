"""Regenerate the whole top-down city pack.

    python make_all.py            (uses ../../build/bin/aseprite.exe, or $ASEPRITE)
    python make_all.py --map level1.json --map level2.json

--map: a level as JSON {"rows": [[global tile index, ...], ...]} using roads + buildings
indices (roads first). Its building shadows are added to the shadow sheet (after the ones
already there, so existing indices stay put) and <level>_shadowed.json is written next to it.

Writes into the parent folder: .aseprite tile sheets, PNG/JSON sheets exported by the
Aseprite CLI, piece/kit JSON, previews and mockups.
"""
import argparse
import json
import os
import struct
import subprocess
import tempfile

import buildings
import mockup
import preview
import roads
import shadows
from assemble import building, roof_grid
from cpcgfx import PALETTE, TW, TH

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
ASE = os.environ.get('ASEPRITE') or os.path.normpath(os.path.join(OUT, '..', 'build', 'bin', 'aseprite.exe'))
LUA = os.path.join(HERE, 'make_aseprite.lua')


def hexdump(t):
    return ''.join('%x' % v for row in t for v in row)


def write_dump(path, name, tiles, names, tags, grid=None):
    with open(path, 'w') as f:
        f.write('name %s\n' % name)
        f.write('pal ' + ' '.join('%02X%02X%02X' % p[3] for p in PALETTE) + '\n')
        for tag, a, b in tags:
            f.write('tag %s %d %d\n' % (tag, a, b))
        for t, n in zip(tiles, names):
            f.write('tile %s %s\n' % (n, hexdump(t)))
        if grid:
            f.write('map %d %d\n' % (len(grid[0]), len(grid)))
            for row in grid:
                f.write('row ' + ' '.join(str(v) for v in row) + '\n')


def aseprite(*args):
    subprocess.run([ASE, '-b'] + list(args), check=True)


def make_sheet(tmp, name, bank):
    dump = os.path.join(tmp, name + '.txt')
    write_dump(dump, name, bank.tiles, bank.names, bank.tag_ranges())
    ase = os.path.join(OUT, name + '.aseprite')
    aseprite('--script-param', 'in=' + dump, '--script-param', 'out=' + ase,
             '--script-param', 'mode=frames', '--script', LUA)
    aseprite(ase, '--sheet', os.path.join(OUT, name + '_sheet.png'), '--sheet-type', 'rows',
             '--sheet-columns', '8', '--data', os.path.join(OUT, name + '_sheet.json'),
             '--format', 'json-array', '--list-tags', '--list-layers')
    strip_trns(os.path.join(OUT, name + '_sheet.png'))


def strip_trns(path):
    """Aseprite marks index 0 transparent in indexed PNGs; these tiles are opaque, so drop it
    (pixel indices are untouched)."""
    data = open(path, 'rb').read()
    out, pos = data[:8], 8
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        if data[pos + 4:pos + 8] != b'tRNS':
            out += data[pos:pos + 12 + n]
        pos += 12 + n
    open(path, 'wb').write(out)


def pad(grid):
    w = max(len(r) for r in grid)
    return [list(r) + [None] * (w - len(r)) for r in grid]


def building_preview(bbank, kit, path):
    groups = []
    for style in ('office', 'brick', 'tower', 'shed', 'house', 'park'):
        k = kit[style]
        entries = []
        if style == 'house':
            entries.append(('house w3', building(kit, 'house', 3, props={(1, 0): 'chimney'}, doors=(1,))))
            entries.append(('house w5', building(kit, 'house', 5, doors=(3,))))
            r = k['roof']
            entries.append(('roof 2 rows', [[r['tl'], r['tm'], r['tr']], [r['bl'], r['bm'], r['br']]]))
        elif style == 'park':
            entries.append(('park 5x4', roof_grid(k, 5, 4, {(1, 1): 'tree', (3, 1): 'path_v', (3, 2): 'fountain',
                                                            (1, 2): 'path_h', (2, 2): 'path_h', (2, 1): 'flowers'})))
            entries.append(('9-slice', roof_grid(k, 3, 3)))
        else:
            floors = {'office': 2, 'brick': 2, 'tower': 3, 'shed': 1}[style]
            props = {'office': {(1, 1): 'ac', (2, 1): 'hatch'}, 'brick': {(1, 1): 'tank', (2, 1): 'chimney'},
                     'tower': {(1, 1): 'helipad'}, 'shed': {(1, 1): 'skylight', (2, 1): 'vent'}}[style]
            entries.append(('%s 4x3 +%d floor' % (style, floors), building(kit, style, 4, 3, floors, props)))
            entries.append(('9-slice', roof_grid(k, 3, 3)))
        if k['props']:
            flat = [v for v in k['props'].values() if not isinstance(v, list)]
            entries.append(('props', [flat]))
        if k['front']:
            f = k['front']
            rows = []
            for part in ('up', 'ground', 'wall'):
                if part in f:
                    rows.append([f[part + '_l'], f[part], f[part + '_r']])
            if 'door' in f:
                rows[-1].append(f['door'])
            entries.append(('front', pad(rows)))
        groups.append((style, entries))
    g = kit['ground']
    groups.append(('ground', [('plaza, lot, bays', [[g['plaza'], g['lot'], g['lot_bay_n'], g['lot_bay_s']]]),
                              ('parking 4x2', [[g['lot_bay_n']] * 4, [g['lot']] * 4])]))
    preview.catalogue(bbank, groups, path, scale=3, max_w=1500, title='BUILDINGS  (tiles 8x16, shown 2:1)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', action='append', default=[], help='level JSON to bake shadows for')
    args = ap.parse_args()
    rbank, pieces = roads.build()
    bbank, kit = buildings.build()
    R = len(rbank.tiles)
    print('road tiles %d, building tiles %d' % (R, len(bbank.tiles)))

    # mockup map, then the shadow tiles it (and any city) needs
    B = len(bbank.tiles)
    casters = [False] * R + [t not in ('bld_park', 'ground') for t in bbank.tags]
    m = mockup.build(rbank, pieces, bbank, kit)
    base_rows = [row[:] for row in m.c]
    sh = shadows.ShadowSet(rbank.tiles + bbank.tiles, rbank.names + bbank.names, R)
    sh.add(shadows.canonical_requests(pieces, kit, R), 'shadow_common')
    reqs = sh.map_requests(m.c, [[casters[t] for t in row] for row in m.c])
    sh.add([(b, n) for b, n, _ in reqs], 'shadow_mockup')
    sh.apply_map(m.c, reqs, R + B)
    for path in args.map:
        with open(path, encoding='utf-8') as f:
            rows = json.load(f)['rows']
        tag = 'shadow_' + os.path.splitext(os.path.basename(path))[0]
        lreqs = sh.map_requests(rows, [[casters[t] for t in row] for row in rows])
        sh.add([(b, n) for b, n, _ in lreqs], tag)
        sh.apply_map(rows, lreqs, R + B)
        out = os.path.splitext(path)[0] + '_shadowed.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump({'w': len(rows[0]), 'h': len(rows), 'rows': rows,
                       'about': 'global indices: roads, buildings, then shadows (see tile_table.json)'}, f)
        print('baked', out)
    sbank = sh.bank
    S = len(sbank.tiles)
    m.tiles = m.tiles + sbank.tiles
    print('shadow tiles %d, total %d' % (S, R + B + S))
    if R + B + S > 256:
        print('WARNING: %d tiles no longer fit 1-byte tile indices' % (R + B + S))
    mockup.render_all(m, OUT)

    with tempfile.TemporaryDirectory() as tmp:
        make_sheet(tmp, 'roads_cpc_mode0', rbank)
        make_sheet(tmp, 'buildings_cpc_mode0', bbank)
        make_sheet(tmp, 'shadows_cpc_mode0', sbank)
        tags = (rbank.tag_ranges() + [(t, a + R, b + R) for t, a, b in bbank.tag_ranges()] +
                [(t, a + R + B, b + R + B) for t, a, b in sbank.tag_ranges()])
        dump = os.path.join(tmp, 'map.txt')
        write_dump(dump, 'city', rbank.tiles + bbank.tiles + sbank.tiles,
                   rbank.names + bbank.names + sbank.names, tags, m.c)
        aseprite('--script-param', 'in=' + dump, '--script-param', 'out=' + os.path.join(OUT, 'mockup_city_tilemap.aseprite'),
                 '--script-param', 'mode=tilemap', '--script', LUA)

    # previews
    groups = {}
    for p in pieces:
        groups.setdefault(p['group'], []).append((p['name'], p['tiles']))
    preview.catalogue(rbank, list(groups.items()), os.path.join(OUT, 'preview_roads.png'), scale=2,
                      max_w=1500, title='ROAD PIECES  (tiles 8x16, shown 2:1)')
    preview.tile_sheet_preview(rbank, os.path.join(OUT, 'preview_roads_index.png'))
    building_preview(bbank, kit, os.path.join(OUT, 'preview_buildings.png'))
    preview.tile_sheet_preview(bbank, os.path.join(OUT, 'preview_buildings_index.png'))
    preview.tile_sheet_preview(sbank, os.path.join(OUT, 'preview_shadows_index.png'))

    # data
    def js(name, obj):
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write('\n')

    js('road_pieces.json', {
        'sheet': 'roads_cpc_mode0_sheet.png', 'tile': [TW, TH], 'tile_count': R,
        'about': "Each piece is a metatile: 'tiles' is rows of tile indices into roads_cpc_mode0_sheet.png "
                 "(w x h tiles). 'connects' lists the sides the piece opens to, in N E S W order: "
                 "EW/NS = straight, two adjacent letters = bend, three = T junction, NESW = crossing, "
                 "one letter = dead end open on that side. Straights and zebras are 1 tile long and repeat. "
                 "Junction pieces 'major_EW+minor_N' join a minor road to a major one; the block is "
                 "minor-width x major-width. Group 'decor' = drop-in straights with manholes and kerb drains "
                 "(on the south/east side of streets and avenues, which building shadows never reach) and "
                 "'asphalt_manhole', a plain asphalt tile for junction cores.",
        'road_types': {
            'alley': {'width_tiles': 1, 'cross_section_units': '2 footway | 12 cobbles | 2 footway',
                      'notes': 'no markings, no kerb; one lane'},
            'street': {'width_tiles': 2, 'cross_section_units': '4 paving, 2 kerb | 9 lane | 2 centre dash | 9 lane | kerb, paving',
                       'notes': 'two lanes ~5 Mode 0 pixels wide when vertical'},
            'avenue': {'width_tiles': 4, 'cross_section_units': '6 sidewalk | 10 lane, 2 dash, 10 lane | 2 yellow, 4, 2 yellow | 10 lane, 2 dash, 10 lane | 6 sidewalk',
                       'notes': 'four lanes and a double yellow line'},
        },
        'units': '1 tile = 16x16 visual units; a Mode 0 pixel is 2 units wide and 1 tall',
        'pieces': pieces,
    })

    def kit_json(k):
        return {key: val for key, val in k.items()}
    js('building_kit.json', {
        'sheet': 'buildings_cpc_mode0_sheet.png', 'tile': [TW, TH], 'tile_count': len(bbank.tiles),
        'about': "Flat roofs are 9-slices (keys tl t tr / l c r / bl b br): corners once, edges repeat, "
                 "c fills the middle; any size >= 2x2. Props replace a 'c' tile (helipad is 2x2, row-major). "
                 "Under the roof's bottom row put the front wall: optional 'up' rows (upper floors), then one "
                 "'ground' row; *_l / *_r are the ends, 'door' can replace any middle ground tile. "
                 "House: 2 roof rows (tl tm tr / bl bm br, tm repeats) + one 'wall' row. "
                 "Park: 9-slice with hedge; tree, flowers, fountain and paths replace 'c'. "
                 "Fronts face south (the camera looks slightly north), so put them on the south side of a building.",
        'styles': {s: kit_json(k) for s, k in kit.items()},
    })

    base_names = rbank.names + bbank.names
    js('shadow_table.json', {
        'sheet': 'shadows_cpc_mode0_sheet.png', 'tile': [TW, TH], 'tile_count': S,
        'about': "Building shadows: light from the top-left, footprint (roof + front wall) swept %d units "
                 "right and %d down (= sidewalk width). Shadow tile = base tile with the mask's pixels "
                 "remapped to darker pens. Masks are 16 rows, bit n = pixel n. Buildings cast (every "
                 "buildings-sheet tile except tags bld_park and ground); only non-building cells receive. "
                 "Tag shadow_common = sidewalks of straights + open ground, shadow_mockup = extra "
                 "cases the mockup needed (junction corners, park edges, alleys with furniture...). "
                 "For other cases run src/make_all.py --map your_level.json." % (shadows.DX, shadows.DY),
        'remap': {PALETTE[i][1]: PALETTE[j][1] for i, j in enumerate(shadows.REMAP) if i != j},
        'masks': {n: list(v) for n, v in sh.masks.items()},
        'tiles': [dict(e, global_index=R + B + e['index'], base_name=base_names[e['base_global']],
                       name=sbank.names[e['index']]) for e in sh.table],
    })

    table = []
    for sheet, bank, off in (('roads', rbank, 0), ('buildings', bbank, R), ('shadows', sbank, R + B)):
        for i, (n, t) in enumerate(zip(bank.names, bank.tags)):
            table.append({'sheet': sheet, 'index': i, 'global': i + off, 'name': n, 'tag': t})
    js('tile_table.json', {
        'about': "Every tile is opaque (plain copy, pen 0 = black). 'global' = index when the sheets are "
                 "loaded into one bank: roads 0..%d, buildings %d..%d, shadows %d..%d."
                 % (R - 1, R, R + B - 1, R + B, R + B + S - 1),
        'tiles': table})
    js('mockup_city_map.json', {
        'w': mockup.MAP_W, 'h': mockup.MAP_H,
        'about': 'Row-major global tile indices (see tile_table.json). rows = with shadows, '
                 'base_rows = the same map before shadows were baked.',
        'rows': m.c, 'base_rows': base_rows})

    manifest = {
        'set': 'cpc_topdown_city',
        'about': 'GTA1-style top-down city for Amstrad CPC Mode 0. Tiles are 8x16 Mode 0 pixels '
                 '(square on screen), 64 bytes each.',
        'palette': [{'pen': i, 'name': p[1], 'firmware_ink': p[2], 'rgb': '#%02X%02X%02X' % p[3]}
                    for i, p in enumerate(PALETTE)],
        'sheets': [
            {'name': 'roads', 'file': 'roads_cpc_mode0_sheet.png', 'aseprite': 'roads_cpc_mode0.aseprite',
             'size': [TW, TH], 'count': R,
             'tags': {t: b - a + 1 for t, a, b in rbank.tag_ranges()},
             'pieces': 'road_pieces.json'},
            {'name': 'buildings', 'file': 'buildings_cpc_mode0_sheet.png', 'aseprite': 'buildings_cpc_mode0.aseprite',
             'size': [TW, TH], 'count': len(bbank.tiles),
             'tags': {t: b - a + 1 for t, a, b in bbank.tag_ranges()},
             'kit': 'building_kit.json'},
            {'name': 'shadows', 'file': 'shadows_cpc_mode0_sheet.png', 'aseprite': 'shadows_cpc_mode0.aseprite',
             'size': [TW, TH], 'count': S,
             'tags': {t: b - a + 1 for t, a, b in sbank.tag_ranges()},
             'table': 'shadow_table.json'},
        ],
        'memory': {'tiles': R + B + S, 'bytes': 64 * (R + B + S),
                   'note': 'all three sheets together %s a 1-byte tile map (256 tiles)'
                           % ('fit' if R + B + S <= 256 else 'do NOT fit')},
        'mockups': ['mockup_city.png', 'mockup_screen.png', 'mockup_city_tilemap.aseprite', 'mockup_city_map.json'],
        'notes': 'Previews and mockups are drawn with 2:1 pixels. The three cars in the mockups are '
                 'placeholders for scale only and are not part of the sheets. Light comes from the top-left. '
                 'Regenerate everything with src/make_all.py.',
    }
    js('manifest.json', manifest)


if __name__ == '__main__':
    main()
