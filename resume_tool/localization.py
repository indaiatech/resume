"""Document vocabulary; uncommon job languages are translated locally."""

from functools import lru_cache
import re

from .models import Record


class Labels(Record):
    summary: str
    earlier_experience: str
    experience: str
    education: str
    skills: str
    languages: str
    certifications: str
    achievements: str
    current: str
    greeting: str
    closing: str
    modalities: dict[str, str]
    stealth_client: str
    contract: str


@lru_cache(maxsize=16)
def labels(language: str) -> dict[str, str]:
    if not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("Document language must be a lowercase ISO 639 code")
    english = {
        "summary": "Summary", "earlier_experience": "Earlier Experience",
        "achievements": "Selected Achievements",
        "experience": "Experience", "education": "Education", "skills": "Skills",
        "languages": "Languages", "certifications": "Certifications", "current": "Present",
        "greeting": "Dear Hiring Team,", "closing": "Sincerely,",
        "modalities": {"remote": "Remote", "hybrid": "Hybrid", "onsite": "On-site"},
        "stealth_client": "Confidential Client (NDA)", "contract": "Contract",
    }
    if language == "en":
        return english
    if language == "pt":
        return {
            "summary": "Resumo profissional", "earlier_experience": "Experiência anterior",
            "achievements": "Principais conquistas",
            "experience": "Experiência profissional", "education": "Formação acadêmica",
            "skills": "Competências", "languages": "Idiomas", "certifications": "Certificações",
            "current": "Atual", "greeting": "Prezada equipe de recrutamento,", "closing": "Atenciosamente,",
            "modalities": {"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial"},
            "stealth_client": "Cliente Confidencial (NDA)", "contract": "Contrato",
        }
    from .llm import infer
    return infer(Labels, "Translate these document labels into the requested language. Keep them concise and professional. No other text.", {"language": language, "labels": english}).model_dump()
