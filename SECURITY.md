# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities by emailing the repository owner directly.
Do not open public issues for security problems.

## Security Measures

This repository implements:
- **Branch protection** on `main` (required PR reviews, linear history, no force pushes)
- **Dependency scanning** via `safety` and `pip-audit`
- **SAST scanning** via `bandit`
- **Secret scanning** via GitHub Advanced Security
- **Production deployment** via gunicorn (not Flask dev server with debug mode)
