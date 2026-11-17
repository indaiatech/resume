"""Document vocabulary; uncommon job languages are translated locally."""

from functools import lru_cache
import re

from .models import Record


class Labels(Record):
    experience: str
    education: str
    skills: str
    languages: str
    certifications: str
    current: str
    greeting: str
    closing: str


@lru_cache(maxsize=16)
def labels(language: str) -> dict[str, str]:
    if not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("Document language must be a lowercase ISO 639 code")
    english = {
        "experience": "Experience", "education": "Education", "skills": "Skills",
        "languages": "Languages", "certifications": "Certifications", "current": "Present",
        "greeting": "Dear Hiring Team,", "closing": "Sincerely,",
    }
    if language == "en":
        return english
    if language == "pt":
        return {
            "experience": "Experiência profissional", "education": "Formação acadêmica",
            "skills": "Competências", "languages": "Idiomas", "certifications": "Certificações",
            "current": "Atual", "greeting": "Prezada equipe de recrutamento,", "closing": "Atenciosamente,",
        }
    from .llm import infer
    return infer(Labels, "Translate these document labels into the requested language. Keep them concise and professional. No other text.", {"language": language, "labels": english}).model_dump()
