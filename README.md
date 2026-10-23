# Stem 7

A pixel font that refuses to blur. Stem 7 is drawn on the 7 × 7 grid of my mark, and one cell is always the font size divided by eight. At **16, 32, 48, 72 and 120 px** every edge lands on a whole pixel, with zero grey pixels.

**Website, with every glyph and how it was made: https://davidghatley.github.io/stem7/**

- Three styles: Regular, a hand-drawn Bold, and Grid (a variable font where every cell is its own square).
- 120 glyphs each: Basic Latin, curly quotes, dashes, arrows, `·` `×` `•` `°`, a figure space, my mark at U+E000 (or type `dh`) and seven project glyphs at U+E001–E007.
- Tabular figures, whole-cell kerning, and WOFF2 files of about 3.4 KB.
- SIL Open Font License 1.1, with no reserved font name.

## Install

**Download:** [stem7.zip](https://github.com/davidghatley/stem7/releases/latest/download/stem7.zip) holds the TTF and WOFF2 files, `stem7.css` and the licence.

**npm**, straight from GitHub:

```sh
npm install github:davidghatley/stem7
```

```js
import "stem7/stem7.css";
```

```html
<h1 class="stem7 stem7--48">Hello</h1>
```

**CDN** (jsDelivr):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/davidghatley/stem7@v1.0.1/stem7.css">
```

## Use it well

```css
.pixel {
  font-family: "Stem 7";
  font-size: 32px;              /* 16, 32, 48, 72 or 120 */
  line-height: 1;               /* the baseline sits 7 cells down */
  -webkit-font-smoothing: none;
}
```

- Use only the five sizes. At 20 px a cell is 2.5 px, and the half pixel turns grey.
- At 16 px, set caps and figures only. Lowercase starts at 32.
- Start text on a whole pixel.
- Use Grid from 48 px up. It is crisp below that, but thin.

## Build it

The glyphs are plain text: `src/regular.s7` and `src/bold.s7` hold nine rows of `X` and `.` per glyph, with the reason for each drawing in a comment above it. `src/kern-*.txt` holds the kerning in whole cells. The mark and project glyphs come from `src/house.json`.

```sh
uv venv && uv pip install fonttools brotli pillow uharfbuzz
.venv/bin/python tools/stemctl.py build      # fonts/Stem7-{Regular,Bold,Grid}.{ttf,woff2}
.venv/bin/python tools/stemctl.py lint       # glyph and font checks
.venv/bin/python tests/kerncheck.py          # every kerning pair, shaped by HarfBuzz
.venv/bin/python tools/stemctl.py crisp      # counts grey pixels in headless Chromium
.venv/bin/python tools/export_site.py        # glyph data for the website
sh tools/release.sh                          # dist/stem7.zip
```

`stemctl` also derives kerning (`kern --write`), renders proof sheets (`proof`), drafts Bold (`draft-bold`) and draws before/after diffs (`diff`, `compare`). Run `python tools/stemctl.py -h` for the full list.

## Changelog

- **1.001**: F now kerns against a, c, e, g, m, n, o, r, u, w and y. The source always asked for those 11 pairs, but the build put F in a class subtable where it already had a value of 0. The fix enumerates single-glyph-against-class pairs, and `tests/kerncheck.py` now checks every pair.
- **1.000**: Regular, hand-drawn Bold and variable Grid.

## Licence

Copyright 2026 David Hatley. Licensed under the [SIL Open Font License 1.1](OFL.txt). The site's design system files (`site/tokens.css`, `site/components.css`) come from my house system, Secret Sauce.
