"""Word count of the PDD as the handbook defines it: section 1 up to References (tables included),
excluding the cover page, references and Appendix A. Run: python3 count_words.py"""
from docx import Document
from docx.oxml.ns import qn


def blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield "".join(t.text or "" for t in child.iter(qn("w:t")))
        elif child.tag == qn("w:tbl"):
            yield " ".join(t.text or "" for t in child.iter(qn("w:t")))


counting, words = False, 0
for text in blocks(Document("AegisRAG-Project-Definition-Document.docx")):
    if text.startswith("1 Problem to be solved"):
        counting = True
    if text.strip() == "References":
        break
    if counting:
        words += len(text.split())
print(words)
