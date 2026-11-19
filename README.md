# Local Resume Toolkit

Import a text-based LinkedIn PDF into a reviewed YAML profile, build concise Typst resumes, check PDF readability offline, compare your profile with a job, and draft a cover letter.

All inference uses local Ollama. No OpenAI account, Codex subscription, browser automation, or external inference API is needed. Internet access is needed for initial dependency/model downloads and, when configured, fetching the latest profile from a Gist. Document rendering and inference stay local.

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

## Start from the example

```bash
task profile                 # copies examples/profile.yaml to profile.yaml with reviewed: false
task profile PROFILE=another.yaml
task clean                   # lists output/ artifacts and asks before deleting them
```

`task profile` never overwrites an existing file. Review the copied profile and set `reviewed: true` before generating documents. To import real data instead, see the next section.

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

## Version the profile in a Gist (optional)

Keep the complete profile out of the public toolkit repository while versioning it
in a separate **secret Gist** containing a file named `profile.yaml`.
Secret Gists are **unlisted, not private**: anyone who obtains the URL can read the
file and its history. Keeping the URL in `.env` prevents committing it here; it
does not provide access control. Use a private repository instead if that is required.

1. Create a secret Gist from the reviewed profile, using the GitHub website or
   `gh gist create profile.yaml --desc 'Resume profile source'` (secret by default).
2. Create `.env` from `.env.example` if it does not already exist, and replace the
   example URL with your Gist's browser URL:

   ```dotenv
   PROFILE_GIST_URL=https://gist.github.com/YOUR_GITHUB_USERNAME/YOUR_GIST_ID
   ```

3. Run `task resume`. Task loads `.env`; the CLI fetches the latest `profile.yaml`,
   validates the schema and `reviewed: true`, then replaces the local copy atomically.
   The URL is not printed or saved in generated reports. No GitHub token is needed
   to download a secret Gist.

Every configured resume run requires network access. Download, validation, or
conflict errors stop generation; there is no silent fallback to a stale profile.
If `PROFILE_GIST_URL` is empty or unset, the existing local-only workflow is unchanged.
Direct CLI usage reads this variable from the process environment, not from `.env`.
Other commands use the local profile and do not fetch it automatically.

Local edits are never automatically uploaded. Publish them before the next resume:

```bash
gh gist edit 'https://gist.github.com/YOUR_GITHUB_USERNAME/YOUR_GIST_ID' --filename profile.yaml profile.yaml
```

Synchronization refuses to replace unsynchronized local edits. It also refuses to
adopt a different remote over an existing, different local profile without a matching
sync baseline. The local `*.gist-sync.json` baseline contains only source/content
hashes and is ignored by Git, as are the profile, local profile copies, `.env`, and
temporary sync directories. Preserve this baseline between runs.

To render a different local profile without downloading the configured Gist:

```bash
PROFILE_GIST_URL= task resume PROFILE=examples/profile.yaml
```

## Generate a resume

```bash
task resume
# Smoke example, without replacing your profile:
task resume PROFILE=examples/profile.yaml
```

A general resume renders the reviewed profile verbatim with English section labels and no model call. Job-tailored runs translate the selected achievement bullets and summary locally, save the wording for review, and check numeric tokens against the synchronized profile. Official names, titles, dates, and factual qualifications remain intact; the model never rewrites the source YAML.

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

`profile.yaml` is the complete source of truth, including details intended for LinkedIn.
The resume displays its `summary` above Experience. Add `collapse: true` to an
experience entry to show only its company, title, and dates under Earlier Experience
(Experiência anterior in Portuguese). Entries with the same title share a role label
and list their companies with individual periods, without shrinking typography or
spacing. Omitted or `false` keeps the full entry. Optional `earlier_layout: lines`
on a collapsed entry stacks each grouped company on its own line instead of the
default inline `;`-joined list; entries without the flag stay inline.
Set `contractor: true` on engagements performed as contractors; the resume marks
the company with a localized `· Contract` marker. Set `stealth: true` when the
client identity is NDA-protected: the company renders as Confidential Client
(NDA) (Cliente Confidencial (NDA) in Portuguese) and the source name stays only
in the YAML — following the common convention for stealth clients.
Bullets remain in the profile, saved snapshots, and matching evidence; collapse
affects resume presentation only and never deletes or rewrites the source YAML.
Job-tailored selection still determines which entries appear before collapse is applied.

```yaml
experience:
  - id: earlier-role
    company: Example Company
    title: Developer
    start: '2009'
    end: '2011'
    collapse: true
    earlier_layout: lines # stacks each company on its own line (default: inline)
    bullets:
      - Full project details remain available for LinkedIn and matching.
```

The document uses the [tech-focused-resume](https://typst.app/universe/package/tech-focused-resume) (MIT) and [exp-cover-letter](https://typst.app/universe/package/exp-cover-letter) (public domain) Typst packages. Their sources are fetched from the Typst package registry once during `task setup` and cached; document rendering then stays offline. Cover letters keep the package's sender/date/closing layout with the same font as the resume.

The header has three lines: centered name, centered roles from `headline`, and a contact row. Explicit stack gaps keep the role line compact. Contacts keep their existing distribution across the available width. No photo is rendered.

The footer pairs Education with Languages, then Certifications with Skills. An unpaired section uses the full width. Optional `achievements` appear last as Selected Achievements (Principais conquistas in Portuguese). Keep these brief and source-backed; they are also available as matching evidence and translated with numeric-fact checks. Imports only accept achievements explicitly present in the source.

```yaml
achievements:
  - First place in the fictional Example Systems engineering challenge (2023).
```

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

This project is MIT-licensed (see [LICENSE](LICENSE)). PyMuPDF remains available under AGPL or a commercial license: distributing binaries or offering a service built on it carries AGPL obligations for the combined work. Review those obligations; this is not an all-MIT dependency stack.
