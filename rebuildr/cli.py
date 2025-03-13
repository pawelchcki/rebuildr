from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
from rebuildr.build import DockerCLIBuilder
from rebuildr.descriptor import Descriptor, TagTarget
# typer is used to speed up development - ideally for ease of embedding
# we shouldn't rely on 3rd party code a lot

import importlib.util
import sys

from rebuildr.fs import Context
from rebuildr.stable_descriptor import StableDescriptor


def load_py_desc(path: str) -> StableDescriptor:
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = module
    spec.loader.exec_module(module)
    absolute_dirname = Path(os.path.dirname(os.path.abspath(path)))

    image = StableDescriptor.from_descriptor(module.image, absolute_dirname)

    return image


def parse_py(path: str) -> Descriptor:
    desc = load_py_desc(path)

    json = desc.stable_json()

    print(json)
    return desc


def built_ctx(path: str):
    desc = load_py_desc(path)
    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    builder = DockerCLIBuilder()
    tags = []
    for tgt in desc.targets:
        if isinstance(tgt, TagTarget):
            # by default tag with content_id
            tag = tgt.repository + ":src-id-" + desc.inputs.sha_sum()

            tags.append(tag)
            if tgt.tag:
                tags.append(tgt.repository + ":" + tgt.tag)

    iid = builder.build(
        root_dir=ctx.root_dir,
        dockerfile=None
        if desc.inputs.dockerfile is None
        else desc.inputs.dockerfile.path,
        tags=tags,
    )
    print(iid)

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

    if args[0] == "build-py":
        if len(args) < 2:
            logging.error("No path provided")
            return
        built_ctx(args[1])
        return

    logging.error(f"Unknown command: {args[0]}")
    print_usage()
    return


def main():
    logging.basicConfig(level=logging.DEBUG)
    parse_cli()
