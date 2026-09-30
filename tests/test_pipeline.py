"""Which markdown files ingestion indexes."""
from pathlib import Path

from ingestion.pipeline import EXCLUDED_DIRS, iter_markdown_files


def _touch(root, rel):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# x\n", encoding="utf-8")


def test_excludes_mock_api_and_alarms_at_any_depth(tmp_path):
    for rel in (
        "starter-kit/docs/user-guide/troubleshoot/coe-device-errors.md",
        "starter-kit/docs/part-programmers-reference/05-functions.md",
        "starter-kit/mock-api/INTERFACE.md",
        "starter-kit/mock-api/README.md",
        "starter-kit/alarms/notes.md",
        "alarms/top-level.md",
    ):
        _touch(tmp_path, rel)

    files = [p.relative_to(tmp_path).as_posix() for p in iter_markdown_files(tmp_path)]

    assert files == [
        "starter-kit/docs/part-programmers-reference/05-functions.md",
        "starter-kit/docs/user-guide/troubleshoot/coe-device-errors.md",
    ]


def test_only_directories_are_excluded_not_similarly_named_files(tmp_path):
    _touch(tmp_path, "docs/alarms.md")
    _touch(tmp_path, "docs/receive-alarms/overview.md")

    files = [p.relative_to(tmp_path).as_posix() for p in iter_markdown_files(tmp_path)]

    assert files == ["docs/alarms.md", "docs/receive-alarms/overview.md"]


def test_real_corpus_keeps_the_emcy_doc_and_drops_mock_api():
    files = [p.as_posix() for p in iter_markdown_files(Path("docs/docs-proto"))]

    assert any(f.endswith("user-guide/troubleshoot/coe-device-errors.md") for f in files)
    assert not any(set(Path(f).parts) & EXCLUDED_DIRS for f in files)
