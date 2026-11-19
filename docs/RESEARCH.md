# Primary-source investigation

## ATS checking

Sources inspected during v1 design:

- [Reactive Resume public checker](https://rxresu.me/ats-checker): advertises browser-side PDF extraction and readability checks without uploading the file, with a separate optional job keyword match.
- [Official checker guide](https://docs.rxresu.me/guides/using-the-ats-checker): explains what the checks mean and their limits. These are readability checks, not access to an employer's screening system.
- [MIT source engine at inspected commit](https://github.com/reactive-resume/reactive-resume/tree/602578f75edb77b739ea4e18bc3adbb94cb35c30/packages/resume/src/ats-pdf): the TypeScript analyzer is browser-independent. Its browser extraction adapter lives in `apps/web/src/features/ats-checker/extract-client.ts`. It is incorrect to describe the analyzer as inseparable from the web UI.
- [Reactive Resume license](https://github.com/reactive-resume/reactive-resume/blob/main/LICENSE): MIT; reusing source requires preserving its notice.
- [OpenResume source](https://github.com/xitanggg/open-resume): browser-based resume parsing, licensed AGPL-3.0. It is not a drop-in equivalent of the complete checker. Its source was not copied.
- [ATS Buddy source](https://github.com/seehiong/ats-buddy): advertises local WebLLM/Ollama analysis. License and model quality were not established during this investigation; it was not selected.

### V1 decision

Use an independent Python 80/20 checker (initially PyMuPDF; later pdfplumber and pdfium for permissive licensing). Reusing Reactive Resume's engine is possible, but adds a JavaScript runtime and an adapter for its extraction schema alongside the Python PDF extraction already needed for import. For this small local CLI, that integration cost was not selected. No Reactive Resume source is vendored, and no claim of rule or score equivalence is made. A future replacement should compare actual PDF findings, not just numerical scores.

Two distinct assessments remain separate:

1. **PDF readability:** deterministic, explicitly weighted heuristics over the actual PDF.
2. **Profile match:** model-extracted job requirements and evidence classifications, followed by a transparent arithmetic percentage.

Neither estimates hiring probability.

## Local inference and Codex

- [Official Codex advanced configuration](https://developers.openai.com/codex/config-advanced): Codex CLI supports local OSS providers. Using the CLI does not inherently require hosted OpenAI inference.
- [Official Ollama Codex integration](https://docs.ollama.com/integrations/codex): describes local model operation and its context requirements.
- [Codex noninteractive mode](https://developers.openai.com/codex/noninteractive): structured output can be requested, but this does not establish semantic scoring quality for any particular local model.
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs): JSON Schema-constrained local output.
- [Ollama FAQ](https://docs.ollama.com/faq): local operation, model storage, and disabling cloud features.
- [Qwen3.5 model library](https://ollama.com/library/qwen3.5): available model variants. Installed tags and hardware suitability must be checked by execution rather than assumed.

### V1 decision

Call the local Ollama chat API directly with JSON Schema and no tools. This needs neither Codex's agent execution features nor an extra subprocess protocol. Loopback-only URLs, disabled proxy inheritance, rejected redirects, data-only Typst inputs, and verified evidence references constrain the application's behavior. They do not prove factual correctness of generated prose.

The application does not use a model as a free-form percentage generator: required requirements carry weight 2, desired requirements weight 1; evidence credit is 1, 0.5, or 0. The model still controls requirement extraction and assessment, so the report must remain reviewable.

## Document guidance

[Harvard's guide](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/) recommends specific, active, factual, concise language; skimmable formatting; reverse chronology within sections; and sections ordered by importance. It explicitly limits cover letters to one page. The linked page does not establish a universal one-page maximum for every resume.

V1 adapts this to experienced professionals: experience first, one column, no photograph, one-page resume target and two-page maximum, with no silent font shrinking or truncation. These are project decisions, not claims of Harvard certification.

## PDF dependency license

PyMuPDF originally carried an AGPL/commercial dual license; it was replaced by pdfplumber (MIT), pdfminer.six (MIT), and pypdfium2 (Apache-2.0, bundled PDFium under BSD-3), so the toolkit no longer depends on copyleft components. The project itself is MIT-licensed.
