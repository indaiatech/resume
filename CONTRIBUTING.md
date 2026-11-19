# Contributing

## Setup

- Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), [Task](https://taskfile.dev/), and Docker with Compose.
- `task setup`, then `task test`.

## Ground rules

- Tests must pass: `task test`.
- Keep the privacy posture: never commit `profile*.yaml`, `.env`, `*.gist-sync.json`, or `output/` artifacts. Personal data stays out of the repository and its history.
- Conventional commit subjects (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`), matching the existing history.
- Smallest change that works; match the existing style. No new dependencies without justification.

## Agent-assisted contributions

Accepted. AI-assisted work is fine under one rule: a human takes responsibility for the change. Review every line, run the tests, and note the assistance in the pull request (for example, `assisted-by: <tool>`).
