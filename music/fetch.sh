#!/usr/bin/env bash
# Ξανακατεβάζει τα MIDI του mfiles.co.uk σε αυτόν τον φάκελο.
# Τα αρχεία δεν είναι στο git — δείτε README.md για τον λόγο και τους όρους.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAGE="https://www.mfiles.co.uk/midi-original.htm"
BASE="https://www.mfiles.co.uk/"
UA="Mozilla/5.0"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Λήψη καταλόγου: $PAGE"
curl -sS -L -A "$UA" --max-time 60 "$PAGE" -o "$tmp/page.html"

python3 - "$tmp/page.html" "$DIR" "$BASE" > "$tmp/dl.conf" <<'PY'
import html, re, sys, urllib.parse
page, out, base = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(page, encoding="utf-8", errors="replace").read()
links = sorted(set(html.unescape(m)
                   for m in re.findall(r'href="(downloads/[^"]*\.mid)"', src, re.I)))
if not links:
    sys.exit("ΣΦΑΛΜΑ: δεν βρέθηκαν σύνδεσμοι .mid — άλλαξε η δομή της σελίδας.")
for href in links:
    name = href.split("/")[-1].replace('"', "")
    print('url = "%s"' % (base + urllib.parse.quote(href, safe="/")))
    print('output = "%s/%s"' % (out, name))
print("# %d αρχεία" % len(links), file=sys.stderr)
PY

# -L: έντεκα αρχεία σερβίρονται με 301 σε διαφορετικά πεζά/κεφαλαία.
# --limit-rate: ευγένεια προς τον server.
curl -sS -L -A "$UA" --retry 2 --max-time 600 --limit-rate 500k -K "$tmp/dl.conf"

bad=0
shopt -s nullglob
for f in "$DIR"/*.mid; do
  if [ "$(head -c 4 "$f" | xxd -p)" != "4d546864" ]; then
    echo "ΣΦΑΛΜΑ: δεν είναι MIDI: $(basename "$f")" >&2
    bad=$((bad + 1))
  fi
done
n=$(ls "$DIR"/*.mid 2>/dev/null | wc -l)
if [ "$bad" -gt 0 ]; then
  echo "$bad από $n αρχεία δεν είναι έγκυρα MIDI." >&2
  exit 1
fi
echo "Εντάξει: $n έγκυρα MIDI στο $DIR"
