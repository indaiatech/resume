# Agent guidance

Instructions for coding agents working in this repository. Setup, tests, and
ground rules live in [CONTRIBUTING.md](CONTRIBUTING.md); privacy notes live in
the [README](README.md).

## Profile and the Gist

`profile.yaml` is the owner's personal file. It stays out of Git and is
versioned in the owner's secret Gist, configured through `PROFILE_GIST_URL`
in `.env`.

- After every change to `profile.yaml` — any field, however small — publish it
  before finishing: `task profile-sync`. Do not batch it for later and do not
  leave it to the owner.
- If `.env` has no `PROFILE_GIST_URL`, leave the change local and say so in
  your reply instead of publishing.
- Never commit `profile.yaml`, other `profile*.yaml` files, `.env`, or
  `*.gist-sync.json`; never print the Gist URL or profile contents in chat or
  command output.
- `task resume` refuses to run while local profile edits are unpublished; that
  guard is intentional. Publishing resolves it.
