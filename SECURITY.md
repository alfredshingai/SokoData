# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

Only the latest release on `main` branch receives security updates.

## Reporting a Vulnerability

**Do not open a public issue** for security vulnerabilities.

Email: **alfredshingai@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

| Severity | Initial Response | Fix Target |
| -------- | ---------------- | ---------- |
| Critical (RCE, auth bypass, data exposure) | 24 hours | 72 hours |
| High (SQLi, SSRF, privilege escalation) | 48 hours | 7 days |
| Medium (XSS, info disclosure, DoS) | 5 days | 30 days |
| Low (minor info leak, cosmetic) | 14 days | Next release |

## Disclosure Process

1. Reporter emails vulnerability details
2. Maintainer acknowledges within SLA
3. Fix developed and tested in private
4. Fix deployed to production
5. Public advisory issued (GitHub Security Advisory + release notes)
6. Credit given to reporter (unless anonymity requested)

## Scope

In scope:
- API endpoints (`/v1/*`)
- ETL pipeline (data integrity, injection)
- Authentication/authorization (API keys, webhooks)
- Dependency vulnerabilities (via `pip-audit` in CI)

Out of scope:
- Third-party data source vulnerabilities (WFP, WB, Open-Meteo, etc.)
- User-deployed instances with custom config
- Social engineering / phishing

## Security Practices in Codebase

- Parameterized queries (DuckDB) — no string interpolation
- Input validation via Pydantic on all API endpoints
- Rate limiting on all public endpoints
- API keys hashed (bcrypt) at rest
- Secrets via environment variables only (never in code)
- `pip-audit` runs in CI on every PR
- Dependabot alerts enabled

## Hardening Checklist (for deployers)

- [ ] Use strong `API_KEY_SECRET` (32+ chars, random)
- [ ] Enable HTTPS (Render provides by default)
- [ ] Restrict CORS to known origins in production
- [ ] Monitor `/v1/health` and webhook delivery failures
- [ ] Rotate API keys quarterly
- [ ] Review webhook subscriptions for unauthorized endpoints