"""Minimal PDF fixture helpers replacing the PyMuPDF test utilities.

Coordinates follow the previous PyMuPDF convention: origin at the top-left of an
A4 page, y growing downward. save() translates them to reportlab's bottom-up axis.
"""
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

PAGE = (595, 842)  # A4 in points, matching the previous fixtures


class PdfBuilder:
    """Collects insert_text calls per page, mirroring the old fitz workflow."""

    def __init__(self):
        self._pages = [[]]

    def add_page(self):
        self._pages.append([])
        return self

    def insert_text(self, point, text, fontsize=11, color=(0, 0, 0), alpha=1.0, render_mode=0):
        for offset, line in enumerate(text.splitlines() or [""]):
            self._pages[-1].append((point[0], point[1] + offset * fontsize * 1.2, line, fontsize, color, alpha, render_mode))
        return self

    def save(self, path):
        document = canvas.Canvas(str(path), pagesize=PAGE)
        for page in self._pages:
            for x, y, text, fontsize, color, alpha, render_mode in page:
                style = document.beginText(x, PAGE[1] - y)
                style.setFont("Helvetica", fontsize)
                style.setFillColor(Color(*color, alpha=alpha))
                style.setTextRenderMode(render_mode)
                if render_mode == 0:
                    # PDF text state persists across text objects and reportlab skips
                    # emitting the default operator; force it or later text inherits.
                    style._code.append("0 Tr")
                style.textLine(text)
                document.drawText(style)
            document.showPage()
        document.save()


def encrypt_pdf(path, destination, user_password="reader", owner_password="owner"):
    import pypdf

    writer = pypdf.PdfWriter(clone_from=str(path))
    writer.encrypt(user_password=user_password, owner_password=owner_password, algorithm="RC4-128")
    writer.write(str(destination))
