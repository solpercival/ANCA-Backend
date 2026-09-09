# docs/ — documentation submodule (placeholder)

This directory is the mount point for the **cnc-documentation** repository,
owned by the documentation team and consumed here as a git submodule.

It is intentionally empty in a fresh clone. To populate it:

```bash
git submodule add git@github.com:your-org/cnc-documentation.git docs
git submodule update --init --recursive
```

The ingestion pipeline reads `*.md` here plus `reference-answers.json`
(the gold set used by the eval suite). Nothing in this folder is edited from
the engine repo — content changes happen upstream, and a submodule pointer
bump is a reviewed PR that re-triggers ingestion + evaluation.