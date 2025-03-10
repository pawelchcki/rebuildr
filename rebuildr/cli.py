from dataclasses import asdict
import json
import os
from rebuildr.descriptor import Descriptor
# typer is used to speed up development - ideally for ease of embedding
# we shouldn't rely on 3rd party code a lot

import importlib.util
import sys


def hello(name: str):
    print(f"Hello {name}")


def parse_py(path: str) -> Descriptor:
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    foo = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = foo
    spec.loader.exec_module(foo)
    absolute_dirname = os.path.dirname(os.path.abspath(path))
    image = foo.image.postprocess_paths(absolute_dirname)

    data = {
        "image": asdict(foo.image),
        "sha256": image.sha_sum(),
    }

    print(json.dumps(data, indent=4, sort_keys=True))

    return foo.image


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        print("No arguments provided")
        print("Usage: rebuildr <command> <args>")
        print("Commands:")
        print("  parse-py <path>")
        return
    if args[0] == "parse-py":
        if len(args) < 2:
            print("No path provided")
            return
        parse_py(args[1])
