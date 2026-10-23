"""The auto-bold rule, used to draft bold.s7 (stemctl draft-bold) and as a fallback for glyphs not drawn yet.

Rule: double every column that carries a vertical stroke (a vertical run of 2+ cells). Stems become
2 cells wide, horizontals stay 1 cell tall, and counters keep their width because the glyph grows
instead of filling in. Diagonals do not survive this rule well; draw them by hand in bold.s7.
"""
from copy import deepcopy


def stem_columns(rows):
    cols = []
    for c in range(len(rows[0])):
        run = best = 0
        for r in rows:
            run = run + 1 if r[c] == "X" else 0
            best = max(best, run)
        cols.append(best >= 2)
    return cols


def embolden(g):
    b = deepcopy(g)
    if not g.rows or g.source or g.width is not None:
        return b
    stems = stem_columns(g.rows)
    b.rows = ["".join(ch * (2 if stems[c] else 1) for c, ch in enumerate(r)) for r in g.rows]
    if g.tabular:  # figures stay tabular: every bold figure is 7 wide
        w = len(b.rows[0])
        if w < 7:
            b.rows = [r + "." * (7 - w) for r in b.rows]
    b.note = []
    return b
