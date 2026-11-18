"""Pre-download the Typst Universe packages used by the templates."""

import pathlib
import tempfile

import typst

DOC = """\
#import "@preview/tech-focused-resume:0.1.2": *
#import "@preview/exp-cover-letter:0.1.0": *
"""

with tempfile.TemporaryDirectory() as directory:
    source = pathlib.Path(directory) / "warm.typ"
    source.write_text(DOC)
    typst.compile(str(source), output=str(pathlib.Path(directory) / "warm.pdf"))
print("Typst packages cached")
