from rebuildr.cli import load_py_desc
from rebuildr.stable_descriptor import StableEnvironment
from tests.utils import resolve_current_dir

current_dir = resolve_current_dir(__file__)


def test_build_args_are_read():
    desc = load_py_desc(current_dir / "build_args.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.build_args["arg"] = "value"
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    assert desc.stable_inputs_dict(env) == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "build_args": [{"key": "arg", "value": "value"}],
            "files": [{"target_path": "second_file.txt"}, {"target_path": "test.txt"}],
            "builders": [{"target_path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "1f04b905bc7e8221320ad315a06da50a063ccc1a1576452b56f0cdf9c9271c76",
    }


def test_build_args_ignored_for_hashing_if_not_set():
    desc = load_py_desc(current_dir / "build_args.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    assert desc.stable_inputs_dict(env) == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "build_args": [{"key": "arg"}],
            "files": [{"target_path": "second_file.txt"}, {"target_path": "test.txt"}],
            "builders": [{"target_path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "f380815bce00259e731c4361c7ada90095ac6aa5db021668d0fcf6dbdad2fd30",
    }
