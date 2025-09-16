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
            "files": [{"path": "second_file.txt"}, {"path": "test.txt"}],
            "builders": [{"path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "72416769611cf07d0344276cedf44de2e722ea2f7a91ed965dc39c52cbc62d36",
    }


def test_build_args_ignored_for_hashing_if_not_set():
    desc = load_py_desc(current_dir / "build_args.rebuildr.py")
    env = StableEnvironment.from_os_env()
    env.env["_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"] = ""

    assert desc.stable_inputs_dict(env) == {
        "inputs": {
            "envs": [{"key": "_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"}],
            "build_args": [{"key": "arg"}],
            "files": [{"path": "second_file.txt"}, {"path": "test.txt"}],
            "builders": [{"path": "simple.Dockerfile"}],
            "external": [],
        },
        "sha256": "19ff9c6aaccc44204b9df6e04123e25ccfcd00208c1c3f5d7434a38d9ea031e6",
    }
