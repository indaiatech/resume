# Changelog

## Unreleased

- Replace PyMuPDF with pdfplumber (MIT), pdfminer.six, and pypdfium2 so every runtime dependency stays permissively licensed; the PyMuPDF-specific repaired-PDF warning is gone.
- Publish under the MIT license with community health files, a CI workflow, and repository governance.

- Preserve complete profile details while grouping `collapse: true` roles under Earlier Experience in resumes.
- Render the profile summary above Experience and include it in job-tailored translation with numeric-fact checks.
- Optionally fetch a versioned profile from a Gist before resume generation, with `.env` configuration, review validation, atomic replacement, and local-edit conflict protection.
- Center the resume name and roles above the contact row, and group earlier jobs by title while preserving every company's dates.
- Bypass cached Gist raw responses so newly published profile revisions are fetched without weakening local-edit conflict protection.
- Support source-backed achievements in profiles, imports, matching, translated resumes, and localized section headings.
- Allow collapsed entries to stack grouped companies with `earlier_layout: lines`, keeping other groups inline.
- Add `contractor` and `stealth` experience flags: contract engagements get a localized marker and NDA-protected clients render as Confidential Client without exposing the source name.
- Pair Education with Languages and Certifications with Skills, place Selected Achievements last, and tighten header gaps without shrinking typography. Keep experience headings with their first bullet across page breaks.

## 0.1.0

- Import text-based LinkedIn PDFs into a review-gated YAML profile with source text and ambiguity warnings.
- Generate general and job-tailored Typst resumes with readable typography and a two-page hard limit.
- Inspect actual PDF readability offline with independent, explained 80/20 heuristics.
- Compare job requirements with profile evidence and calculate an auditable coverage percentage.
- Draft evidence-linked cover letters as editable text and one-page Typst PDFs.
- Provide Taskfile commands, local Ollama deployment, isolated run artifacts, and deterministic regression checks.
