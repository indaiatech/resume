import pymupdf as fitz
import pytest
import yaml

from resume_tool import cli, drafting
from resume_tool.models import ImportResult, MatchResult, Profile, score_match


def test_achievements_can_support_job_requirements():
    profile = Profile(name="Alex Example", achievements=["Won the 2025 engineering hackathon."])
    job = "Engineering hackathon award"
    result = MatchResult.model_validate({"language": "en", "requirements": [
        {"text": job, "importance": "desired", "assessment": "supported",
         "evidence": [{"ref": "achievements:0", "quote": "2025 engineering hackathon"}],
         "explanation": "Documented award."},
    ]})
    assert score_match(result, profile, job)["percentage"] == 100


def test_achievements_only_profile_is_translated_without_changing_source(monkeypatch):
    source = "First place in the 2025 engineering hackathon."
    translated = "Primeiro lugar no hackathon de engenharia de 2025."
    profile = Profile(name="Alex Example", achievements=[source])
    monkeypatch.setattr(drafting, "infer", lambda *args: drafting.ResumeWording(
        bullets=[], achievements=[translated],
    ))
    result = drafting.draft_resume(profile, "pt", None)
    assert result["achievements"] == [translated]
    assert profile.achievements == [source]


@pytest.mark.parametrize("achievements", [
    [],
    ["Won the 2025 hackathon.", "Invented another award."],
    ["Won the 2024 hackathon."],
])
def test_wording_rejects_omitted_invented_or_changed_achievements(monkeypatch, achievements):
    profile = Profile(name="Alex Example", achievements=["Won the 2025 hackathon."])
    monkeypatch.setattr(drafting, "infer", lambda *args: drafting.ResumeWording(
        bullets=[], achievements=achievements,
    ))
    with pytest.raises(ValueError, match="achievements"):
        drafting.draft_resume(profile, "en", None)


@pytest.mark.parametrize("invented", [False, True])
def test_import_accepts_only_source_backed_achievements(tmp_path, monkeypatch, invented):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "linkedin.pdf"
    achievement = "Won the 2025 Example Hackathon."
    with fitz.open() as pdf:
        pdf.new_page().insert_text((40, 40), f"Alex Example\n{achievement}")
        pdf.save(source)
    proposed = achievement.replace("2025", "2024") if invented else achievement
    monkeypatch.setattr(cli, "infer", lambda *args: ImportResult(
        profile=Profile(name="Alex Example", achievements=[proposed]),
    ))
    destination = tmp_path / "profile.yaml"
    if invented:
        with pytest.raises(ValueError, match="not copied from the PDF"):
            cli.import_profile(source, destination)
        assert not destination.exists()
    else:
        cli.import_profile(source, destination)
        imported = yaml.safe_load(destination.read_text())
        assert imported["achievements"] == [achievement]
        assert imported["reviewed"] is False
