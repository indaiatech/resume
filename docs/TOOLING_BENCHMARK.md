# Human-first and agent-ready repository benchmark

Research date: 2026-11-18. Planning only; no recommended configuration has been implemented. Upstream links below track moving branches, not immutable snapshots.

## Scope and evidence

The comparison covers contributor-facing documentation and repository entry points, not a security audit or a test of upstream software. Kubernetes and Rust community findings are recorded separately in [Community benchmark](COMMUNITY_BENCHMARK.md).

### uv: executable guidance without duplicated onboarding

Observed:

- The [README](https://github.com/astral-sh/uv/blob/main/README.md) starts with product purpose, highlights, installation, and working examples, and links to deeper documentation.
- [CONTRIBUTING.md](https://github.com/astral-sh/uv/blob/main/CONTRIBUTING.md) explains which issues are suitable for contributions, asks for discussion before new features, and provides concrete setup and focused test commands.
- [AGENTS.md](https://github.com/astral-sh/uv/blob/main/AGENTS.md) refers agents to CONTRIBUTING.md for tooling. It adds project-specific constraints: check existing coverage, prefer focused tests, follow nearby patterns, avoid unrelated lockfile updates, and avoid leaking conversation history into maintainer-facing prose.
- The [security policy](https://github.com/astral-sh/uv/blob/main/SECURITY.md) distinguishes expected code execution from in-scope vulnerabilities and links to private reporting guidance.
- Astral's [external-contributor AI policy](https://github.com/astral-sh/.github/blob/main/AI_POLICY.md) permits AI assistance but requires human understanding and responsibility. It explicitly disallows autonomous agent contributions and AI-generated maintainer comments.

Adopt: clear quickstart, concrete contribution commands, focused agent constraints, explicit security scope, and human responsibility for submitted work.

Adapt: this project wants agent-driven work, so do not copy Astral's autonomy ban. Permit agent-authored changes with a named accountable human, reviewable evidence, and human approval for merge, release, and handling personal data. Translation and accessibility assistance should remain practical rather than copying upstream communication restrictions.

Skip: uv's Rust toolchain, snapshot framework, privileged automation dispatcher, and large test matrix. Those solve uv-specific problems, not this Python CLI's current needs.

### Codex: public source does not imply an open PR policy

Observed:

- The [README](https://github.com/openai/codex/blob/main/README.md) puts installation and first use before contributor documentation, includes a product image, and identifies its Apache-2.0 license.
- The current [contribution policy](https://github.com/openai/codex/blob/main/docs/contributing.md) accepts issues, root-cause analyses, and feature requests but explicitly rejects external code contributions and pull requests.
- The policy asks bug reporters for reproduction steps, expected versus actual behavior, versions, environment, and sanitized diagnostics, and redirects security reports to a separate policy.

Adopt: user-first onboarding, actionable issue reports, sanitized logs, and explicit contribution boundaries.

Do not copy: the closed external-PR policy if the goal is an open contributor community. A famous open-source repository is not automatically the right community model.

## Recommendations for this repository

1. Resolve licensing and inspect publication material for personal data before public distribution. The existing README already identifies the PyMuPDF licensing concern; repository popularity cannot resolve it.
2. Keep README focused on the first successful synthetic workflow, expected artifacts, supported environments, and honest limitations. Move workstation-specific verification details into the existing verification document.
3. Add CONTRIBUTING.md with one setup path, focused checks, contribution scope, and review expectations. Do not require Ollama to run deterministic contribution checks.
4. Add a concise AGENTS.md that links to contributor commands and documents evidence integrity, review-gated profiles, local inference, untrusted document handling, and private artifact restrictions.
5. Verify Claude Code instruction discovery for the supported version. Add an import-only CLAUDE.md only if compatibility requires it; do not duplicate instructions. See [Claude Code memory documentation](https://code.claude.com/docs/en/memory) and [AGENTS.md](https://agents.md/).
6. Permit agents to implement and verify scoped work, but require accountable human review for publication and consequential actions. Instructions are guidance, not enforcement: use CI, branch protection, and credentials with minimal permissions.
7. Start with deterministic tests, package build/install smoke checks, and synthetic PDF rendering in CI. Evaluate real-model quality separately with reviewed synthetic cases and recorded model versions.
8. Use lightweight bug/feature forms and a PR checklist asking for behavior, evidence, and privacy review. Avoid issue bureaucracy, CLA infrastructure, custom bots, and mandatory MCP services without a demonstrated need.

## Publication acceptance criteria

- A newcomer can produce and inspect a synthetic PDF without supplying personal information.
- A contributor can run deterministic checks without a model service or paid account.
- An agent can find the same commands and constraints without private chat context.
- A maintainer can identify what changed, how it was checked, and who owns the submission.
- Licensing, private vulnerability reporting, supported environments, and model limitations are explicit.

These are proposed acceptance criteria, not claims that the repository already meets them.
