# Local Resume Toolkit

Import a text-based LinkedIn PDF into a reviewed YAML profile, build concise Typst resumes, check PDF readability offline, compare your profile with a job, and draft a cover letter.

All inference uses local Ollama. No OpenAI account, Codex subscription, browser automation, or external inference API is needed. Internet access is needed for initial dependency/model downloads, not document processing.

## Setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), [Task](https://taskfile.dev/), and Docker with Compose. Typst is bundled by the Python binding; a separate Typst CLI is unnecessary.

```bash
task setup
```

The pinned Ollama image runs on CPU and exposes port 11434 only on `127.0.0.1`. The default model is `qwen3.5:4b` (several GB to download). CPU inference can be slow. GPU access is not assumed: this workstation's Docker runtime did not expose its NVIDIA GPU. The Docker VM has about 7.4 GiB RAM; the 9B variant's runner was killed during verification, so v1 uses the smaller model. Keep adequate RAM and disk space available.

```bash
task model-up
task model-down
```

An existing local Ollama can be used instead: skip Compose startup, pull the same model yourself, and set `OLLAMA_URL=http://127.0.0.1:11434` if needed. Only literal loopback HTTP origins are accepted; redirects and environment HTTP proxies are disabled. To use a different installed model, export `OLLAMA_MODEL` before setup and processing. Model quality is not interchangeable.

## Import and review

```bash
task import -- '/absolute/path/LinkedIn Profile.pdf'
```

This writes `profile.yaml` with `reviewed: false`. Review it against the original PDF and `output/...-import-.../source.txt`, recover any omissions reported in `import-report.json`, then set `reviewed: true`.

- Existing profiles are never overwritten by import.
- To import another profile: `task import PROFILE=another.yaml -- '/path/profile.pdf'`.
- Only text-based PDFs are supported: no OCR, encrypted documents, or scanned pages.
- Import limits: 25 MB, 30 pages, 60,000 extracted characters.
- Descriptive imported facts must occur in the extracted text. Dates are normalized to `YYYY` or `YYYY-MM`; verify them manually. Unknown start dates are reported for manual recovery rather than guessed.
- A missing end date means the position is current. Verify that interpretation.
- IDs must be unique lowercase slugs. Keep them stable: reports reference them.
- `examples/profile.yaml` is synthetic and demonstrates the schema. It is not your CV.

## Generate a resume

```bash
task resume
# Smoke example, without replacing your profile:
task resume PROFILE=examples/profile.yaml
```

A general resume uses English achievement wording. Official names, titles, dates, and factual qualifications remain intact. Concise wording is generated locally and saved for review; numeric tokens are checked against the original bullets. The source YAML is not changed.

Provide the vacancy as literal text in an environment variable, not as shell commands:

```bash
JOB_DESCRIPTION='We require Python and PostgreSQL. Docker is desirable.' task resume
JOB_DESCRIPTION='We require Python and PostgreSQL. Docker is desirable.' task match
JOB_DESCRIPTION='We require Python and PostgreSQL. Docker is desirable.' task cover-letter
```

For multiline text, quotes, or shell punctuation, use a quoted heredoc:

```bash
JOB_DESCRIPTION="$(cat <<'JOB'
Senior Backend Engineer
Required: Python, PostgreSQL, and professional English.
Desired: Docker and Kubernetes.
JOB
)" task match
```

`JOB_DESCRIPTION` is read directly from the environment and never interpolated into Taskfile shell commands. Do not paste untrusted text into unquoted shell syntax. Job text is limited to 60,000 characters.

Each run creates a unique `output/<UTC timestamp>-<command>-<random>/` directory. No previous application is silently overwritten. It includes the profile snapshot, original job text where supplied, model tag, and generated artifacts. Resume runs produce `resume.pdf` and `resume-wording.json`; tailored runs also produce match reports. Experience entries with supporting/partial evidence are selected; if none have evidence, the full history is retained with a warning. Other profile sections are retained, not silently rewritten to fit.

The document uses the [tech-focused-resume](https://typst.app/universe/package/tech-focused-resume) (MIT) and [exp-cover-letter](https://typst.app/universe/package/exp-cover-letter) (public domain) Typst packages. Their sources are fetched from the Typst package registry once during `task setup` and cached; document rendering then stays offline. Cover letters keep the package's sender/date/closing layout with the same font as the resume.

Two-column header: name and contacts on the left, photo on the right. Set `photo: /path/to/image` in the profile, or just leave a `profile.jpeg` file in the project root. Note: Harvard's guidance recommends omitting photos; this is your explicit choice, and some US employers discard resumes with photos.

One page is the target; two is the maximum. Overflow fails with a diagnostic instead of shrinking the font or truncating content. Shorten the reviewed content or select a more focused profile if necessary.

## Offline PDF readability check

```bash
task ats -- 'output/<run>/resume.pdf'
```

This needs neither Ollama nor internet. It prints the extracted text, score, findings, and disclaimer, and saves `ats.json` in its own run folder. The independent 80/20 checker inspects text layers, encoding symptoms, possible columns, small fonts, some hidden text, conventional EN/PT headings, contacts, and date patterns. Geometric layout findings can be false positives; inspect the PDF and extracted text together. Other languages may trigger heading/date warnings.

**The readability score is not an employer ATS score or a probability of passing screening.** See [the source investigation](docs/RESEARCH.md) for why this version uses an independent Python checker rather than embedding the Reactive Resume application.

## Match report

`task match` writes `match.json` and `match.md`, including:

- A verbatim quote for each model-extracted job requirement.
- Required versus desired classification.
- Supported, partial, or unproven assessment.
- Profile references and verified source quotations.
- An estimated coverage percentage: required weight 2, desired weight 1; supported credit 1, partial 0.5, unproven 0.

The percentage is calculated from those classifications, not freely invented by the LLM. It measures evidence coverage, not your actual ability, hiring probability, or interview likelihood. Missing evidence does not mean missing ability. Requirement completeness, classification, and semantic fit remain model judgments; inspect the report, particularly unproven mandatory requirements. Verified quotations do not prove the model's interpretation is correct.

## Cover letter

`task cover-letter` writes `cover-letter.txt`, `cover-letter.pdf`, evidence-bearing `cover-letter.json`, and match reports. It drafts at most 350 words, with a one-page PDF limit, generic greeting, and your name. Resume headings and letter prose follow the job language; non-EN/PT document labels are translated locally. Font coverage depends on installed fonts, so review documents in other writing systems visually.

**Review before sending.** The model is instructed not to invent facts, recipient names, motivations, or employer research. Evidence quotations are verified, but prose is not a formally proven entailment of those quotations. Never submit generated content without checking every claim.

## Privacy and safety

- No external inference providers or agent tools; PDF and job content are treated as untrusted data.
- Generated text is passed to Typst as JSON data, never evaluated as Typst source.
- New CLI artifacts use restrictive permissions. Existing directory permissions are not changed.
- `profile.yaml`, root PDFs, and `output/` are ignored by Git. Custom profile paths are **not** automatically ignored: add them before committing. Ignoring files is not encryption or deletion.
- Raw PDF text, job descriptions, and profile snapshots remain on disk for review. Delete them yourself when no longer needed. Ollama may retain a model in RAM until its normal idle timeout.
- The Ollama port has no authentication; other local processes can access it. Do not expose it to a network.
- Stop the model with `task model-down`; this preserves downloaded models.

## Checks and design references

```bash
task test
```

Deterministic checks cover evidence rejection, scoring, explicit review, loopback restrictions, data-only Typst rendering, page limits, and PDF heuristics. They do not establish real-model quality. See [verification notes](docs/VERIFICATION.md) for actual model runs and remaining limits.

- [Harvard resume and cover letter guidance](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/): concise, factual, skimmable, reverse chronology; a cover letter no longer than one page. This is an adaptation for an experienced professional, not an official Harvard template.
- [Domain glossary](GLOSSARY.md)

## Licensing

PyMuPDF is available under AGPL or a commercial license. Review those obligations before distributing this tool or offering a service; this is not an all-MIT dependency stack. No license for your project code has been selected on your behalf.
