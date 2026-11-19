# Security

Report vulnerabilities privately through GitHub: Security tab → "Report a vulnerability". Do not open a public issue.

This tool processes untrusted input: imported PDFs, job description text, and generated documents. Injection, SSRF, or data-leak paths are in scope; include a reproduction.

Intentionally out of scope: the Ollama container binds to `127.0.0.1` without authentication by design — do not expose it to a network.
