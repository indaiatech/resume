"""Render local, data-only Typst documents without exposing profile text as code."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
import shutil
import tempfile

import pymupdf as fitz
import typst


from .localization import labels


_REGIONS = {"en": "us", "pt": "br"}


def _contacts(profile: dict) -> dict:
    """Map profile links onto the tech-focused-resume contact fields."""
    fields = {
        "email": profile.get("email") or "",
        "phone": profile.get("phone") or "",
        "location": profile.get("location") or "",
        "github": "", "linkedin": "", "personal-site": "",
    }
    for value in profile.get("links", []):
        url = value.split("://", 1)[-1].rstrip("/")
        if "github.com/" in url:
            fields["github"] = url.split("github.com/", 1)[1]
        elif "linkedin.com/in/" in url:
            fields["linkedin"] = url.split("linkedin.com/in/", 1)[1]
        elif not fields["personal-site"]:
            fields["personal-site"] = url
    return fields


def _data(profile: dict, language: str) -> dict:
    if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("Document language must be a two- or three-letter lowercase code.")
    return {
        "profile": profile,
        "labels": labels(language),
        "language": language,
        "region": _REGIONS.get(language, language.upper()),
        "contacts": _contacts(profile),
    }


def _render(data: dict, output: Path, template: str, max_pages: int) -> None:
    output = Path(output)
    templates = Path(__file__).resolve().parent / "templates"
    if not templates.is_dir():
        templates = Path(__file__).resolve().parent.parent / "templates"
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        # Keep compilation on the destination filesystem for atomic replacement.
        with tempfile.TemporaryDirectory(prefix=".resume-", dir=output.parent) as directory:
            root = Path(directory)
            shutil.copyfile(templates / template, root / "main.typ")
            photo = data.pop("photo_source", None)
            if photo:
                shutil.copyfile(photo, root / photo.name)
                data["photo"] = photo.name
            (root / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            pdf = root / "document.pdf"
            typst.compile(str(root / "main.typ"), output=str(pdf), root=str(root))
            with fitz.open(pdf) as document:
                pages = document.page_count
            if not 1 <= pages <= max_pages:
                raise ValueError(
                    f"Document has {pages} pages; the limit is {max_pages}. "
                    "Select fewer experience entries or shorten the supplied content; "
                    "nothing was truncated or reduced in font size."
                )
            os.replace(pdf, output)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not render {output.name}: {exc}") from exc


def render_resume(
    profile: dict,
    output: Path,
    language: str = "en",
    selection: list[str] | None = None,
) -> None:
    """Write a one-column resume, rejecting output longer than two pages.

    Selection contains experience IDs only. The existing output is preserved if
    compilation or the page-limit check fails. Summary text is intentionally omitted.
    """
    experience = profile.get("experience", [])
    if selection is not None:
        selected = set(selection)
        unknown = selected - {entry["id"] for entry in experience}
        if unknown:
            raise ValueError("Unknown experience IDs: " + ", ".join(sorted(unknown)))
        experience = [entry for entry in experience if entry["id"] in selected]
    data = _data(profile, language)
    data["profile"] = dict(profile)
    photo = profile.get("photo")
    if not photo and Path("profile.jpeg").exists():
        photo = "profile.jpeg"
    data["photo_source"] = Path(photo) if photo else None
    # Dates have already been validated as YYYY or YYYY-MM by the profile model.
    data["profile"]["experience"] = sorted(
        experience,
        key=lambda entry: (entry.get("end") or "9999-12", entry["start"]),
        reverse=True,
    )
    data["profile"]["education"] = sorted(
        profile.get("education", []),
        key=lambda entry: (entry.get("end") or "9999-12", entry.get("start") or ""),
        reverse=True,
    )
    _render(data, output, "resume.typ", max_pages=2)


def render_letter(
    profile: dict,
    paragraphs: list[str],
    output: Path,
    language: str = "en",
) -> None:
    """Write supplied cover-letter paragraphs, rejecting more than one page."""
    if not paragraphs or any(not isinstance(text, str) or not text.strip() for text in paragraphs):
        raise ValueError("A cover letter requires non-empty text paragraphs.")
    data = _data(profile, language)
    data["paragraphs"] = paragraphs
    data["date"] = datetime.now().strftime("%B %d, %Y")
    _render(data, output, "letter.typ", max_pages=1)
