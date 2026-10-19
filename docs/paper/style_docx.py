"""Post-process the Pandoc Word file: borders and a shaded header row on every table, Arial body text."""
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


def borders(table):
    props = table._tbl.tblPr
    edges = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "BFBFBF")
        edges.append(e)
    props.append(edges)
    for cell in table.rows[0].cells:
        shade = OxmlElement("w:shd")
        shade.set(qn("w:val"), "clear")
        shade.set(qn("w:fill"), "E8EEF4")
        cell._tc.get_or_add_tcPr().append(shade)


def main(path):
    doc = Document(path)
    for style in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if style in [s.name for s in doc.styles]:
            doc.styles[style].font.name = "Arial"
            doc.styles[style].font.size = Pt(10)
    for table in doc.tables:
        borders(table)
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(8.5)
    doc.save(path)


if __name__ == "__main__":
    main(sys.argv[1])
