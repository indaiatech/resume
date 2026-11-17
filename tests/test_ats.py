from pathlib import Path
import tempfile
import unittest

import pymupdf as fitz

from resume_tool.ats import check_pdf


class PdfChecksTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "resume.pdf"

    def write_pdf(self, text=None, **save_options):
        with fitz.open() as document:
            page = document.new_page()
            if text:
                page.insert_text((60, 60), text, fontsize=11)
            document.save(self.path, **save_options)

    def codes(self, result):
        return {finding["code"] for finding in result["findings"]}

    def test_textless_document_is_a_zero_score_blocker(self):
        self.write_pdf()
        result = check_pdf(self.path)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["extracted_text"], "")
        blocker = next(item for item in result["findings"] if item["code"] == "empty_text_layer")
        self.assertEqual(blocker["severity"], "blocker")
        self.assertEqual(blocker["page"], 1)
        self.assertIn("OCR", blocker["message"])

    def test_selectable_text_is_extracted_and_expected_checks_pass(self):
        self.write_pdf(
            "Alex Example\nalex@example.com\n+55 (11) 99999-1234\n"
            "Experience\nEngineer at Example, Jan 2020 - Present\n"
            "Education\nEngineering 2015-2019\nSkills\nPython and SQL"
        )
        result = check_pdf(self.path)
        self.assertIn("Engineer at Example", result["extracted_text"])
        self.assertIn("alex@example.com", result["extracted_text"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result, check_pdf(self.path))
        self.assertIn("not a probability", result["disclaimer"])

    def test_portuguese_headings_and_numeric_dates(self):
        self.write_pdf(
            "Ana Example\nana@example.com\n+55 19 99999-1234\n"
            "Experiência profissional\nEngenheira 01/2020 - Atual\nFormação acadêmica"
        )
        result = check_pdf(self.path)
        self.assertNotIn("missing_headings", self.codes(result))
        self.assertNotIn("missing_dates", self.codes(result))

    def test_year_range_does_not_count_as_a_phone(self):
        self.write_pdf("Experience\nEngineer 2020-2024\nalex@example.com")
        result = check_pdf(self.path)
        self.assertIn("missing_phone", self.codes(result))
        self.assertNotIn("missing_dates", self.codes(result))

    def test_empty_page_caps_otherwise_readable_document(self):
        with fitz.open() as document:
            page = document.new_page()
            page.insert_text((60, 60), "Experience\nEngineer 2020-2024\nalex@example.com\n+55 19 99999-1234")
            document.new_page()
            document.save(self.path)
        result = check_pdf(self.path)
        self.assertLessEqual(result["score"], 20)
        self.assertIn("Engineer", result["extracted_text"])
        self.assertEqual(next(item["page"] for item in result["findings"] if item["code"] == "empty_text_layer"), 2)

    def test_columns_require_repeated_side_by_side_lines(self):
        with fitz.open() as document:
            page = document.new_page()
            page.insert_text((50, 80), "Left column\nPython\nSQL\nLinux", fontsize=11)
            page.insert_text((330, 80), "Right column\nEngineer\nEducation\nProjects", fontsize=11)
            document.save(self.path)
        self.assertIn("possible_columns", self.codes(check_pdf(self.path)))

    def test_tiny_and_invisible_text_are_reported(self):
        with fitz.open() as document:
            page = document.new_page()
            page.insert_text((60, 60), "Very small text", fontsize=5)
            page.insert_text((60, 100), "Hidden keywords", render_mode=3)
            page.insert_text((60, 140), "White keywords", color=(1, 1, 1))
            document.save(self.path)
        codes = self.codes(check_pdf(self.path))
        self.assertIn("tiny_fonts", codes)
        self.assertIn("invisible_text", codes)
        self.assertIn("white_text", codes)

    def test_encrypted_pdf_has_actionable_error(self):
        self.write_pdf("Private resume", encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="reader")
        with self.assertRaisesRegex(ValueError, "Encrypted PDF.*decrypted copy"):
            check_pdf(self.path)

    def test_invalid_pdf_has_actionable_error(self):
        self.path.write_bytes(b"%PDF-1.7\ncorrupt document")
        with self.assertRaisesRegex(ValueError, "corrupt.*re-export"):
            check_pdf(self.path)

    def test_non_pdf_and_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            check_pdf(self.path)
        self.path.write_text("not a PDF", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Not a PDF.*export"):
            check_pdf(self.path)

    def test_iso_month_dates_match_the_generated_resume_format(self):
        self.write_pdf("Experience\nEngineer 2021-03 – Present\nalex@example.com")
        self.assertNotIn("missing_dates", self.codes(check_pdf(self.path)))
