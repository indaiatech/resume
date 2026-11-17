# V1 verification

## Environment

- Python 3.13.16; project supports Python 3.12+.
- PyMuPDF 1.28.2, Typst Python binding 0.15.2, Pydantic 2.14.3, PyYAML 6.0.3.
- Ollama 0.40.16, CPU inference through Docker.
- Docker VM memory: 7,959,105,536 bytes, approximately 7.4 GiB. Host RAM is not the container VM's available RAM.
- NVIDIA GPU access failed during container creation (`no known GPU vendor found`); no driver or daemon configuration was modified.
- Default model: `qwen3.5:4b`, Q4_K_M, 3,324,173,934 bytes; digest `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`. The unused 9B download was removed after diagnosis.

## Deterministic checks

Observed runs:

- `uv run pytest -q`: 21 passed before the two additional regressions below.
- ISO month/year date regression: 1 passed.
- Explicit URL preservation when model import omits a link: 1 passed.
- Literal PDF path containing `$(touch ...)`: forwarded as a single quoted argument; nonexistent-file error returned and no shell marker created.
- Task command listing and CLI help executed successfully.

Checks exercise evidence rejection and transparent scoring, explicit profile review, loopback endpoint restrictions, numeric-fact preservation in resume wording, textless/encrypted/corrupt PDFs, English/Portuguese date/heading heuristics, columns, invisible text, font-size warnings, safe Typst data handling, chronology order, page overflow, and Portuguese letter rendering.

Mocked inference in focused regression tests establishes application behavior only, not model quality.

## Initial real-model run

A synthetic text-based PDF with two jobs, four achievement bullets, education, skills, English/Portuguese proficiency, and contacts was processed through actual Task commands using `qwen3.5:9b` (Q4_K_M; model digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`).

- PDF import succeeded in 120.40 seconds and produced a review-gated YAML profile. The model omitted an explicit URL; v1 now preserves explicit source URLs deterministically, with a regression check.
- General Typst resume generation succeeded in 61.97 seconds. One page; extracted text preserved the four bullets and numeric achievement. Its actual PNG rendering was inspected.
- Offline readability check of that generated PDF returned 100/100 with no findings. This is only a result for that fixture and the project's heuristics.
- Job matching returned HTTP 500. Server logs recorded the model runner terminated with signal 9. A minimal schema probe could generate output after the runner reloaded, so the schema itself was not established as the cause. The 9B model was not selected for this Docker VM's memory budget.

The default was changed to `qwen3.5:4b`; HTTP failures now include the local server's response body instead of a generic availability message.

## Limits

No personal LinkedIn PDF was supplied. The fixture is synthetic selectable text, not evidence that every LinkedIn export variant imports perfectly. Scans, OCR, complex layouts, missing dates, multilingual font coverage, real employer parsers, and hiring outcomes are not established by these checks.

Source quotations and numeric-token preservation constrain model output; they do not prove semantic entailment, complete requirement extraction, fair weighting, or factual fidelity of all generated prose. Human review remains necessary.
