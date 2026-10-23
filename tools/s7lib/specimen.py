"""specimen: one self-contained HTML page (the three WOFF2 files inlined as data: URIs), house colours from
tokens.json for light and dark, ready to publish as an artifact. -> proofs/specimen.html"""
from . import FONT_DIR, ROOT
from .render import font_faces, colours, esc, STEPS, CRISP_STEPS
from .fontbuild import sources, bold_set, VERSION, UPM, CELL
from .proof import VOCAB

OUT = ROOT / "proofs" / "specimen.html"


def tokens_css():
    C = colours()
    names = ["paper", "sheet", "ink", "ink-muted", "rule", "rule-faint", "cobalt", "cobalt-text", "on-cobalt",
             "vermilion", "on-vermilion", "cobalt-tint"]
    light = ";".join(f"--{n}:{C['light'][n]}" for n in names)
    dark = ";".join(f"--{n}:{C['dark'][n]}" for n in names)
    return (f":root,[data-theme=light]{{{light};color-scheme:light}}"
            f"@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{{dark};color-scheme:dark}}}}"
            f"[data-theme=dark]{{{dark};color-scheme:dark}}")


def main(a):
    reg, bold_src = sources()
    bold, _ = bold_set(reg, bold_src)
    chars = "".join(chr(g.cps[0]) for g in reg.values() if g.cps and g.rows and any(g.ink()) and g.cps[0] < 0xE000)
    pua = [(g.name.replace("pantry.", ""), chr(g.cps[0])) for g in reg.values() if g.cps and g.cps[0] >= 0xE000]
    water = "".join(
        f'<div class="wrow"><span class="lab">{s} px · {s / 8:g} px cell{" · whole" if s in CRISP_STEPS else ""}</span>'
        f'<span class="px" style="font-size:{s}px">{"SEED 4127 · Tile rules" if s < 72 else ("PLATE 2.1" if s < 120 else "dh 07")}</span></div>'
        for s in STEPS if s >= 16)
    styles = "".join(
        f'<div class="st"><span class="lab">{n}</span><span class="px {c}" style="font-size:48px">BUILD LOG 07</span>'
        f'<span class="px {c}" style="font-size:32px">playdough · napkin</span></div>'
        for n, c in (("Regular 400", ""), ("Bold 700", "b"), ("Grid (opsz)", "g")))
    vocab = "".join(f'<li class="px" style="font-size:32px">{esc(v)}</li>' for v in VOCAB[:12])
    puas = "".join(f'<figure><span class="px" style="font-size:72px">{c}</span><figcaption class="lab">U+{ord(c):04X} · {esc(n)}</figcaption></figure>' for n, c in pua)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stem 7 specimen</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:ital,opsz,wght@1,6..72,400&display=swap">
<style>
{font_faces(inline=True)}
{tokens_css()}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:400 16px/24px Archivo,system-ui,sans-serif}}
main{{max-width:62rem;margin:0 auto;padding:32px 16px 64px}}
.lab{{font:500 11px/16px "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-muted)}}
.px{{font-family:"Stem 7";line-height:1;font-synthesis:none;letter-spacing:0;font-variant-ligatures:common-ligatures;
  -webkit-font-smoothing:none;font-kerning:normal;overflow-wrap:anywhere}}
.b{{font-weight:700}} .g{{font-family:"Stem 7 Grid"}}
.plate{{background:var(--sheet);border:1px solid var(--rule);padding:12px 16px 16px;margin:0 0 32px}}
.head{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding-bottom:12px;margin-bottom:16px}}
.cap{{font:italic 400 16px/24px Newsreader,Georgia,serif;color:var(--ink-muted);margin:16px 0 0;max-width:46rem}}
.spine{{display:flex;gap:24px;align-items:flex-end;flex-wrap:wrap}}
.mast{{font-size:120px}}
.wrow{{display:grid;grid-template-columns:13rem minmax(0,1fr);gap:16px;align-items:end;padding:8px 0;border-bottom:1px solid var(--rule-faint);overflow:hidden}}
.wrow .px{{white-space:nowrap}}
.st{{display:grid;gap:12px;padding:12px 0;border-bottom:1px solid var(--rule-faint)}}
.chars{{font-size:32px;line-height:48px;word-break:break-all}}
ul{{list-style:none;margin:0;padding:0;display:grid;gap:16px}}
.pua{{display:flex;flex-wrap:wrap;gap:24px}} figure{{margin:0;display:grid;gap:8px}}
.spec{{display:flex;flex-wrap:wrap;gap:8px 24px;border-top:1px solid var(--rule);padding-top:12px;margin-top:16px}}
.spec i{{font-style:normal;color:var(--ink-muted)}}
.spec span{{font:400 13px/20px "IBM Plex Mono",monospace}}
.stamp{{background:var(--vermilion);color:var(--on-vermilion);padding:2px 6px;border-radius:2px}}
table{{border-collapse:collapse;width:100%;font:400 13px/20px "IBM Plex Mono",monospace}}
td,th{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule-faint)}} th{{color:var(--ink-muted);font-weight:500}}
@media (max-width:640px){{.mast{{font-size:72px}} .wrow{{grid-template-columns:minmax(0,1fr)}}}}
</style></head>
<body><main>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.1 · Stem 7 · specimen</span><span class="lab"><span class="stamp">v{VERSION}</span> · OFL 1.1</span></div>
  <div class="spine"><span class="px mast">dh</span><span class="px mast">Stem 7</span></div>
  <p class="cap">A pixel face drawn on the grid of the dh mark: seven-cell caps, a four-cell x-height, a two-cell descender. Typing dh sets the mark.</p>
  <div class="spec"><span><i>UPM</i> {UPM}</span><span><i>cell</i> {CELL} u = size/8</span><span><i>cap</i> 7 cells</span><span><i>x-height</i> 4</span><span><i>descender</i> 2</span><span><i>whole pixels at</i> 16 · 32 · 48 · 72 · 120 px</span><span><i>glyphs</i> {len(reg)}</span></div>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.2 · Waterfall · house steps</span><span class="lab">Regular</span></div>
  {water}
  <p class="cap">At 16, 32, 48, 72 and 120 px a cell is 2, 4, 6, 9 and 15 device pixels, and the text has no anti-aliased pixels. Below 16 px, set IBM Plex Mono.</p>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.3 · Three styles</span><span class="lab">Regular · Bold · Grid</span></div>
  {styles}
  <p class="cap">Bold doubles every vertical stroke and keeps horizontals at one cell. Grid draws each cell as its own square; its gap is half a cell up to 40 px and a third from 48 px, set by the browser's optical size.</p>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.4 · Character set</span><span class="lab">{len(chars)} characters</span></div>
  <p class="px chars">{esc(chars)}</p>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.5 · House vocabulary</span><span class="lab">32 px</span></div>
  <ul>{vocab}</ul>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.6 · Private use · the mark and the pantry</span><span class="lab">U+E000–E007</span></div>
  <div class="pua">{puas}</div>
  <p class="cap">Read from src/house.json at build time, so the font matches the house SVGs.</p>
</section>
<section class="plate">
  <div class="head"><span class="lab">Plate 1.7 · Use</span><span class="lab">CSS</span></div>
  <table><tr><th>size</th><th>cell</th><th>use</th></tr>
  <tr><td>16 px</td><td>2 px</td><td>labels on splashes and HUDs, caps only</td></tr>
  <tr><td>32 px</td><td>4 px</td><td>in-game readouts</td></tr>
  <tr><td>48 px</td><td>6 px</td><td>HUD numerals, spec callouts; smallest size for Grid</td></tr>
  <tr><td>72 px</td><td>9 px</td><td>splash and title-card words</td></tr>
  <tr><td>120 px</td><td>15 px</td><td>one display numeral or the typed mark</td></tr></table>
  <p class="cap">Set line-height: 1 and the line box runs from the cap line to one cell under the baseline. Keep letter-spacing at 0 and start text on a whole pixel.</p>
</section>
<p class="lab">Copyright {2026} David Hatley · SIL Open Font License 1.1 · design · AI/ML · generative tools</p>
</main></body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(OUT, f"{OUT.stat().st_size // 1024} KB")
