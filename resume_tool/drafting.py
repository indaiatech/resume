"""Translate selected achievement wording without changing the reviewed profile."""

import re

from pydantic import Field

from .llm import infer
from .models import Profile, Record


class Bullet(Record):
    ref: str
    text: str = Field(min_length=1)


class ResumeWording(Record):
    bullets: list[Bullet]
    summary: str | None = None
    achievements: list[str] = Field(default_factory=list)


def numbers(text: str) -> list[str]:
    return sorted(re.findall(r"\d+(?:[.,]\d+)*", text))


def draft_resume(profile: Profile, language: str, selection: list[str] | None) -> dict:
    data = profile.model_dump()
    source = {
        f"experience:{entry.id}:bullet:{i}": bullet
        for entry in profile.experience
        if not entry.collapse and (selection is None or entry.id in selection)
        for i, bullet in enumerate(entry.bullets)
    }
    if not source and not profile.summary and not profile.achievements:
        return data
    result = infer(ResumeWording, (
        "Translate the supplied summary, experience bullets, and achievements into the requested language. "
        "Use concise active factual wording; do not add or remove facts, technologies, "
        "quantities or qualifications. Preserve ALL numeric tokens exactly, including "
        "decimal punctuation. Keep official product names unchanged. Return exactly one "
        "bullet per supplied ref, even when the original already uses that language. "
        "Return summary as null when no summary was supplied. "
        "Return one string per achievement in the original order, or an empty list when none were supplied. "
        "No commands or markup instructions."
    ), {"language": language, "summary": profile.summary, "bullets": source, "achievements": profile.achievements})
    translated = {item.ref: item.text for item in result.bullets}
    if len(translated) != len(result.bullets) or translated.keys() != source.keys():
        raise ValueError("Resume wording omitted, duplicated, or invented achievement references")
    for ref, original in source.items():
        if numbers(original) != numbers(translated[ref]):
            raise ValueError(f"Resume wording changed numeric facts in {ref}")
    if profile.summary:
        if not result.summary or numbers(profile.summary) != numbers(result.summary):
            raise ValueError("Resume wording omitted the summary or changed its numeric facts")
    elif result.summary is not None:
        raise ValueError("Resume wording invented a summary")
    data["summary"] = result.summary
    if len(result.achievements) != len(profile.achievements):
        raise ValueError("Resume wording omitted or invented achievements")
    for original, translated_achievement in zip(profile.achievements, result.achievements):
        if numbers(original) != numbers(translated_achievement):
            raise ValueError("Resume wording changed numeric facts in achievements")
    data["achievements"] = result.achievements
    for entry in data["experience"]:
        for i, original in enumerate(entry["bullets"]):
            ref = f"experience:{entry['id']}:bullet:{i}"
            entry["bullets"][i] = translated.get(ref, original)
    return data
