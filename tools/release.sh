#!/bin/sh
# Build dist/stem7.zip: the fonts, stem7.css, the licence and a short readme.
set -e
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist/stem7/fonts
cp fonts/*.ttf fonts/*.woff2 dist/stem7/fonts/
cp stem7.css OFL.txt dist/stem7/
cat > dist/stem7/README.txt <<'T'
Stem 7 1.001, a pixel font by David Hatley. https://davidghatley.github.io/stem7/

Desktop: install the files in fonts/*.ttf.
Web: link stem7.css, or copy its @font-face rules.

Set it at 16, 32, 48, 72 or 120 px with line-height: 1, and every edge lands on a whole pixel.
At 16 px use caps and figures only. Use Stem 7 Grid from 48 px up.

SIL Open Font License 1.1 (OFL.txt).
T
(cd dist && TZ=UTC find stem7 -exec touch -t 202610230000 {} + && zip -qrX stem7.zip stem7)
ls -l dist/stem7.zip
