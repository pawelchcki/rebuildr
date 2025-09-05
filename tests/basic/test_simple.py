from rebuildr.cli import load_py_desc
from rebuildr.context import LocalContext
from rebuildr.fs import Context
from rebuildr.stable_descriptor import StableEnvironment
from tests.utils import resolve_current_dir

current_dir = resolve_current_dir(__file__)


def test_basic_properties():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    assert desc.inputs.envs[0].key == "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"
    assert str(desc.inputs.files[0].path) == str("test.txt")


def test_sha_sum():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    import hashlib

    m = hashlib.sha256()
    m.update("_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM".encode())
    print("example: " + m.hexdigest())
    with open(current_dir / "simple.Dockerfile", "r") as f:
        m.update(f.read().encode())

    with open(current_dir / "test.txt", "r") as f:
        m.update(f.read().encode())

    assert desc.sha_sum(env) == m.hexdigest()

    assert (
        desc.sha_sum(env)
        == "e2b803a131a4bac358aeb8f6eec7428f576fb7239155ad2a34bef1864054d2a1"
    ), "sha sum is not correct"

    # changing the env should change the sha sum
    import os

    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = "something else"
    assert (
        desc.sha_sum(env)
        == "ebe6d57945599f48f79959fb4206381b488cdacd5cd0c9c2efafa379eca73a49"
    )
    os.environ["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""


def test_context_prepare():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    ctx = LocalContext.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    files_in_ctx.sort()
    assert files_in_ctx == [
        "./simple.Dockerfile",
        "./src",
        "./src/test.txt",
    ]


def test_context_prepare_with_glob():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")

    ctx = LocalContext.temp()
    ctx.prepare_from_descriptor(desc)

    assert str(ctx.root_dir) != str(current_dir)
    assert str(ctx.root_dir / "test.txt") != str(current_dir / "test.txt")

    import glob

    files_in_ctx = glob.glob("./**/*", root_dir=ctx.root_dir, recursive=True)
    files_in_ctx.sort()
    assert files_in_ctx == [
        "./simple.Dockerfile",
        "./src",
        "./src/second_file.txt",
        "./src/test.txt",
    ]


def test_with_binary_file():
    desc = load_py_desc(current_dir / "simple_with_binary_file.rebuildr.py")
    env = StableEnvironment.from_os_env()
    assert (
        desc.sha_sum(env)
        == "7da05a4083203b1fdb83b111c46f2b20fbcbb219301ecbb1deb076e7557b6a6f"
    )


def test_inputs_dict_consistency():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    assert desc.stable_inputs_dict(env) == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "build_args": [],
            "files": [{"path": "second_file.txt"}, {"path": "test.txt"}],
            "builders": [{"path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "19ff9c6aaccc44204b9df6e04123e25ccfcd00208c1c3f5d7434a38d9ea031e6",
    }
