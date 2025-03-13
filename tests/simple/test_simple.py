from rebuildr.cli import load_py_desc, parse_py
from rebuildr.fs import Context
from tests.utils import resolve_current_dir

current_dir = resolve_current_dir(__file__)


def test_basic_properties():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    assert desc.inputs.envs[0].key == "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"
    assert desc.inputs.files[0].path == str("test.txt")


def test_sha_sum():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    import hashlib

    m = hashlib.sha256()
    m.update("_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM".encode())
    print("example: " + m.hexdigest())
    with open(current_dir / "simple.Dockerfile", "r") as f:
        m.update(f.read().encode())

    with open(current_dir / "test.txt", "r") as f:
        m.update(f.read().encode())

    assert desc.sha_sum() == m.hexdigest()

    assert (
        desc.sha_sum()
        == "e2b803a131a4bac358aeb8f6eec7428f576fb7239155ad2a34bef1864054d2a1"
    ), "sha sum is not correct"

    # changing the env should change the sha sum
    import os

    os.environ["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = "something else"
    assert (
        desc.sha_sum()
        == "ebe6d57945599f48f79959fb4206381b488cdacd5cd0c9c2efafa379eca73a49"
    )
    os.environ["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""


def test_context_prepare():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    assert files_in_ctx == [
        "./simple.Dockerfile",
        "./src",
        "./src/test.txt",
    ]


def test_context_prepare_with_glob():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")

    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    assert files_in_ctx == [
        "./simple.Dockerfile",
        "./src",
        "./src/second_file.txt",
        "./src/test.txt",
    ]


def test_xxx():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")

    assert desc.stable_inputs_dict() == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "files": [{"path": "second_file.txt"}, {"path": "test.txt"}],
            "builders": [{"path": "simple.Dockerfile"}],
        },
        "sha256": "19ff9c6aaccc44204b9df6e04123e25ccfcd00208c1c3f5d7434a38d9ea031e6",
    }
