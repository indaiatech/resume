from pathlib import Path

import pymupdf as fitz
import pytest
import yaml

from resume_tool.cli import extract_pdf, read_profile
from resume_tool.llm import endpoint
from resume_tool.models import MatchResult, Profile, score_match
from resume_tool.render import render_letter, render_resume


@pytest.fixture
def profile():
    return Profile.model_validate(yaml.safe_load(Path("examples/profile.yaml").read_text()))


def test_weighted_match_rejects_fabricated_evidence(profile):
    job = "Python required. Kubernetes preferred."
    result = MatchResult.model_validate({"language": "en", "requirements": [
        {"text": "Python required", "importance": "required", "assessment": "supported",
         "evidence": [{"ref": "skills:0", "quote": "Python"}], "explanation": "Listed skill."},
        {"text": "Kubernetes preferred", "importance": "desired", "assessment": "unproven",
         "evidence": [], "explanation": "Not documented."},
    ]})
    assert score_match(result, profile, job)["percentage"] == 66.7
    result.requirements[0].evidence[0].quote = "Kubernetes"
    with pytest.raises(ValueError, match="unsupported evidence"):
        score_match(result, profile, job)


def test_requirement_must_occur_in_job(profile):
    result = MatchResult.model_validate({"language": "en", "requirements": [
        {"text": "Imaginary certification", "importance": "required", "assessment": "unproven",
         "evidence": [], "explanation": "Absent."},
    ]})
    with pytest.raises(ValueError, match="verbatim"):
        score_match(result, profile, "Python required")


def test_profile_requires_explicit_review(tmp_path, profile):
    path = tmp_path / "profile.yaml"
    data = profile.model_dump()
    data["reviewed"] = False
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="reviewed: true"):
        read_profile(path)


@pytest.mark.parametrize("url", ["https://example.com", "http://127.0.0.1.evil.test", "http://user:secret@127.0.0.1:11434", "http://127.0.0.1:11434/remote"])
def test_remote_or_credentialed_model_endpoints_rejected(monkeypatch, url):
    monkeypatch.setenv("OLLAMA_URL", url)
    with pytest.raises(ValueError, match="loopback"):
        endpoint()


def test_typst_treats_profile_text_as_data_and_renders_readable_pdf(tmp_path, profile):
    data = profile.model_dump()
    data["experience"][0]["bullets"][0] = 'Literal #read("/etc/passwd") and *markup* are text.'
    output = tmp_path / "resume.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        text = "".join(page.get_text() for page in pdf)
        assert pdf.page_count == 1
        assert '#read("/etc/passwd")' in text
        assert "root:x:" not in text
        assert "Software Engineer" in text
        assert text.index("Software Engineer") < text.index("Junior Software Engineer")


def test_page_limit_does_not_replace_existing_pdf(tmp_path, profile):
    data = profile.model_dump()
    data["experience"][0]["bullets"] = ["A long factual achievement with enough text to occupy one line." for _ in range(300)]
    output = tmp_path / "resume.pdf"
    output.write_bytes(b"existing document")
    with pytest.raises(ValueError, match="limit"):
        render_resume(data, output)
    assert output.read_bytes() == b"existing document"


def test_portuguese_cover_letter_and_text_only_import_guard(tmp_path, profile):
    letter = tmp_path / "letter.pdf"
    render_letter(profile.model_dump(), ["Desenvolvi APIs em Python com PostgreSQL."], letter, "pt")
    with fitz.open(letter) as pdf:
        assert pdf.page_count == 1
        assert "Prezada equipe de recrutamento" in pdf[0].get_text()
    empty = tmp_path / "scan.pdf"
    with fitz.open() as pdf:
        pdf.new_page()
        pdf.save(empty)
    with pytest.raises(ValueError, match="OCR"):
        extract_pdf(empty)


def test_resume_wording_rejects_changed_metrics(monkeypatch, profile):
    from resume_tool import drafting
    from resume_tool.models import facts

    bullets = [
        {"ref": ref, "text": value.replace("30", "90")}
        for ref, value in facts(profile).items() if ":bullet:" in ref
    ]
    monkeypatch.setattr(drafting, "infer", lambda *args: drafting.ResumeWording.model_validate({"bullets": bullets}))
    with pytest.raises(ValueError, match="numeric facts"):
        drafting.draft_resume(profile, "en", None)


def test_two_column_pdf_is_extracted_column_by_column(tmp_path):
    source = tmp_path / "twocol.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 40), "Summary")
        page.insert_text((40, 60), "I lead engineering initiatives with reliability.")
        page.insert_text((40, 80), "acquired companies and unicorns included.")
        page.insert_text((330, 40), "Top Skills")
        page.insert_text((330, 60), "Argo")
        page.insert_text((330, 80), "MySQL")
        pdf.save(source)
    text = extract_pdf(source)
    assert "with reliability." in text
    assert text.index("initiatives with reliability.") < text.index("Top Skills")
    assert "operatingTop" not in text.replace(" ", "")


def test_import_preserves_explicit_links_omitted_by_model(tmp_path, monkeypatch):
    from resume_tool import cli
    from resume_tool.models import ImportResult

    monkeypatch.chdir(tmp_path)
    source = tmp_path / "linkedin.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 40), "Alex Example\nhttps://example.com/alex\n")
        pdf.save(source)
    monkeypatch.setattr(cli, "infer", lambda *args: ImportResult(profile=Profile(name="Alex Example")))
    destination = tmp_path / "profile.yaml"
    cli.import_profile(source, destination)
    imported = yaml.safe_load(destination.read_text())
    assert imported["links"] == ["https://example.com/alex"]
    assert imported["reviewed"] is False


@pytest.mark.parametrize("language, summary_heading, earlier_heading", [
    ("en", "Summary", "Earlier Experience"),
    ("pt", "Resumo profissional", "Experiência anterior"),
])
@pytest.mark.parametrize("selection", [None, ["sample-services"], ["example-platform"]])
def test_collapsed_resume_preserves_profile_details(
    tmp_path, profile, language, summary_heading, earlier_heading, selection
):
    from resume_tool.models import condensed, facts

    profile.summary = 'Product-minded engineer with 20 years of experience. Literal #read("/etc/passwd").'
    profile.experience[1].collapse = True
    data = Profile.model_validate(profile.model_dump()).model_dump()
    output = tmp_path / "resume.pdf"
    render_resume(data, output, language, selection)
    with fitz.open(output) as pdf:
        text = "".join(page.get_text() for page in pdf)
    assert summary_heading in text
    assert condensed(profile.summary) in condensed(text)
    assert "root:x:" not in text
    collapsed = profile.experience[1]
    assert condensed(collapsed.bullets[0]) not in condensed(text)
    if selection is None or collapsed.id in selection:
        assert earlier_heading in text
        assert text.index(summary_heading) < text.index(earlier_heading)
        for value in (collapsed.company, collapsed.title, collapsed.start, collapsed.end):
            assert value in text
    else:
        assert earlier_heading not in text
        assert collapsed.company not in text
    detailed = profile.experience[0]
    if selection is None or detailed.id in selection:
        assert condensed(detailed.bullets[0]) in condensed(text)
    else:
        assert detailed.company not in text
    assert facts(Profile.model_validate(data))[f"experience:{collapsed.id}:bullet:0"] == collapsed.bullets[0]
    assert data == profile.model_dump()


def test_collapsed_details_are_not_translated_or_discarded(monkeypatch, profile):
    from resume_tool import drafting

    profile.summary = "Product-minded engineer with 20 years of experience."
    profile.experience[1].collapse = True

    def translate(schema, prompt, payload):
        assert all(":sample-services:" not in ref for ref in payload["bullets"])
        return schema.model_validate({
            "summary": "Engenheiro com 20 anos de experiência.",
            "bullets": [{"ref": ref, "text": value} for ref, value in payload["bullets"].items()],
        })

    monkeypatch.setattr(drafting, "infer", translate)
    data = drafting.draft_resume(profile, "pt", None)
    assert data["experience"][1]["bullets"] == profile.experience[1].bullets
    assert data["experience"][1]["collapse"] is True
    assert profile.summary == "Product-minded engineer with 20 years of experience."


@pytest.mark.parametrize("summary", [None, "Engineer with 90 years of experience."])
def test_resume_wording_rejects_missing_or_changed_summary(monkeypatch, profile, summary):
    from resume_tool import drafting

    profile.summary = "Engineer with 20 years of experience."
    profile.experience = []
    monkeypatch.setattr(drafting, "infer", lambda *args: drafting.ResumeWording(bullets=[], summary=summary))
    with pytest.raises(ValueError, match="summary"):
        drafting.draft_resume(profile, "en", None)
