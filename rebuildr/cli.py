from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import tarfile
from rebuildr.build import DockerCLIBuilder
from rebuildr.containers.util import (
    image_exists_in_registry,
    image_exists_locally,
    pull_image,
    push_image,
)
from rebuildr.descriptor import Descriptor
# typer is used to speed up development - ideally for ease of embedding
# we shouldn't rely on 3rd party code a lot

import importlib.util
import sys

from rebuildr.fs import Context, TarContext
from rebuildr.stable_descriptor import StableDescriptor, StableImageTarget


def load_py_desc(path: str) -> StableDescriptor:
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = module
    spec.loader.exec_module(module)
    absolute_dirname = Path(os.path.dirname(os.path.abspath(path)))

    image = StableDescriptor.from_descriptor(module.image, absolute_dirname)

    return image


def parse_and_print_py(path: str):
    desc = load_py_desc(path)
    data = desc.stable_inputs_dict()

    print(json.dumps(data, indent=4, sort_keys=True))


def build_docker(path: str):
    desc = load_py_desc(path)

    if len(desc.targets) != 1:
        raise ValueError(
            "WIP - for now - Only one target is supported for docker build"
        )

    target = desc.targets[0]

    if not isinstance(target, StableImageTarget):
        raise ValueError("WIP - for now - Image target is supported for docker build")

    content_id_tag = (
        target.content_id_tag(desc.inputs) if target.also_tag_with_content_id else None
    )

    if content_id_tag and image_exists_locally(content_id_tag):
        logging.info(f"Tag {target.content_id_tag(desc.inputs)} already exists")
        return content_id_tag
    elif content_id_tag and image_exists_in_registry(content_id_tag):
        logging.info(
            f"Tag {target.content_id_tag(desc.inputs)} already exists in registry, downloading"
        )
        pull_image(content_id_tag)
        return content_id_tag

    ctx = Context.temp()
    ctx.prepare_from_descriptor(desc)

    builder = DockerCLIBuilder()

    tags = target.image_tags(desc.inputs)

    if len(tags) == 0:
        raise ValueError("No tags specified")

    dockerfile_path = ctx.root_dir / target.dockerfile
    builder.build(
        root_dir=ctx.src_path(),
        dockerfile=dockerfile_path,
        tags=tags,
        platform="linux/amd64,linux/arm64",
    )

    if content_id_tag:
        return content_id_tag
    else:
        return tags[0]


def build_tar(path: str, output: str):
    desc = load_py_desc(path)

    ctx = TarContext()
    ctx.prepare_from_descriptor(desc)

    ctx.copy_to_file(Path(output))


def print_usage():
    print("Usage: rebuildr <command> <args>")
    print("Commands:")
    print("  load-py <rebuildr-file>")
    print("  load-py <rebuildr-file> materialize-image")
    print("  load-py <rebuildr-file> push-image")
    print("  load-py <rebuildr-file> build-tar <output>")


def parse_cli():
    args = sys.argv[1:]
    if len(args) == 0:
        logging.error("No arguments provided")

        print_usage()
        return

    if args[0] == "load-py":
        parse_cli_parse_py(args[1:])
        return

    logging.error(f"Unknown command: {args[0]}")
    print_usage()
    return


def parse_cli_parse_py(args):
    if len(args) == 0:
        logging.error("Path to rebuildr file is required")
        return

    file_path = args[0]
    args = args[1:]

    if len(args) == 0:
        parse_and_print_py(file_path)
        return

    if "materialize-image" == args[0]:
        print(build_docker(file_path))
        return

    if "push-image" == args[0]:
        tag = build_docker(file_path)
        push_image(tag)
        print(tag)
        return

    if "build-tar" == args[0]:
        if len(args) < 2:
            logging.error("Tar path is required")
            return
        else:
            build_tar(file_path, args[1])
        return

    if args[0] == "-h" or args[0] == "--help":
        print_usage()
        return

    logging.error(f"Unknown command: {args[0]}")
    print_usage()


def main():
    logging.basicConfig(level=logging.DEBUG)
    parse_cli()


if __name__ == "__main__":
    main()
