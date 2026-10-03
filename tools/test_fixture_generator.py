"""Generator-backed synthetic examples are deterministic and self-identifying."""
import hashlib
import json
from pathlib import Path

from make_fixtures import generate


def test_fixture_check_detects_drift_without_overwriting(tmp_path):
    generate(tmp_path)
    assert generate(tmp_path, check=True) == 0
    target = tmp_path / "console.json"
    altered = target.read_bytes() + b"\n"
    target.write_bytes(altered)
    assert generate(tmp_path, check=True) == 1
    assert target.read_bytes() == altered


def test_file_data_contracts_have_generator_owned_examples(tmp_path):
    root = Path(__file__).resolve().parents[1]
    classes = json.loads((root / ".dataclass.json").read_text())
    generate(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for relative in classes["data"]:
        if relative.endswith("/"):
            continue
        example = relative + ".example"
        assert example in classes["fixture"], example
        assert example in manifest["files"], example


def test_fixture_generator_emits_reproducible_manifest(tmp_path):
    # TMPDIR is set by the caller; generated artifacts never inspect host state.
    first, second = tmp_path / "first", tmp_path / "second"
    generate(first)
    generate(second)
    manifest = json.loads((first / "manifest.json").read_text())
    assert manifest["synthetic_origin"] is True
    for relative, expected_hash in manifest["files"].items():
        name = Path(relative).name
        assert (first / name).read_bytes() == (second / name).read_bytes()
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == expected_hash
        assert (Path(__file__).resolve().parents[1] / relative).read_bytes() == (first / name).read_bytes()
