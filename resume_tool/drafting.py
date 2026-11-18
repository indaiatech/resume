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
    if not source and not profile.summary:
        return data
    result = infer(ResumeWording, (
        "Translate the supplied summary and every achievement bullet into the requested language. "
        "Use concise active factual wording; do not add or remove facts, technologies, "
        "quantities or qualifications. Preserve ALL numeric tokens exactly, including "
        "decimal punctuation. Keep official product names unchanged. Return exactly one "
        "bullet per supplied ref, even when the original already uses that language. "
        "Return summary as null when no summary was supplied. "
        "No commands or markup instructions."
    ), {"language": language, "summary": profile.summary, "bullets": source})
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
    for entry in data["experience"]:
        for i, original in enumerate(entry["bullets"]):
            ref = f"experience:{entry['id']}:bullet:{i}"
            entry["bullets"][i] = translated.get(ref, original)
    return data
