"""kern: whole-cell class kerning derived from the glyph drawings, plus spacing tests.

Profiles. For each glyph and each of the 9 rows we take the white space between the ink and the glyph's
right edge (its advance) and between its left edge and the ink. For a pair L R, the gap at a row is
L.right[r] + R.left[r']; we take the smallest gap over all rows r, r' with |r - r'| <= 1, so cells that
would touch diagonally count as touching. Two straight stems (HH, nn) sit 1 cell apart: that is the rhythm.

Rule (cells). Over the rows where both glyphs have ink (within the one-row window), take the gap per row
(capped at 6) and average it: that is how open the pair looks.
  * mean gap under 3      -> no kern (HH, nn, rn, Et: on rhythm or open by the glyph's own shape)
  * mean gap 3 to 5       -> -1   (To, Fa, r., Te)
  * mean gap 5 or more    -> -2   (LT, P., L')
  * never closer than 1 cell at the tightest row (min gap + kern >= 1), so nothing touches, even diagonally
  * never into a mouth: the right glyph may tuck under an arm (To, LT) but not into a space the left glyph
    closes above and below (C-, E-), where it would read as one glyph
  * no rows within reach  -> -1, only when one side is a quote, period or comma (." ’s)
Only letters and the punctuation in PUNCT take part. Figures never kern, so tables stay tabular.
Left glyphs are grouped into classes by identical right profiles and right glyphs by identical left
profiles, so the GPOS is a small class table. The MANUAL block of each file survives --write and wins.
"""
import difflib
from . import SRC
from .fontbuild import sources, bold_set

PUNCT = {"period", "comma", "colon", "semicolon", "quoteright", "quoteleft", "quotedblleft", "quotedblright",
         "quotesingle", "quotedbl", "ellipsis", "hyphen", "exclam", "question", "parenright", "parenleft"}
SMALL = {"period", "comma", "quoteright", "quoteleft", "quotedblleft", "quotedblright", "quotesingle", "quotedbl"}
INF = 99
SPACING_TESTS = ["nnonnn", "HHOHH", "ooxoo", "nnannennn", "HHAHHEHH", "minimum", "To LT r. Fa"]
MANUAL_MARK = "# == MANUAL"


def kernable(g):
    if not g.rows or not g.cps or g.tabular or g.source:
        return False
    ch = chr(g.cps[0])
    return ch.isalpha() and ch.isascii() or g.name in PUNCT


def profiles(g):
    """(left[9], right[9]) white cells from each edge to the ink, INF where the row is empty."""
    L, R = [], []
    for row in g.rows:
        if "X" in row:
            L.append(g.lsb + row.index("X"))
            R.append(g.advance - g.lsb - row.rindex("X") - 1)
        else:
            L.append(INF); R.append(INF)
    return tuple(L), tuple(R)


def min_gap(right, left):
    best = INF
    for r in range(9):
        if right[r] >= INF:
            continue
        for r2 in (r - 1, r, r + 1):
            if 0 <= r2 < 9 and left[r2] < INF:
                best = min(best, right[r] + left[r2])
    return best


CAP_GAP = 6


def mean_gap(right, left):
    """Average windowed gap over the rows where the right-hand glyph has ink."""
    rows = []
    for r in range(9):
        if left[r] >= INF:
            continue
        near = [right[r2] for r2 in (r - 1, r, r + 1) if 0 <= r2 < 9 and right[r2] < INF]
        if near:
            rows.append(min(CAP_GAP, min(near) + left[r]))
    return sum(rows) / len(rows) if rows else INF


def enclosed(right, left, k):
    """True if, kerned by k, the right glyph's ink enters a column span the left glyph closes above and below.
    Positions are measured inward from the left glyph's advance edge (its right profile)."""
    for r in range(9):
        if left[r] >= INF:
            continue
        depth = -k - left[r]          # how far this row's ink reaches past the left glyph's advance edge
        if depth <= 0:
            continue
        reach = lambda rr: right[rr] < INF and right[rr] < depth   # left glyph's ink extends past that point
        if any(reach(rr) for rr in range(0, r)) and any(reach(rr) for rr in range(r + 1, 9)):
            return True
    return False


def rule(gap, mean, a, b, right=None, left=None):
    if gap >= INF:
        return -1 if (a in SMALL or b in SMALL) else 0
    k = 0 if mean < 3 else (-1 if mean < 5 else -2)
    k = max(k, 1 - gap)  # never closer than 1 cell
    while k < 0 and right is not None and enclosed(right, left, k):
        k += 1
    return k


def derive(glyphs):
    ks = [g for g in glyphs.values() if kernable(g)]
    prof = {g.name: profiles(g) for g in ks}
    lcls, rcls = {}, {}
    for g in ks:
        lcls.setdefault(prof[g.name][1], []).append(g.name)   # left side of a pair: its right profile
        rcls.setdefault(prof[g.name][0], []).append(g.name)   # right side of a pair: its left profile
    pairs = []
    for rp, lnames in lcls.items():
        for lp, rnames in rcls.items():
            gap, mean = min_gap(rp, lp), mean_gap(rp, lp)
            # punctuation exceptions decided per glyph; split a class only when the rule disagrees
            vals = {(a, b): rule(gap, mean, a, b, rp, lp) for a in lnames for b in rnames}
            if len(set(vals.values())) == 1:
                v = next(iter(vals.values()))
                if v:
                    pairs.append((tuple(lnames), tuple(rnames), v, gap, mean))
            else:
                for (a, b), v in vals.items():
                    if v:
                        pairs.append(((a,), (b,), v, gap, mean))
    return pairs


def render_file(style, pairs, manual):
    names, out = {}, []

    def cname(members, side):
        if len(members) == 1:
            return members[0]
        key = (side, members)
        if key not in names:
            names[key] = f"{side}{len([k for k in names if k[0] == side]) + 1}"
            out.append(f"class {names[key]} = {' '.join(members)}")
        return names[key]
    body = []
    for l, r, v, gap, mean in sorted(pairs, key=lambda p: (p[2], p[0], p[1])):
        a, b = cname(l, "L"), cname(r, "R")
        why = f"min {gap} -> {gap + v}, mean {mean:.1f}" if gap < INF else "no shared rows"
        body.append(f"kern {a} {b} {v}   # {why}")
    head = [f"# kern-{style.lower()}.txt: whole-cell kerning for Stem 7 {style} (values in cells; 1 cell = 300 units).",
            "# The AUTO block is written by `stemctl kern --write` from the glyph drawings (rule in s7lib/kern.py).",
            "# Put hand decisions in the MANUAL block as `kern <glyph> <glyph> <cells>`: it survives --write and wins.",
            "# == AUTO"]
    return "\n".join(head + out + body) + "\n\n" + (manual or f"{MANUAL_MARK}\n")


def split_manual(text):
    i = text.find(MANUAL_MARK)
    return (text[:i], text[i:]) if i >= 0 else (text, "")


def sample_pairs(style, glyphs):
    """Strings for the proof: one sample per kern line (first members of each class) plus real words."""
    p = SRC / f"kern-{style.lower()}.txt"
    if not p.exists():
        return ["To", "LT", "r.", "Fa"]
    classes, out = {}, []
    ch = {g.name: chr(g.cps[0]) for g in glyphs.values() if g.cps}
    for raw in p.read_text().splitlines():
        line = raw.split("#", 1)[0].split()
        if not line:
            continue
        if line[0] == "class":
            classes[line[1]] = line[3:]
        elif line[0] == "kern":
            a = classes.get(line[1], [line[1]])[0]
            b = classes.get(line[2], [line[2]])[0]
            s = ch.get(a, "") + ch.get(b, "")
            if s not in out:
                out.append(s)
    return out[:40] + ["Today", "LTD", "for.", "Farm", "“Tile”", "end.”", "it’s"]


def spacing_report(glyphs):
    G = {chr(cp): g for g in glyphs.values() for cp in g.cps}
    lines = []
    for s in SPACING_TESTS:
        gaps = []
        for a, b in zip(s, s[1:]):
            if a == " " or b == " ":
                gaps.append("_")
                continue
            gaps.append(str(min_gap(profiles(G[a])[1], profiles(G[b])[0])))
        lines.append(f"  {s:14} gaps {' '.join(gaps)}")
    return lines


def main(a):
    reg, bold_src = sources()
    bold, _ = bold_set(reg, bold_src)
    styles = [a.style] if getattr(a, "style", None) else ["Regular", "Bold"]
    stale = 0
    for st in styles:
        gl = reg if st == "Regular" else bold
        pairs = derive(gl)
        path = SRC / f"kern-{st.lower()}.txt"
        old = path.read_text() if path.exists() else ""
        _, manual = split_manual(old)
        new = render_file(st, pairs, manual)
        n_glyph_pairs = sum(len(p[0]) * len(p[1]) for p in pairs)
        print(f"{st}: {len(pairs)} kern lines covering {n_glyph_pairs} glyph pairs")
        print("\n".join(spacing_report(gl)))
        if new != old:
            if getattr(a, "write", False):
                path.write_text(new)
                print(f"  wrote {path.relative_to(SRC.parent.parent.parent)}")
            else:
                stale += 1
                diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), "on disk", "derived", lineterm="", n=0))
                print(f"  {path.name} is out of date ({len(diff)} diff lines); run `stemctl kern --write`")
    return 1 if (stale and getattr(a, "check", False)) else 0
