"""Independent, deterministic 80/20 PDF readability checks, not an ATS emulator.

Reactive Resume's MIT source was inspected at commit
602578f75edb77b739ea4e18bc3adbb94cb35c30:
https://github.com/reactive-resume/reactive-resume/tree/602578f75edb77b739ea4e18bc3adbb94cb35c30/packages/resume/src/ats-pdf
Its TypeScript analyzer is browser-independent; its PDF.js extraction adapter is
in apps/web/src/features/ats-checker/extract-client.ts. Reusing it would require
a JavaScript runtime and its extraction schema, not just a Python dependency.
This pdfplumber and pdfium implementation does not copy or claim to run that engine.

The score sums remaining points across text (40), layout (20), contact (20),
sections (10), and dates (10). Deductions are declared at each finding below;
textless documents score zero and any textless page caps the score at 20.
No OCR, network requests, or claims about a particular employer's parser.
"""

import ctypes
from pathlib import Path
import re
import unicodedata

import pypdfium2 as pdfium
import pypdfium2_raw as pdfium_c
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTTextContainer
from pdfminer.pdfdocument import PDFEncryptionError
from pdfminer.pdfparser import PDFSyntaxError
from pypdfium2 import PdfiumError


DISCLAIMER = (
    "Independent 80/20 PDF readability heuristics, not the Reactive Resume engine. "
    "The score is not a probability of acceptance or proof of compatibility with any ATS. "
    "No OCR is performed. Columns, headings, contact details, and dates are heuristics; "
    "hidden-text inspection detects invisible rendering, zero opacity, and white text, "
    "not all clipping, overlays, background colors, or reading-order problems. "
    "Review extracted_text against the visible PDF."
)
_BUDGETS = {"text": 40, "layout": 20, "contact": 20, "sections": 10, "dates": 10}
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE)
_PHONE = re.compile(r"(?<!\w)\+?\d[\d ().-]{6,}\d(?!\w)")
_YEAR = r"(?:19|20)\d{2}"
_DATE_RANGE = re.compile(
    rf"\b{_YEAR}\b\s*(?:[-–—]|to|a|ate)\s*(?:{_YEAR}\b|present\b|current\b|atual\b|presente\b)",
    re.IGNORECASE,
)
_DATED = re.compile(
    rf"\b{_YEAR}-(?:0[1-9]|1[0-2])\b|"
    rf"\b(?:0?[1-9]|1[0-2])[/.-]{_YEAR}\b|"
    rf"\b(?:jan(?:uary|eiro)?|feb(?:ruary)?|fev(?:ereiro)?|mar(?:ch|co)?|"
    rf"apr(?:il)?|abr(?:il)?|may|maio|jun(?:e|ho)?|jul(?:y|ho)?|"
    rf"aug(?:ust)?|ago(?:sto)?|sep(?:tember)?|set(?:embro)?|"
    rf"oct(?:ober)?|out(?:ubro)?|nov(?:ember|embro)?|dec(?:ember)?|dez(?:embro)?)"
    rf"\.?\s+(?:de\s+)?{_YEAR}\b",
    re.IGNORECASE,
)
_HEADINGS = {
    "experience", "work experience", "professional experience", "employment history",
    "education", "skills", "technical skills", "summary", "professional summary",
    "projects", "certifications", "languages", "experiencia", "experiencia profissional",
    "historico profissional", "formacao", "formacao academica", "educacao",
    "habilidades", "competencias", "competencias tecnicas", "resumo", "resumo profissional",
    "objetivo", "projetos", "certificacoes", "idiomas",
}


def _normalize(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )


def _has_columns(lines: list[tuple], width: float) -> bool:
    # shortcut: repeated side-by-side lines suggest columns, not semantic reading order; inspect extraction manually.
    for fraction in (0.35, 0.45, 0.5, 0.55, 0.65):
        middle = width * fraction
        left = [box for box in lines if box[2] <= middle - 12]
        right = [box for box in lines if box[0] >= middle + 12]
        if len(left) < 3 or len(right) < 3:
            continue
        aligned = [
            box for box in left
            if any(min(box[3], other[3]) > max(box[1], other[1]) for other in right)
        ]
        if len(aligned) >= 3 and max(box[3] for box in aligned) - min(box[1] for box in aligned) >= 36:
            return True
    return False


def check_pdf(path: Path) -> dict:
    """Return JSON-safe score, categories, findings, extracted_text and disclaimer.

    categories maps category names to score/max_score/findings. Each finding has
    code, severity (blocker/warning), message, category, and optional 1-based page.
    Missing/unreadable files raise OSError. Invalid, encrypted, or unextractable
    PDFs raise actionable ValueError; no output file is written.
    """
    categories = {
        name: {"score": budget, "max_score": budget, "findings": []}
        for name, budget in _BUDGETS.items()
    }
    findings = []

    def add(category: str, code: str, severity: str, message: str, points: int, page=None):
        finding = {"code": code, "severity": severity, "message": message, "category": category}
        if page is not None:
            finding["page"] = page
        findings.append(finding)
        bucket = categories[category]
        bucket["findings"].append(finding)
        bucket["score"] = max(0, bucket["score"] - points)

    # Open through Python first so missing files and permission errors retain their useful OSError types.
    with path.open("rb") as stream:
        header = stream.read(1024)
    if b"%PDF-" not in header:
        raise ValueError("Not a PDF: export the source document as PDF and try again.")
    pages_text = []
    empty_pages = []
    try:
        for number, page_layout in enumerate(extract_pages(path, laparams=LAParams()), 1):
            lines = [line for element in page_layout if isinstance(element, LTTextContainer) for line in element]
            text = "\n".join(line.get_text().strip() for line in lines)
            pages_text.append(text)
            if not any(char.isalnum() for char in text):
                empty_pages.append(number)
                add("text", "empty_text_layer", "blocker", "No usable text layer on this page. Export selectable text or run OCR locally, then check again.", 40, number)
            if "\ufffd" in text:
                add("text", "replacement_characters", "warning", "Extracted text contains Unicode replacement characters; check font encoding and re-export.", 15, number)
            if any(isinstance(char, LTChar) and char.size < 8 for line in lines for char in line):
                add("layout", "tiny_fonts", "warning", "Some text is smaller than 8 points; use a readable body font and inspect extraction.", 5, number)
            if _has_columns([line.bbox for line in lines], page_layout.width):
                add("layout", "possible_columns", "warning", "At least three vertically overlapping text lines occur on each side of a 24-point gutter. Possible columns may interleave; inspect extracted text order.", 10, number)
        if not pages_text:
            raise ValueError("The PDF has no pages: export it again from the source document.")
        # pdfium exposes text render mode and fill alpha, which pdfminer does not.
        traced = pdfium.PdfDocument(path)
        try:
            for number, page in enumerate(traced, 1):
                text_page = page.get_textpage()
                invisible = white_text = False
                for index in range(pdfium_c.FPDFText_CountChars(text_page.raw)):
                    text_object = pdfium_c.FPDFText_GetTextObject(text_page.raw, index)
                    if not text_object:
                        continue
                    render_mode = pdfium_c.FPDFTextObj_GetTextRenderMode(text_object)
                    measured = [ctypes.c_uint() for _ in range(4)]
                    pdfium_c.FPDFText_GetFillColor(text_page.raw, index, *(ctypes.byref(value) for value in measured))
                    red, green, blue, alpha = (value.value / 255 for value in measured)
                    invisible |= render_mode == 3 or alpha < 0.01
                    white_text |= render_mode != 3 and alpha >= 0.01 and min(red, green, blue) >= 0.98
                if invisible:
                    add("text", "invisible_text", "warning", "Invisible or zero-opacity text is present. It may be an OCR layer; verify it matches the visible resume.", 10, number)
                if white_text:
                    add("text", "white_text", "warning", "White text is present; it may be legitimate on a dark background or hidden on white. Check visually.", 5, number)
        finally:
            traced.close()
    except PDFEncryptionError:
        raise ValueError("Encrypted PDF: save a decrypted copy locally before checking it.") from None
    except (PDFSyntaxError, PdfiumError, RuntimeError) as error:
        raise ValueError("The PDF is corrupt or could not be extracted; re-export it from the source document.") from error

    text = "\n\f\n".join(pages_text)
    if not _EMAIL.search(text):
        add("contact", "missing_email", "warning", "No recognizable email address in the text layer; include a visible plain-text address.", 10)
    phones = _PHONE.findall(text)
    if not any(
        8 <= sum(char.isdigit() for char in phone) <= 15
        and not re.fullmatch(rf"{_YEAR}\s*[-.]\s*{_YEAR}", phone)
        and not re.fullmatch(r"\d{4}[.-]\d{2}[.-]\d{2}", phone)
        for phone in phones
    ):
        add("contact", "missing_phone", "warning", "No recognizable 8–15 digit phone number in the text layer; include country and area codes.", 10)
    normalized = _normalize(text)
    headings = {
        line.strip().rstrip(":").strip()
        for line in normalized.splitlines()
        if len(line.strip()) <= 60
    }
    if not headings.intersection(_HEADINGS):
        add("sections", "missing_headings", "warning", "No conventional English or Portuguese section heading was recognized on its own line; use headings such as Experience, Education, Experiência profissional or Formação.", 10)
    if not (_DATE_RANGE.search(normalized) or _DATED.search(normalized)):
        add("dates", "missing_dates", "warning", "No recognizable year range or month/year date found; use dates such as 2020–2024, Jan 2020 or 01/2020 for chronology. This does not validate employment order.", 10)
    score = sum(category["score"] for category in categories.values())
    if empty_pages:
        score = min(score, 20)
    if not any(char.isalnum() for char in text):
        score = 0
    return {
        "score": score,
        "categories": categories,
        "findings": findings,
        "extracted_text": text,
        "disclaimer": DISCLAIMER,
    }
