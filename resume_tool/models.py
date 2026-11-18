"""Validated profile and evidence contracts; no model output is executable."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Experience(Record):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    start: str = Field(pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")
    end: str | None = Field(default=None, pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")
    location: str | None = None
    bullets: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def chronological(self):
        if self.end and self.end[:4] < self.start[:4]:
            raise ValueError("Experience ends before it starts")
        if self.end and len(self.end) == len(self.start) and self.end < self.start:
            raise ValueError("Experience ends before it starts")
        return self


class Certification(Record):
    name: str = Field(min_length=1)
    issuer: str | None = None
    issued: str | None = Field(default=None, pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")
    expires: str | None = Field(default=None, pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")
    credential_id: str | None = None


class Education(Record):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    institution: str = Field(min_length=1)
    degree: str = Field(min_length=1)
    start: str | None = Field(default=None, pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")
    end: str | None = Field(default=None, pattern=r"^\d{4}(-(?:0[1-9]|1[0-2]))?$")


class Profile(Record):
    reviewed: bool = False
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)
    photo: str | None = None
    show_photo: bool = False
    summary: str | None = None
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    certifications: list[Certification | str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [e.id for e in self.experience] + [e.id for e in self.education]
        if len(ids) != len(set(ids)):
            raise ValueError("Experience and education IDs must be unique")
        return self


class ImportResult(Record):
    profile: Profile
    warnings: list[str] = Field(default_factory=list)


class Evidence(Record):
    ref: str
    quote: str = Field(min_length=1)


class Requirement(Record):
    text: str = Field(min_length=1)
    importance: Literal["required", "desired"]
    assessment: Literal["supported", "partial", "unproven"]
    evidence: list[Evidence]
    explanation: str = Field(min_length=1)


class MatchResult(Record):
    language: str = Field(pattern=r"^[a-z]{2,3}$")
    requirements: list[Requirement] = Field(min_length=1)


class LetterParagraph(Record):
    text: str = Field(min_length=1)
    evidence: list[Evidence]


class LetterResult(Record):
    language: str = Field(pattern=r"^[a-z]{2,3}$")
    paragraphs: list[LetterParagraph] = Field(min_length=1, max_length=5)


def facts(profile: Profile) -> dict[str, str]:
    """Stable evidence references into the reviewed profile."""
    result = {"name": profile.name}
    for field in ("summary", "location"):
        if value := getattr(profile, field):
            result[field] = value
    for item in profile.experience:
        result[f"experience:{item.id}"] = (
            f"{item.title} — {item.company}; {item.start} — {item.end or 'present'}"
        )
        for i, bullet in enumerate(item.bullets):
            result[f"experience:{item.id}:bullet:{i}"] = bullet
    for item in profile.education:
        result[f"education:{item.id}"] = f"{item.degree} — {item.institution}"
    for field in ("skills", "languages"):
        for i, value in enumerate(getattr(profile, field)):
            result[f"{field}:{i}"] = value
    for i, item in enumerate(profile.certifications):
        if isinstance(item, str):
            result[f"certifications:{i}"] = item
            continue
        parts = [item.name]
        if item.issuer:
            parts.append(item.issuer)
        if item.issued or item.expires:
            parts.append(f"{item.issued or '?'} – {item.expires or 'no expiration'}")
        if item.credential_id:
            parts.append(f"credential {item.credential_id}")
        result[f"certifications:{i}"] = "; ".join(parts)
    return result


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def condensed(text: str) -> str:
    # PDFs wrap lines and hyphenate; only a whitespace-free string is a reliable containment check.
    # Curly quotes are normalized the same way models rewrite them.
    return re.sub(r"\s+", "", text).replace("\u2019", "'").replace("\u2018", "'").casefold()


def validate_evidence(evidence: list[Evidence], source: dict[str, str]) -> None:
    for item in evidence:
        if item.ref not in source or normalized(item.quote) not in normalized(source[item.ref]):
            raise ValueError(f"Model returned unsupported evidence: {item.ref}")


def score_match(result: MatchResult, profile: Profile, job: str) -> dict:
    source = facts(profile)
    seen = set()
    total = earned = 0.0
    for requirement in result.requirements:
        text = normalized(requirement.text)
        if text not in normalized(job):
            raise ValueError("Requirement must quote the job description verbatim")
        if text in seen:
            raise ValueError("Model returned duplicate requirements")
        seen.add(text)
        validate_evidence(requirement.evidence, source)
        if requirement.assessment != "unproven" and not requirement.evidence:
            raise ValueError("Supported or partial requirements need profile evidence")
        weight = 2 if requirement.importance == "required" else 1
        total += weight
        earned += weight * {"supported": 1, "partial": 0.5, "unproven": 0}[requirement.assessment]
    return {
        **result.model_dump(),
        "percentage": round(100 * earned / total, 1),
        "formula": "100 * sum(weight * credit) / sum(weight); required=2, desired=1; supported=1, partial=0.5, unproven=0",
        "disclaimer": "Estimated evidence coverage, not hiring probability or an employer ATS score. Requirement extraction and classification are model judgments.",
    }
