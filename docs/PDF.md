# Illustrated PDF editions

The two PDF editions are built from the **existing single-page Markdown sources** in `book/es.md` and `book/en.md`. Their chapter sources live in `book/es/` and `book/en/`. No independent PDF text is maintained.

## Build locally

Install `pandoc`, a font such as DejaVu Sans, and the Python packages `weasyprint==68.0` and `pypdf==5.9.0`. On Ubuntu install `libpango-1.0-0` and `libpangocairo-1.0-0` if required.

```bash
python3 scripts/check.py
python3 scripts/build_pdf.py --lang all
```

Outputs (ignored by Git):

- `dist/de-la-caja-negra-a-la-evidencia-es.pdf`
- `dist/from-black-box-to-evidence-en.pdf`

Each edition has its own full-page cover, a clickable table of contents with page numbers, 37 chapters, seven annexes, all 41 diagrams, code listings, selected searchable text and A4 pages. Remote resource fetching is blocked while rendering: all figures must be present in the repository.

## Preview in a pull request

The **Book PDF preview** GitHub Actions workflow builds and uploads both PDF editions as an ephemeral **workflow artifact** (`book-pdf-preview-es-en`). The artifact is for review only. It does not create a tag, change the version or publish a GitHub Release.

## Publish after merge

The **Release** workflow publishes a normal edition from a deliberately pushed `v*` tag pointing to a commit already merged into `main`. It attaches both PDF editions and both existing whole-book Markdown files. Two *exactly named*, maintainer-approved mainline merge commits are exceptional one-shot triggers: the historical first edition `v2026.10.29` and the explicitly labelled **research pre-release `v2026.10.31-rc1`**. An ordinary PR merge does not publish a release; the preview trigger refuses existing tags and never overwrites an edition.

No existing edition number is changed by this PDF feature. The first version/release is an explicit maintainer decision **after** the PR is merged and validated.

## First tagged release

The author-approved merge of PR #2 is the one-time publishing trigger for the existing edition identifier `v2026.10.29`. The merge commit must have the exact title `release: publish first PDF edition after PR #2 merge`. After the PDF build succeeds, the same GitHub Actions job creates the tag (without altering existing files or changing the edition number) and publishes the four assets together. GitHub's token-generated tag does not need to trigger a second workflow. Later releases are initiated only by a deliberately created `v*` tag pointing to `main`.
