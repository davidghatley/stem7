"""Stem 7 font tools: source format, builder, linter, kerning, crispness test, proofs and specimen."""
import pathlib

FONT_DIR = pathlib.Path(__file__).resolve().parent.parent          # tools/
ROOT = FONT_DIR.parent                                               # repo root
SRC = ROOT / "src"                                                   # glyph sources
OUT = ROOT / "fonts"                                                 # built fonts
