from pathlib import Path

import pymupdf as fitz
import pytest
import yaml

from resume_tool.cli import extract_pdf
from resume_tool.llm import endpoint
from resume_tool.models import MatchResult, Profile, score_match
from resume_tool.profile_source import read_profile
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
    data["achievements"] = ['Award text #read("/etc/passwd") is literal.']
    output = tmp_path / "resume.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        text = "".join(page.get_text() for page in pdf)
        assert pdf.page_count == 1
        assert '#read("/etc/passwd")' in text
        assert 'Award text #read("/etc/passwd")' in text
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
            assert condensed(value) in condensed(text.replace("\u00ad", ""))
    else:
        assert earlier_heading not in text
    detailed = profile.experience[0]
    if selection is None or detailed.id in selection:
        assert condensed(detailed.bullets[0]) in condensed(text)
    else:
        assert condensed(detailed.bullets[0]) not in condensed(text)
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
            "achievements": payload["achievements"],
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


def test_resume_header_centers_name_and_roles_above_one_contact_row(tmp_path, profile):
    data = profile.model_dump()
    data["headline"] = "Tech Lead | Platform AI Agents Engineer | Full Stack Engineer | SRE"
    output = tmp_path / "header.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        page = pdf[0]
        name, = page.search_for(data["name"])
        roles, = page.search_for(data["headline"])
        contacts = [page.search_for(data[field])[0] for field in ("phone", "email", "location")]
        for rect in (name, roles):
            assert (rect.x0 + rect.x1) / 2 == pytest.approx(page.rect.width / 2, abs=2)
        assert name.y1 < roles.y0
        assert roles.y1 < min(rect.y0 for rect in contacts)
        assert max(rect.y0 for rect in contacts) < min(rect.y1 for rect in contacts)


def test_long_role_lines_shrink_to_a_single_centered_line(tmp_path, profile):
    data = profile.model_dump()
    data["headline"] = "Engineering Manager | Tech Lead | Staff Software Engineer | AI Platform Engineer | SRE"
    assert len(data["headline"]) > 60
    output = tmp_path / "long-header.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        page = pdf[0]
        roles, = page.search_for(data["headline"])
        assert roles.x1 - roles.x0 < page.rect.width - 2 * 28.8
        assert (roles.x0 + roles.x1) / 2 == pytest.approx(page.rect.width / 2, abs=2)


def test_earlier_experience_groups_roles_without_losing_company_dates(tmp_path, profile):
    from resume_tool.models import condensed

    data = profile.model_dump()
    original = data["experience"][0]
    entries = [
        ("recent-dev", "Recent Studio", "Developer", "2011-01", "2012-06"),
        ("early-lead", "Platform Company", "Tech Lead", "2010-01", "2010-12"),
        ("first-dev", "International Software and Infrastructure Engineering Research and Development Services", "Developer", "2007-05", "2008-04"),
    ]
    data["experience"] = [
        {**original, "id": id_, "company": company, "title": title, "start": start,
         "end": end, "collapse": True, "bullets": ["Hidden project details remain in the profile."]}
        for id_, company, title, start, end in entries
    ]
    output = tmp_path / "earlier.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        text = "".join(page.get_text() for page in pdf)
        for page in pdf:
            for word in page.get_text("words"):
                assert 0 <= word[0] <= word[2] <= page.rect.width
    assert text.count("Developer") == 1
    assert text.count("Tech Lead") == 1
    for _, company, _, start, end in entries:
        assert condensed(f"{company} ({start} — {end})") in condensed(text.replace("\u00ad", ""))
    assert "Hidden project details" not in text


def test_stealth_and_contractor_flags_change_only_company_display(tmp_path, profile):
    data = profile.model_dump()
    data["experience"][0]["company"] = "Really Concealed Ltd"
    data["experience"][0]["stealth"] = True
    data["experience"][0]["contractor"] = True
    output = tmp_path / "stealth.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    assert "Confidential Client (NDA)" in text
    assert "Really Concealed Ltd" not in text
    assert "· Contract" in text
    assert data["experience"][0]["company"] == "Really Concealed Ltd"


def test_contractor_flag_marks_named_companies(tmp_path, profile):
    data = profile.model_dump()
    data["experience"][0]["contractor"] = True
    output = tmp_path / "contract.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    assert "Example Systems" in text and "· Contract" in text
    assert "Confidential Client" not in text


def test_earlier_layout_lines_stack_companies_and_inline_stays_joined(tmp_path, profile):
    data = profile.model_dump()
    data["experience"] = [
        {**data["experience"][0], "id": "stacked-a", "company": "Stacked Company A",
         "title": "Engineering Manager", "start": "2013-01", "end": "2014-01",
         "collapse": True, "earlier_layout": "lines",
         "bullets": ["Stacked detail A."]},
        {**data["experience"][0], "id": "stacked-b", "company": "Stacked Company B",
         "title": "Engineering Manager", "start": "2012-01", "end": "2012-12",
         "collapse": True, "earlier_layout": "lines",
         "bullets": ["Stacked detail B."]},
        {**data["experience"][0], "id": "inline-a", "company": "Inline Company A",
         "title": "Developer", "start": "2011-01", "end": "2011-12",
         "collapse": True, "bullets": ["Inline detail A."]},
        {**data["experience"][0], "id": "inline-b", "company": "Inline Company B",
         "title": "Developer", "start": "2010-01", "end": "2010-12",
         "collapse": True, "bullets": ["Inline detail B."]},
    ]
    output = tmp_path / "layout.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        lines = [line for page in pdf for line in page.get_text().splitlines()]
    stacked_lines = [line.strip() for line in lines if "Stacked Company" in line]
    inline_lines = [line.strip() for line in lines if "Inline Company" in line]
    assert len(stacked_lines) == 2 and any("Stacked Company A" in line for line in stacked_lines) and any("Stacked Company B" in line for line in stacked_lines)
    assert len(inline_lines) == 1 and "Inline Company A" in inline_lines[0] and "Inline Company B" in inline_lines[0]


@pytest.mark.parametrize("language, headings", [
    ("en", ("Education", "Languages", "Certifications", "Skills", "Selected Achievements")),
    ("pt", ("Formação acadêmica", "Idiomas", "Certificações", "Competências", "Principais conquistas")),
])
def test_resume_pairs_footer_sections_and_places_achievements_last(tmp_path, profile, language, headings):
    data = profile.model_dump()
    output = tmp_path / "footer.pdf"
    render_resume(data, output, language)
    positions = {}
    with fitz.open(output) as pdf:
        text = "".join(page.get_text() for page in pdf)
        for index, page in enumerate(pdf):
            for heading in headings:
                matches = page.search_for(heading)
                if matches and heading not in positions:
                    positions[heading] = (index, matches[0])
    for left, right in ((headings[0], headings[1]), (headings[2], headings[3])):
        left_page, left_rect = positions[left]
        right_page, right_rect = positions[right]
        assert left_page == right_page
        assert left_rect.y0 == pytest.approx(right_rect.y0, abs=1)
        assert left_rect.x0 < right_rect.x0
    assert [(positions[heading][0], positions[heading][1].y0) for heading in headings[::2]] == sorted(
        (positions[heading][0], positions[heading][1].y0) for heading in headings[::2]
    )
    assert profile.achievements[0] in text.replace("\n", " ")


@pytest.mark.parametrize("field, heading", [
    ("education", "Education"),
    ("languages", "Languages"),
    ("certifications", "Certifications"),
    ("skills", "Skills"),
])
def test_unpaired_footer_sections_render_without_empty_sections(tmp_path, profile, field, heading):
    data = profile.model_dump()
    for key in ("education", "languages", "certifications", "skills", "achievements"):
        if key != field:
            data[key] = []
    output = tmp_path / "unpaired.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        matches = [rect for page in pdf for rect in page.search_for(heading)]
        assert matches[0].x0 < pdf[0].rect.width / 4
        lines = {line.strip() for page in pdf for line in page.get_text().splitlines()}
    assert heading in lines
    assert not ({"Education", "Languages", "Certifications", "Skills", "Selected Achievements"} - {heading}) & lines


@pytest.mark.parametrize("preceding_bullets", [30, 31, 32, 33])
def test_experience_header_stays_with_its_first_bullet(tmp_path, profile, preceding_bullets):
    data = profile.model_dump()
    data["experience"][0]["bullets"] = [
        "Completed project work improving platform reliability."
    ] * preceding_bullets
    first_bullet = "Built a distinct service with measurable reliability improvements."
    data["experience"][1]["bullets"] = [first_bullet]
    output = tmp_path / "pagination.pdf"
    render_resume(data, output)
    with fitz.open(output) as pdf:
        pages = [page.get_text() for page in pdf]
    company_page = next(i for i, text in enumerate(pages) if data["experience"][1]["company"] in text)
    bullet_page = next(i for i, text in enumerate(pages) if first_bullet in text.replace("\n", " "))
    assert company_page == bullet_page
