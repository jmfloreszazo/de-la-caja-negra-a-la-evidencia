# Book listing inventory and validation scope

**English** · [Español](BOOK_LISTINGS.es.md)

The [machine inventory](../evidence/editorial/book-listings.json) records all 32 fenced examples in each edition, their exact lines, SHA256, labels and missing dependencies. Twenty-seven executable/configuration blocks must have identical English bytes in ES and EN. The five text/Markdown blocks are narrative topology, recorded output or an evidence-sheet template; their prose may be translated.

The editorial correction aligns 17 formerly divergent executable/configuration blocks. It changes comments and example descriptions, not financial lab source or protected oracles. This is a source-language correction, not a new result of the historical experiment.

## Checks and their boundaries

- JSON: parse four documents across three fences, including the two separate example records in listing 27.3. Parsing does not establish that their sample approvals or observations are genuine.
- YAML: parse two mappings. This does not validate a mandate schema, authorize a user or execute a GitHub workflow.
- Bash: `bash -n` for both command blocks; no installation, PowerShell command or container is launched by this check.
- SQLite/Python: execute the exact printed 28.1 schema and the four displayed 28.4 predicates against a disposable consistent state; deliberately corrupt balance and postings and require rejection. This is not the full seven-invariant financial acceptance suite.
- Native selected listings: the dedicated CI compiles the complete printed 26.1 COBOL program, verifies exact identity with the protected reference source and checks all 58 pinned contract records. It also compiles/runs the four exact 12.2 rounding expressions and the complete 15.1 decoder with nine positive and six negative cases. The first original CI result remains pending until archived evidence is recorded below.
- Other COBOL/C#/T-SQL blocks remain application-context examples. CICS needs its transaction environment; Orleans needs actual grain/runtime types; database fragments need their schema/parameters. No fabricated interfaces or no-op stubs are used to claim these complete applications compile.

No listing label is promoted by static parsing or an isolated helper harness. The inventory preserves the published labels and explicitly records that complete integration and cross-platform reproduction are not established. Full Linux/macOS/Windows/WSL execution remains in #11.

| Listing | Language | Published label | Current static check |
| --- | --- | --- | --- |
| A.1 | bash | Reproduction commands · platform-dependent | BASH_SYNTAX |
| A.2 | bash | Requires GnuCOBOL and .NET 10 | BASH_SYNTAX |
| 3.1 | cobol | Illustrative | Context/harness required |
| 3.2 | csharp | Illustrative | Context/harness required |
| 3.3 | csharp | Executed | Context/harness required |
| 6.1 | json | Illustrative | JSON_SYNTAX |
| 9.1 | yaml | Illustrative | YAML_SYNTAX |
| 12.1 | cobol | Executed | Context/harness required |
| 12.2 | csharp | Illustrative | Context/harness required |
| 14.1 | csharp | Illustrative | Context/harness required |
| 15.1 | csharp | Illustrative · logic verified | Context/harness required |
| 17.1 | sql | Illustrative | Context/harness required |
| 17.2 | csharp | Illustrative | Context/harness required |
| 18.1 | sql | Illustrative | Context/harness required |
| 19.1 | csharp | Illustrative | Context/harness required |
| 20.1 | csharp | Illustrative | Context/harness required |
| 23.1 | csharp | Illustrative | Context/harness required |
| 24.1 | text | Executed · simulation | Context/harness required |
| 25a.1 | text | Illustrative topology | Context/harness required |
| 26.1 | cobol | Executed | EXACT_FULL_SOURCE_MATCH |
| 26.2 | text | Executed | Context/harness required |
| 26.3 | text | Executed | Context/harness required |
| 27.1 | csharp | Executed | Context/harness required |
| 27.2 | csharp | Executed | Context/harness required |
| 27.3 | json | Executed | JSON_SYNTAX |
| 27.4 | json | Executed | JSON_SYNTAX |
| 28.1 | sql | Executed | Context/harness required |
| 28.2 | csharp | Executed | Context/harness required |
| 28.3 | csharp | Executed | Context/harness required |
| 28.4 | python | Executed | PYTHON_SYNTAX |
| 31.1 | markdown | Illustrative | Context/harness required |
| 31.2 | yaml | Template · not enabled | YAML_SYNTAX |

## Reproduction

```bash
python3 scripts/check_language_policy.py --self-test
python3 scripts/audit_book_listings.py
# --write refreshes the reviewed inventory after an intentional book change.
# Native checks need SDK .NET 10, GnuCOBOL, Python 3.12 and PyYAML 6.0.3.
SOURCE_HEAD_SHA=$(git rev-parse HEAD) GITHUB_RUN_ID=local python3 scripts/run_book_listing_checks.py
```

The native runner records exact checkout, run ID, source hashes, tool versions, individual expected/observed COBOL records and raw compiler/runtime output before reporting failure. A source-only or skipped check is not a successful native run.
