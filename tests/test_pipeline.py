"""Which markdown files ingestion indexes."""

from pathlib import Path

from ingestion.pipeline import (
    EXCLUDED_DIRS,
    changed_document_hashes,
    collect_markdown,
    hash_file,
    hash_markdown_files,
    iter_markdown_files,
)


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


def test_hash_file_is_sha256_of_raw_bytes(tmp_path):
    path = tmp_path / "guide.md"
    path.write_bytes(b"# title\n")

    assert hash_file(path) == "497c96e612373c14de69c0cbd79e8c6b870cc73ae6da4037f1a1e0c58bcc9315"
    assert hash_file(path) == hash_file(path)


def test_hash_file_changes_when_one_byte_changes(tmp_path):
    path = tmp_path / "guide.md"
    path.write_bytes(b"# title\n")
    original = hash_file(path)

    path.write_bytes(b"# title\n ")

    assert hash_file(path) == "e62b7fceab05e0b1b3092f9a214f1f3c836d64126880474f4dfe395c5f32d55a"
    assert hash_file(path) != original


def test_hash_markdown_files_maps_sources_and_skips_excluded_dirs(tmp_path):
    kept = tmp_path / "guide.md"
    other = tmp_path / "nested" / "other.md"
    skipped = tmp_path / "mock-api" / "skip.md"
    kept.write_bytes(b"# title\n")
    other.parent.mkdir()
    other.write_bytes(b"# other\n")
    skipped.parent.mkdir()
    skipped.write_bytes(b"# skip\n")

    hashes = hash_markdown_files(tmp_path)

    assert hashes == {
        str(kept): "497c96e612373c14de69c0cbd79e8c6b870cc73ae6da4037f1a1e0c58bcc9315",
        str(other): hash_file(other),
    }


def test_changed_document_hashes_selects_missing_empty_and_different():
    current = {
        "same.md": "aaa",
        "edited.md": "bbb",
        "new.md": "ccc",
        "blank.md": "ddd",
    }
    stored = {
        "same.md": "aaa",
        "edited.md": "old",
        "blank.md": "",
        "gone.md": "zzz",
    }

    assert changed_document_hashes(current, stored) == {
        "edited.md": "bbb",
        "new.md": "ccc",
        "blank.md": "ddd",
    }


def test_collect_markdown_skips_sources_that_are_not_requested(tmp_path):
    docs = tmp_path / "docs"
    changed = docs / "changed.md"
    same = docs / "nested" / "same.md"
    changed.parent.mkdir()
    same.parent.mkdir(parents=True)
    changed.write_text("# Changed\nnew\n", encoding="utf-8")
    same.write_text("# Same\nold\n", encoding="utf-8")

    chunks = collect_markdown(docs, {str(changed)})

    assert chunks
    assert {chunk.source for chunk in chunks} == {str(changed)}


def test_real_corpus_keeps_the_emcy_doc_and_drops_mock_api():
    files = [p.as_posix() for p in iter_markdown_files(Path("docs/docs-proto"))]

    assert any(f.endswith("user-guide/troubleshoot/coe-device-errors.md") for f in files)
    assert not any(set(Path(f).parts) & EXCLUDED_DIRS for f in files)
