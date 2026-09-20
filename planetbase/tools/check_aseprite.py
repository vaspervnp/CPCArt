#!/usr/bin/env python3
"""Επαληθεύει ότι τα εξαγόμενα sheets του Aseprite ταυτίζονται με τη γεννήτρια.

    python3 tools/check_aseprite.py

Συγκρίνει pixel-προς-pixel το κάθε frame του `sprites/*_sheet.png` (μέσω του
JSON του Aseprite) με το `build/sprites/aseprite_dump.txt`. Έτσι πιάνεται
οποιαδήποτε απόκλιση παλέτας, διαφάνειας ή σειράς frames.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import RGB

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, "build", "sprites", "aseprite_dump.txt")
SPRITES = os.path.join(ROOT, "sprites")
PREFIX = "planetbase_"


def read_dump(path):
    groups, name = {}, None
    for line in open(path, encoding="utf-8"):
        kind, _, rest = line.strip().partition(" ")
        if kind == "group":
            n, w, h = rest.split()
            name = n
            groups[n] = (int(w), int(h), {})
        elif kind == "frame":
            n, hexes = rest.split()
            groups[name][2][n] = hexes
    return groups


def main():
    if not os.path.isdir(SPRITES):
        print("δεν υπάρχει ο φάκελος sprites/ — τρέξε πρώτα το make_aseprite.lua",
              file=sys.stderr)
        return 1
    rgb2pen = {c: i for i, c in enumerate(RGB)}
    checked = bad = 0
    for group, (w, h, frames) in read_dump(DUMP).items():
        base = os.path.join(SPRITES, f"{PREFIX}{group}_cpc_mode0_sheet")
        sheet = Image.open(base + ".png").convert("RGBA")
        meta = json.load(open(base + ".json", encoding="utf-8"))
        tags = [t["name"] for t in meta["meta"]["frameTags"]]
        if tags != list(frames):
            print(f"  {group}: τα tags δεν ταιριάζουν με τα frames", file=sys.stderr)
            bad += 1
        for i, (name, hexes) in enumerate(frames.items()):
            box = meta["frames"][i]["frame"]
            for y in range(h):
                for x in range(w):
                    r, g, b, a = sheet.getpixel((box["x"] + x, box["y"] + y))
                    want = int(hexes[y * w + x], 16)
                    got = 0 if a == 0 else rgb2pen.get((r, g, b), -1)
                    if got != want:
                        if bad < 10:
                            print(f"  {group}/{name} ({x},{y}): sheet={got} dump={want}",
                                  file=sys.stderr)
                        bad += 1
                    checked += 1
    print("ελέγχθηκαν %d pixels σε %d ομάδες" % (checked, len(read_dump(DUMP))))
    if bad:
        print("ΑΠΟΤΥΧΙΑ: %d διαφορές" % bad, file=sys.stderr)
        return 1
    print("τα sheets του Aseprite ταυτίζονται με τη γεννήτρια")
    return 0


if __name__ == "__main__":
    sys.exit(main())
