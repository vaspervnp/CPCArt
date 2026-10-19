#!/bin/sh
# Συναρμολογεί τους loaders και φτιάχνει μία δισκέτα με τις δύο εικόνες.
#
#     ./build_disk.sh
#
# Θέλει rasm και iDSK στο PATH. Τρέξε πρώτα `python3 src/make_screen.py`,
# που παράγει τα .asm και τα .scr.
#
# Στη δισκέτα τα ονόματα είναι 8.3 και κεφαλαία — το AMSDOS δεν δέχεται άλλο,
# οπότε το `panigiri_drone` γίνεται `DRONE`.
set -e
cd "$(dirname "$0")"

DSK=panigiri.dsk
rm -f "$DSK"
iDSK "$DSK" -n >/dev/null

add() {                       # add <κλειδί> <όνομα 8.3 στη δισκέτα>
    rasm "$1.asm" -o "$1" >/dev/null
    cp "$1.bin" "$2.BIN"
    cp "$1.scr" "$2.SCR"
    # -t 1 = δυαδικό με header AMSDOS, -c = διεύθυνση φόρτωσης, -e = εκκίνησης
    iDSK "$DSK" -i "$2.BIN" -t 1 -c 4000 -e 4000 >/dev/null
    iDSK "$DSK" -i "$2.SCR" -t 1 -c C000 -e 0000 >/dev/null
    rm -f "$2.BIN" "$2.SCR"
    echo "  $1 -> $2.BIN ($(stat -c%s "$1.bin") bytes) + $2.SCR"
}

add panigiri       PANIGIRI
add panigiri_drone DRONE

echo
iDSK "$DSK" -l
echo
echo "Στον 6128:   RUN\"PANIGIRI\"   ή   RUN\"DRONE\""
