from dataclasses import asdict
import json
import logging
import os
from rebuildr.descriptor import Descriptor
# typer is used to speed up development - ideally for ease of embedding
# we shouldn't rely on 3rd party code a lot

import importlib.util
import sys



def load_py(path: str) -> Descriptor:
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = module
    spec.loader.exec_module(module)
    absolute_dirname = os.path.dirname(os.path.abspath(path))
    image = module.image.postprocess_paths(absolute_dirname)

    return image

def parse_py(path: str) -> Descriptor:
    desc = load_py(path)
    
    data = {
        "image": asdict(desc),
        "sha256": desc.sha_sum(),
    }

    print(json.dumps(data, indent=4, sort_keys=True))
    return desc

def built_ctx(path: str):
    desc = load_py(path)
    

    return

def print_usage():
    print("Usage: rebuildr <command> <args>")
    print("Commands:")
    print("  parse-py <path>")
    return

def parse_cli():
    args = sys.argv[1:]
    if len(args) == 0:
        logging.error("No arguments provided")

        print_usage()
        return

    if args[0] == "parse-py":
        if len(args) < 2:
            logging.error("No path provided")
            return
        parse_py(args[1])
        return
    

    logging.error(f"Unknown command: {args[0]}")
    print_usage()
    return

def main():
    logging.basicConfig(level=logging.DEBUG)
    parse_cli()

