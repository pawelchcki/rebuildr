from rebuildr.cli import load_py_desc
from rebuildr.context import LocalContext
from rebuildr.stable_descriptor import StableEnvironment
from tests.utils import resolve_current_dir

current_dir = resolve_current_dir(__file__)


def test_basic_properties():
    desc = load_py_desc(current_dir / "simple.rebuildr.py")

    assert desc.inputs.envs[0].key == "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"
    assert str(desc.inputs.files[0].target_path) == str("test.txt")


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

    m.update("test.txt".encode())
    with open(current_dir / "test.txt", "r") as f:
        m.update(f.read().encode())

    m.update("test_renamed.txt".encode())
    with open(current_dir / "test.txt", "r") as f:
        m.update(f.read().encode())

    assert desc.sha_sum(env) == m.hexdigest()

    assert (
        desc.sha_sum(env)
        == "7c4c0b37896d9404f8c48ba5238b3cb9c2bbba6dda7ea1ed11ff9a42cef4e256"
    ), "sha sum is not correct"

    # changing the env should change the sha sum
    import os

    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = "something else"
    assert (
        desc.sha_sum(env)
        == "e0ee77349e2e81a4a0d41b337437cc08e490139f55ce88ff4369a192703a7c12"
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
        "./src/test_renamed.txt",
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
        == "1ae50efb0efe369f148826935f1cc6feeff2429f808bfe0aaf904fd8389f6876"
    )


def test_inputs_dict_consistency():
    desc = load_py_desc(current_dir / "simple_with_glob.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    assert desc.stable_inputs_dict(env) == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "build_args": [],
            "files": [{"target_path": "second_file.txt"}, {"target_path": "test.txt"}],
            "builders": [{"target_path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "f380815bce00259e731c4361c7ada90095ac6aa5db021668d0fcf6dbdad2fd30",
    }
