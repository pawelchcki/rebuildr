from pathlib import Path
import tarfile

from rebuildr.cli import load_py_desc
from rebuildr.fs import TarContext
from rebuildr.validators import target_path_is_not_root, target_path_is_set

from tests.utils import resolve_current_dir


def test_tar_context_includes_files_and_builders(tmp_path: Path):
    """TarContext should include both regular input files and builder files."""

    current_dir = resolve_current_dir(__file__)
    desc = load_py_desc(current_dir / "basic" / "simple.rebuildr.py")

    tc = TarContext()
    tc.prepare_from_descriptor(desc)

    output_tar = tmp_path / "ctx.tar"
    tc.copy_to_file(output_tar)

    assert output_tar.exists()

    with tarfile.open(output_tar, "r:") as tar:
        names = sorted(tar.getnames())

    # Expected file names inside archive
    assert names == [
        "simple.Dockerfile",
        "test.txt",
        "test_renamed.txt",
    ]


def test_validators_target_path_checks():
    # target_path_is_set should raise when path is empty or None
    for bad in ["", None]:
        try:
            target_path_is_set(bad, type("Dummy", (), {}))
        except ValueError:
            pass
        else:
            raise AssertionError("target_path_is_set did not raise for invalid value")

    # target_path_is_not_root should raise for root directories
    for bad in ["/", "."]:
        try:
            target_path_is_not_root(bad, type("Dummy", (), {}))
        except ValueError:
            pass
        else:
            raise AssertionError(
                "target_path_is_not_root did not raise for invalid value"
            )
