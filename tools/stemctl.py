#!/usr/bin/env python3
"""stemctl: build, lint, kern, test and proof Stem 7.

    python tools/stemctl.py <command> [options]

Commands
    build        fonts/Stem7-{Regular,Bold,Grid}.{ttf,woff2} from src/*.s7
    lint         glyph checks (rows, vertical lines, stems, side bearings, charset, duplicates, ligatures)
    kern         derive whole-cell class kerning -> src/kern-{regular,bold}.txt, print spacing tests
    crisp        render every house step in headless Chromium and count anti-aliased pixels
    proof        PNG proof sheets (light and dark) -> proofs/
    specimen     self-contained HTML specimen (fonts inlined) -> proofs/specimen.html
    review       source bitmaps at big cells, no browser -> proofs/review-*.png
    compare      set strings in an older build and the current one, side by side (PNG)
    diff         before/after crops of changed glyphs against an older .s7 file
    draft-bold   append auto-bold drafts for glyphs missing from src/bold.s7
    all          build, lint, kern --check, crisp, proof, specimen

Run `stemctl.py <command> -h` for options. CPU only; Chromium runs with --headless=new --disable-gpu.
"""
import argparse, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def cmd_build(a):
    from s7lib import fontbuild
    for line in fontbuild.build(a.styles):
        print(line)


def cmd_lint(a):
    from s7lib import lint
    return lint.main(a)


def cmd_kern(a):
    from s7lib import kern
    return kern.main(a)


def cmd_crisp(a):
    from s7lib import crisp
    return crisp.main(a)


def cmd_proof(a):
    from s7lib import proof
    return proof.main(a)


def cmd_specimen(a):
    from s7lib import specimen
    return specimen.main(a)


def cmd_draft_bold(a):
    from s7lib import fontbuild, boldrule, source
    from s7lib import SRC
    reg, bold = fontbuild.sources()
    path = SRC / "bold.s7"
    missing = [n for n in reg if n not in bold]
    if not missing:
        print("bold.s7 already has every glyph")
        return 0
    drafts = {n: boldrule.embolden(reg[n]) for n in missing}
    for d in drafts.values():
        d.note = ["auto-bold draft: review and redraw"]
    pre = "" if path.exists() else (
        "# Stem 7 Bold: glyph source. Same format as regular.s7.\n"
        "# Rule: vertical stems are 2 cells, horizontals stay 1 cell; widen rather than close a counter.\n"
        "# Figures are tabular at 7 cells. The mark and the pantry glyphs are the same drawings as Regular.")
    text = source.dump(drafts, pre)
    with open(path, "a") as f:
        f.write(("\n" if path.exists() else "") + text)
    print(f"appended {len(drafts)} drafts to {path}")


def cmd_review(a):
    from s7lib import fontbuild, bitmap
    from s7lib.proof import PROOFS
    reg, bold = fontbuild.sources()
    gl = reg if a.style == "Regular" else fontbuild.bold_set(reg, bold)[0]
    names = a.glyphs or list(gl)
    for th in ("light",) + (("dark",) if a.dark else ()):
        im = bitmap.sheet([gl[n] for n in names], a.cell, theme=th, title=f"STEM 7 {a.style.upper()} · SOURCE REVIEW · {a.cell} PX CELLS")
        out = pathlib.Path(a.out) if a.out else PROOFS / f"review-{a.style.lower()}-{th}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out)
        print(out)


def cmd_diff(a):
    from s7lib import fontbuild, bitmap, source, house
    reg, bold = fontbuild.sources()
    new = reg if a.style == "Regular" else fontbuild.bold_set(reg, bold)[0]
    old = source.parse(a.old, house.load())
    names = a.glyphs or [n for n in new if n in old and (old[n].rows != new[n].rows or old[n].lsb != new[n].lsb or old[n].rsb != new[n].rsb)]
    im = bitmap.diff_image(old, new, names, a.cell, title=a.title or f"BEFORE > AFTER · {len(names)} GLYPHS")
    if im is None:
        print("no changed glyphs")
        return 0
    im.save(a.out)
    print(a.out, " ".join(names))


def cmd_compare(a):
    from s7lib import proof
    print(proof.compare(a.before, a.strings, a.out, weight=a.weight, title=a.title or "BEFORE / AFTER"))




def cmd_all(a):
    for f, extra in ((cmd_build, dict(styles=["Regular", "Bold", "Grid"])), (cmd_lint, dict(strict=False)),
                     (cmd_kern, dict(write=False, check=True, style=None)),
                     (cmd_crisp, dict(styles=None, sizes=None, out=None)), (cmd_proof, dict(only=None)),
                     (cmd_specimen, dict())):
        print(f"\n== {f.__name__[4:]} ==")
        rc = f(argparse.Namespace(**extra))
        if rc:
            return rc


def main():
    p = argparse.ArgumentParser(prog="stemctl", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the fonts")
    b.add_argument("--styles", nargs="+", default=["Regular", "Bold", "Grid"], choices=["Regular", "Bold", "Grid"])
    b.set_defaults(f=cmd_build)
    l = sub.add_parser("lint", help="glyph checks")
    l.add_argument("--strict", action="store_true", help="treat warnings as errors")
    l.set_defaults(f=cmd_lint)
    k = sub.add_parser("kern", help="derive whole-cell kerning")
    k.add_argument("--write", action="store_true", help="rewrite src/kern-*.txt (keeps the manual block)")
    k.add_argument("--check", action="store_true", help="fail if the kern files are out of date")
    k.add_argument("--style", choices=["Regular", "Bold"], help="one style only")
    k.set_defaults(f=cmd_kern)
    c = sub.add_parser("crisp", help="anti-aliasing test in headless Chromium")
    c.add_argument("--styles", nargs="+", choices=["Regular", "Bold", "Grid"])
    c.add_argument("--sizes", nargs="+", type=int, help="px sizes (default: every house step)")
    c.add_argument("--out", help="also write the result table as JSON to this path")
    c.set_defaults(f=cmd_crisp)
    pr = sub.add_parser("proof", help="PNG proof sheets")
    pr.add_argument("--only", nargs="+", help="sheet names (charset, waterfall, spacing, kerning, vocabulary, pua, bold, grid)")
    pr.set_defaults(f=cmd_proof)
    s = sub.add_parser("specimen", help="self-contained HTML specimen")
    s.set_defaults(f=cmd_specimen)
    d = sub.add_parser("draft-bold", help="append auto-bold drafts to bold.s7")
    d.set_defaults(f=cmd_draft_bold)
    rv = sub.add_parser("review", help="source bitmaps at big cells (no browser)")
    rv.add_argument("--style", default="Regular", choices=["Regular", "Bold"])
    rv.add_argument("--glyphs", nargs="+")
    rv.add_argument("--cell", type=int, default=10)
    rv.add_argument("--dark", action="store_true")
    rv.add_argument("-o", "--out")
    rv.set_defaults(f=cmd_review)
    df = sub.add_parser("diff", help="before/after crops against an older .s7 file")
    df.add_argument("old")
    df.add_argument("--style", default="Regular", choices=["Regular", "Bold"])
    df.add_argument("--glyphs", nargs="+")
    df.add_argument("--cell", type=int, default=10)
    df.add_argument("--title")
    df.add_argument("-o", "--out", required=True)
    df.set_defaults(f=cmd_diff)
    cp = sub.add_parser("compare", help="set strings with an older fonts dir and the current fonts, side by side")
    cp.add_argument("before", help="directory holding the older Stem7-*.woff2")
    cp.add_argument("strings", nargs="+", help="'size:text', e.g. '48:SEED 4127'")
    cp.add_argument("--weight", type=int, default=400)
    cp.add_argument("--title")
    cp.add_argument("-o", "--out", required=True)
    cp.set_defaults(f=cmd_compare)
    al = sub.add_parser("all", help="build, lint, kern --check, crisp, proof, specimen")
    al.set_defaults(f=cmd_all)
    a = p.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == "__main__":
    main()
