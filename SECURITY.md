# Security

The lab is didactic: it processes no real data, exposes no services and runs without network access. Even so, if you find a vulnerability in the scripts, the container recipe or the GitHub Actions workflows, do not open a public issue. Use **Security → Report a vulnerability** in this repository to send a private report with the file, the impact and how to reproduce it. You will get an acknowledgement and, once fixed, credit in the CHANGELOG if you wish.

| Scope | Included |
|---|---|
| `scripts/`, `lab/` (code, `Containerfile`, scripts), `.github/workflows/` | Yes |
| Errors in the book's content | No: open an erratum |
| Third-party products (GnuCOBOL, .NET, SQLite, Podman) | No: report to the relevant project |
