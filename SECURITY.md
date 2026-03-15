# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | ✅ Yes              |
| < 1.0   | ❌ No               |

## Reporting a Vulnerability

If you discover a security vulnerability in PyZData, **please do not open a public issue.**

Instead, email the maintainer directly:

📧 **Jnv2252@Gmail.com**

Please include:

- A description of the vulnerability
- Steps to reproduce it
- Any potential impact
- Suggested fix (if you have one)

You should receive a response within **72 hours**. We will work with you to understand the issue and coordinate a fix before any public disclosure.

## Scope

Security issues we care about:

- **Credential leakage** — enctoken, password, or TOTP values being logged, cached to disk, or sent to unintended destinations
- **Injection attacks** — user input being passed unsafely to file paths, URLs, or shell commands
- **Dependency vulnerabilities** — known CVEs in `requests`, `pandas`, `streamlit`, etc.

## Out of Scope

- Zerodha API security — report those directly to [Zerodha](https://zerodha.com/contact)
- Rate limiting or account blocking by Zerodha — that's expected API behaviour
