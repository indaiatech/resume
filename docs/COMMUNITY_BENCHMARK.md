# Community benchmark: Kubernetes and Rust

Research date: 2026-11-18. Scope: contributor onboarding, community conduct, review, security disclosure, and human-first agent participation in `kubernetes/kubernetes`, `kubernetes/community`, and `rust-lang/rust`. This is a planning note, not an implemented policy or an audit of either project's effectiveness.

## Executive recommendation

Borrow **clear contribution paths, accountable human review, respectful communication, private security reporting, and durable decision context**. Do not borrow the organizational machinery that makes those practices work across a compiler ecosystem or Kubernetes SIGs.

For this maintainer-led Python CLI, the smallest useful model is one documented maintainer decision path, one contribution guide, a short review checklist, a conduct/reporting policy, and a private security contact. Agent instructions should summarize human documentation; agents must not become a prerequisite for participation or a substitute for human responsibility.

The local [README](../README.md) describes a local Ollama/PDF/Typst workflow, reviewed profile data, synthetic examples, and evidence-linked generated output. Recommendations below therefore emphasize reproducible synthetic inputs, protection of personal resume data, and review of model-dependent behavior—not cluster administration or compiler soundness processes.

## Method and limits

- Inspected official repository files and the official documentation they link to. GitHub API listings established repository entry points and Rust's PR template rather than assuming filenames: [Kubernetes root](https://api.github.com/repos/kubernetes/kubernetes/contents/), [community root](https://api.github.com/repos/kubernetes/community/contents/), [Rust root](https://api.github.com/repos/rust-lang/rust/contents/), and [Rust `.github`](https://api.github.com/repos/rust-lang/rust/contents/.github).
- “Observed” below means documented in an inspected primary source, not proven to happen for every contribution. Recommendations are this note's judgments, not upstream requirements for this CLI.
- Sources use moving default branches or live documentation. Recheck policies before copying them, especially LLM rules. No review-throughput measurements, contributor interviews, branch-protection inspection, or security-response exercises were performed.
- Only this research note is added. No code, configuration, issue templates, governance, or license decisions are changed.

## 1. Contributor onboarding and community

### Kubernetes: a small entry point backed by a large community repository

**Observed.** The main repository's [CONTRIBUTING.md](https://raw.githubusercontent.com/kubernetes/kubernetes/master/CONTRIBUTING.md) points to a separate community contributor guide and requires a Contributor License Agreement. The community [getting-started guide](https://raw.githubusercontent.com/kubernetes/community/main/contributors/guide/README.md) presents prerequisites and a first-contribution path, explicitly says a development environment is not required for every contribution, and provides a playground for learning the PR process. Its [README](https://raw.githubusercontent.com/kubernetes/community/main/README.md) recognizes documentation and talks as contributions and describes committees, SIGs, subprojects, and temporary cross-SIG working groups.

**Adopt.** Make the contribution entry point easy to find and explicitly welcome documentation, accessibility, reproducible bug reports, synthetic examples, and tests—not only Python changes. Separate “report a problem” from “set up the development environment.”

**Adapt.** Keep all essential instructions in this repository. Link to existing setup/check commands instead of reproducing them in several guides. Mark a few genuinely bounded, maintainer-supported issues as suitable first contributions; a label without context or review capacity is not onboarding.

**Skip.** A separate community repository, SIGs, membership ladders, workshops, and a contributor-playground repository. Do not introduce a CLA simply because Kubernetes has one; first resolve this project's own licensing and contribution terms. The existing research note already flags dependency licensing considerations in [RESEARCH.md](RESEARCH.md#pdf-dependency-license).

### Rust: explicit routes to help and the right documentation

**Observed.** Rust's [CONTRIBUTING.md](https://raw.githubusercontent.com/rust-lang/rust/main/CONTRIBUTING.md) thanks contributors, names a newcomer help channel, distinguishes compiler and standard-library guides, and directs submodule/subtree changes to their owning repositories. The official [contribution procedures](https://rustc-dev-guide.rust-lang.org/contributing.html) welcome bug reports even when the reporter is uncertain, call duplicate searching “extra credit,” and route security-sensitive bugs away from ordinary public reports.

**Adopt.** A welcoming tone, one clear place to ask questions, and permission to report an uncertain bug. Treat contributor time and language fluency as constraints, not qualifications.

**Adapt.** Use English for canonical project instructions and identifiers, short sentences, and copyable commands; welcome questions from non-native speakers without grammar policing. Start with GitHub issues for ordinary questions rather than requiring a new chat account. Clearly distinguish deterministic PDF checks from model-generated assessments so reports reach the right maintainer context. These language/channel choices are recommendations, not claimed Rust or Kubernetes requirements.

**Skip.** Multiple discussion platforms and specialist contributor books until actual contributor traffic justifies them.

### Conduct needs an actual reporting and enforcement path

**Observed.** Kubernetes' [conduct entry](https://raw.githubusercontent.com/kubernetes/community/main/code-of-conduct.md) adopts the CNCF code of conduct and names its conduct committee and reporting address. Rust's repository [conduct entry](https://raw.githubusercontent.com/rust-lang/rust/main/CODE_OF_CONDUCT.md) links to its official [conduct policy](https://www.rust-lang.org/conduct.html), which describes inclusive behavior, private harassment reporting, moderation actions, and private appeals. Rust explicitly warns projects reusing its conduct policy to identify their own moderation arrangements rather than imply the Rust team will enforce them.

**Adopt.** State expected behavior, where it applies, who handles reports, and how to report privately. Explain available enforcement actions and how conflicts involving the maintainer are handled.

**Adapt.** Name the real responsible person and, only if someone has agreed, an alternate for conflicts. Do not advertise an independent committee or confidential channel that does not exist. Maintain a practical policy a small project can actually operate.

**Skip.** Standing committees and claims that CNCF or Rust moderators handle this project's incidents.

## 2. Review and contribution quality

### Kubernetes: separate technical review from holistic acceptance

**Observed.** The community [contribution guide](https://raw.githubusercontent.com/kubernetes/community/main/contributors/guide/contributing.md) asks for focused patches, clear rationale, relevant tests, and respectful review; its suggested review order is idea, architecture, then polish. [OWNERS documentation](https://raw.githubusercontent.com/kubernetes/community/main/contributors/guide/owners.md) describes reviewer and approver roles, directory ownership, `/lgtm` and `/approve`, and Prow/Tide automation. Technical reviewers examine correctness and engineering; approvers consider compatibility and cross-feature implications. [Community expectations](https://raw.githubusercontent.com/kubernetes/community/main/contributors/guide/expectations.md) emphasize the effect reviewers have on newcomers and timely responses or reassignment when reviewers are unavailable.

**Adopt.** Review the problem and approach before spending time on cosmetic details. Require a concise explanation of what changed, why, and what was checked. Give actionable, respectful comments that distinguish required changes from suggestions.

**Adapt.** One maintainer can perform both the technical and product/compatibility checks explicitly; these need not become two roles or approvals. Ask another knowledgeable person for high-risk changes when available, without presenting that as an already guaranteed capability. Use a small checklist covering behavior, regression evidence, user-facing errors, output/schema compatibility, privacy, and documentation. Record review availability honestly; do not promise a response SLA the maintainer cannot sustain.

**Skip.** Prow/Tide deployment, nested OWNERS trees, aliases, bot command conventions, and mandatory multi-role sign-offs. Reconsider native CODEOWNERS only when distinct areas have multiple active owners.

### Rust: preserve reasoning and make review state visible

**Observed.** Rust's compiler [review policy](https://forge.rust-lang.org/compiler/reviews.html) requires knowledgeable review, clear description and rationale, attention to risks and compatibility, and enough context to reconstruct a decision years later. It discusses regression tests, documentation, impartiality, and splitting oversized changes. Its [PR lifecycle](https://rustc-dev-guide.rust-lang.org/pr-lifecycle.html) documents automatic reviewer assignment, waiting-on-author/review states, human approval followed by a bot-managed merge queue, and patience with volunteer reviewers. These are compiler-project practices, not universal requirements for Rust packages.

**Adopt.** Keep decisions and trade-offs in public issues/PRs instead of leaving essential reasoning in private chat. Record meaningful test evidence and explicitly say when something was not checked.

**Adapt.** A short PR template can ask for problem, approach, checks, risks, and relevant issue. Two review-state labels are enough if ambiguity becomes a recurring problem; otherwise ordinary PR comments suffice. For this CLI, review changes to profile identifiers, generated files, evidence references, loopback restrictions, PDF handling, and model output assumptions as compatibility/security changes—not merely internal refactors.

**Skip.** Bors, rollups, compiler proposal processes, ecosystem-wide compilation experiments, and release-team triage machinery. Native repository checks and a manual maintainer merge are sufficient at small volume.

### Issue templates should obtain evidence without collecting personal data

**Observed.** Kubernetes' [bug report form](https://raw.githubusercontent.com/kubernetes/kubernetes/master/.github/ISSUE_TEMPLATE/bug-report.yaml) asks what happened, expected behavior, a minimal reproduction, versions/environment, and warns security reporters to disclose privately. Rust's contribution procedures similarly favor descriptive issue titles and appropriate templates.

**Adapt.** Ask for CLI version, OS/Python versions, command, expected/actual result, and a minimal synthetic profile/PDF when needed. Ask for model tag and Ollama version only for model-dependent failures. Warn reporters not to attach real resumes, contact information, private job material, or unredacted output directories; do not request full environment dumps that may contain secrets. Permit incomplete reports and help refine them. Do not copy Kubernetes-specific infrastructure fields.

## 3. Security disclosure

### Kubernetes: clear separation from ordinary support

**Observed.** The community [security policy](https://raw.githubusercontent.com/kubernetes/community/main/SECURITY.md) links reporting instructions, supported-version policy, and announcements. Official [disclosure documentation](https://kubernetes.io/docs/reference/issues-security/security/) offers a bug-bounty channel and private security email, distinguishes vulnerabilities from hardening/support requests, describes acknowledgment within three working days, and coordinates public disclosure with mitigation readiness. These are Kubernetes' commitments, not proposed commitments for this project.

### Rust: explicit scope, supported releases, and private review

**Observed.** Rust's [security policy](https://www.rust-lang.org/policies/security) names a private reporting address, describes scope and exclusions, gives acknowledgment/update expectations, and explains coordinated fixes, private review, disclosure, and supported release channels. Its trust assumptions are toolchain-specific: it generally treats source code and dependencies as trusted. They must not be copied into a document-processing CLI that deliberately accepts external PDFs or job text.

**Adopt.** Provide a private reporting route before public promotion, define supported releases, and separate public bug reports from vulnerabilities. Coordinate fixes and user guidance before releasing sensitive exploit details where possible.

**Adapt.** Publish one monitored private channel, report requirements, and realistic response expectations. State whether only the latest stable CLI release receives fixes. Include malicious documents, unintended file access/overwrite, personal-data exposure, dependency vulnerabilities, and unintended network transmission in triage scope. Ordinary inaccurate model prose can be a quality bug; a prompt injection that crosses a trust boundary deserves security evaluation. These CLI-specific boundaries require an explicit project decision, not an inherited upstream policy.

**Skip.** Bug bounty promises, distributor embargo networks, dedicated response committees, and Rust/Kubernetes response-time promises. A local-first product still needs security reporting; “offline” is not evidence of safety.

## 4. Human-first, agent-ready contributions

**Observed.** Kubernetes' inspected [AGENTS.md](https://raw.githubusercontent.com/kubernetes/kubernetes/master/AGENTS.md) asks for focused changes, relevant tests, AI-use disclosure, and reminders that the human author is responsible; it also documents generated-file constraints and commands. Rust's [CONTRIBUTING.md](https://raw.githubusercontent.com/rust-lang/rust/main/CONTRIBUTING.md) and [PR template](https://raw.githubusercontent.com/rust-lang/rust/main/.github/pull_request_template.md) link an explicit LLM policy and disclosure instructions.

Rust's current [LLM policy](https://forge.rust-lang.org/policies/llm-usage.html) is notably stricter than a generic “AI allowed with disclosure” policy. Within its stated repository/team scope it prohibits, among other things, originally LLM-created documentation and personal-account comments, substituting LLM judgment for human judgment, and agent-required contribution processes. It conditionally permits other uses, including an experimental route for pre-arranged, non-critical, well-tested, well-reviewed generated code with disclosure. Review bots require maintainer approval and remain advisory. The policy explicitly says human documentation must remain primary; `AGENTS.md` may summarize but must not uniquely hold necessary instructions.

**Adopt.** Human-readable instructions are authoritative. Humans own submissions and merge decisions. Disclose material agent assistance, verify generated claims, never require an AI account, and never make automated review alone sufficient to merge or reject work.

**Adapt.** Define this project's own short AI policy: acceptable assistance, contributor accountability, evidence expectations, and limits on unsolicited bot output. Keep agent guidance a concise index of existing human instructions plus repository safety constraints. Prohibit putting real resume data or secrets into external tools without explicit consent. Require permission before bots post reviews or open issues/PRs at scale. Agent readiness means predictable commands and reviewable artifacts, not autonomous write access or mandatory infrastructure.

**Skip.** Copying Rust's policy verbatim, especially compiler-specific soundness rules, experimental quotas, or private organizational channels. Do not claim Rust welcomes unrestricted generated contributions. Decide any restrictions on generated prose/code deliberately, including their effect on translation and accessibility assistance.

## Minimal adoption sequence (recommendation only)

1. **Before inviting contributors:** settle project licensing/contribution terms; provide one concise contribution entry point, an enforceable conduct/reporting path, and a real private security contact. Link existing setup and verification instructions rather than create competing versions.
2. **For the first external PRs:** use minimal bug/PR prompts, synthetic reproduction guidance, a short maintainer review checklist, and an explicit human-accountable AI policy. State maintainer capacity honestly.
3. **Only when actual traffic requires it:** add review-state labels, backup maintainers, path ownership, or additional communication channels. Introduce each mechanism to solve an observed routing/review problem.

Success is a stranger being able to understand the project, report a problem without exposing their resume, make a bounded change without an agent, and understand why the maintainer accepted or declined it. Kubernetes-scale governance is not a prerequisite.

## Not checked and risks

No builds, tests, formatters, policy-enforcement checks, or live reporting channels were exercised. Upstream policy URLs may change; review them before implementation. This note does not establish legal sufficiency, a staffed moderation process, security-response capacity, or an upstream endorsement.
