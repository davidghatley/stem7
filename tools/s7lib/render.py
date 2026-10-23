"""Headless Chromium helpers (CPU only) and house colours from tokens.json."""
import json, subprocess, tempfile, pathlib, base64, html
from . import ROOT, OUT, FONT_DIR

CHROMIUM = "chromium"
WORK = ROOT / "proofs" / ".work"
STEPS = [11, 13, 16, 20, 25, 32, 48, 72, 120]
CRISP_STEPS = [16, 32, 48, 72, 120]


def shoot(page_html, png, width, height, budget=4000):
    """Write page_html next to the fonts' relative paths and screenshot it at width x height (1x)."""
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / (pathlib.Path(png).stem + ".html")
    src.write_text(page_html)
    png = pathlib.Path(png)
    png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [CHROMIUM, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
           f"--virtual-time-budget={budget}", f"--window-size={width},{height}", f"--screenshot={png}",
           "--no-first-run", "--no-default-browser-check", f"--user-data-dir={WORK / 'profile'}",
           "--disk-cache-size=1", src.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not png.exists():
        raise RuntimeError(f"chromium failed: {r.stderr[-800:]}")
    return png


def font_faces(inline=False, fonts_dir=OUT):
    """@font-face rules for the three styles. inline=True embeds the WOFF2 files as data: URIs."""
    rules = []
    for fam, file, weight in (("Stem 7", "Stem7-Regular.woff2", 400), ("Stem 7", "Stem7-Bold.woff2", 700),
                              ("Stem 7 Grid", "Stem7-Grid.woff2", 400)):
        p = fonts_dir / file
        # cache-bust with the file's mtime: Chromium otherwise reuses an older build of the same path
        url = ("data:font/woff2;base64," + base64.b64encode(p.read_bytes()).decode()) if inline \
            else f"{p.as_uri()}?v={p.stat().st_mtime_ns}"
        rules.append(f'@font-face {{ font-family: "{fam}"; src: url("{url}") format("woff2"); '
                     f'font-weight: {weight}; font-style: normal; font-display: block; }}')
    return "\n".join(rules)


def colours():
    """{'light': {...}, 'dark': {...}} resolved hex values from tokens.json."""
    T = json.loads((FONT_DIR / "tokens.json").read_text())
    themes = [t["id"] for t in T["color"]["themes"]]
    raw = {t["name"]: t["value"] if isinstance(t["value"], dict) else {themes[0]: t["value"]} for t in T["color"]["tokens"]}

    def res(name, th, d=0):
        v = raw[name].get(th, raw[name][themes[0]])
        return res(v[1:-1], th, d + 1) if v.startswith("{") and d < 16 else v
    return {th: {n: res(n, th) for n in raw} for th in themes}


def esc(s):
    return html.escape(s, quote=True)
