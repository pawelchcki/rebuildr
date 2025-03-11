from rebuildr.cli import load_py_desc, parse_py
from rebuildr.fs import Context
from tests.utils import resolve_current_dir

current_dir = resolve_current_dir(__file__)


def test_basic_properties():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    assert desc.inputs.env[0].key == "EXAMPLE_ENV"
    assert desc.inputs.files[0].path == str(current_dir / "test.txt")


def test_sha_sum():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    import hashlib

    m = hashlib.sha256()

    m.update("EXAMPLE_ENV".encode())
    with open(current_dir / "test.txt", "r") as f:
        m.update(f.read().encode())
    with open(current_dir / "simple.Dockerfile", "r") as f:
        m.update(f.read().encode())

    assert (
        desc.sha_sum()
        == "ceb4a0286c40df1f8d7a090b8771f7cbfc2e976e8c915f6a1e23f925e290c9ef"
    ), "sha sum is not correct"
    assert desc.sha_sum() == m.hexdigest()

    # changing the env should change the sha sum
    import os

    os.environ["EXAMPLE_ENV"] = "something else"
    assert (
        desc.sha_sum()
        == "8a3d317957285aebdcb1154c335e6c46b257ceef03990adbf3295cea73bc9012"
    )


def test_context_prepare():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    assert files_in_ctx == [
        "./test.txt",
    ]


def test_context_prepare_with_glob():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")

    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    assert files_in_ctx == ["./second_file.txt", "./test.txt"]
