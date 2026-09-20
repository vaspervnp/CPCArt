#!/usr/bin/env python3
"""Τρέχει όλη την αλυσίδα: sprites -> αρχεία Aseprite -> επαλήθευση.

    python3 tools/make_all.py [--anim-frames 1|2] [--uniform-quads]

Το βήμα του Aseprite χρειάζεται το εκτελέσιμο: ορίζεται με τη μεταβλητή
περιβάλλοντος ASEPRITE. Αν λείπει, τα υπόλοιπα βήματα τρέχουν κανονικά και
τυπώνεται η εντολή που πρέπει να τρέξει χειροκίνητα.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DUMP = os.path.join(ROOT, "build", "sprites", "aseprite_dump.txt")
OUT = os.path.join(ROOT, "sprites")
LUA = os.path.join(HERE, "make_aseprite.lua")


def run(*cmd):
    print("$ " + " ".join(cmd))
    return subprocess.call(cmd)


def main(argv):
    if run(sys.executable, os.path.join(HERE, "make_sprites.py"), *argv):
        return 1

    os.makedirs(OUT, exist_ok=True)
    ase = os.environ.get("ASEPRITE")
    cmd = [ase or "aseprite", "-b",
           "--script-param", "in=" + DUMP,
           "--script-param", "out=" + OUT,
           "--script", LUA]
    if not ase:
        print("\nΔεν ορίστηκε ASEPRITE — παράλειψη του βήματος Aseprite.")
        print("Για να φτιαχτούν τα .aseprite τρέξε:")
        print("  " + " ".join('"%s"' % c if " " in c else c for c in cmd))
        return 0
    if run(*cmd):
        return 1
    return subprocess.call([sys.executable, os.path.join(HERE, "check_aseprite.py")])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
