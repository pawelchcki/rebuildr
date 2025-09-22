import json
import logging
import os
from pathlib import Path
from rebuildr.build import DockerCLIBuilder
from rebuildr.containers.util import (
    image_exists_in_registry,
    image_exists_locally,
    pull_image,
    push_image,
)


import importlib.util
import sys

from rebuildr.context import LocalContext
from rebuildr.fs import TarContext
from rebuildr.stable_descriptor import (
    StableDescriptor,
    StableEnvironment,
    StableImageTarget,
)


def load_py_desc(path: str | Path) -> StableDescriptor:
    # Disable bytecode generation for this import
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load descriptor from path: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = module

    original_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        # Restore the original setting
        sys.dont_write_bytecode = original_dont_write_bytecode

    root_absolute_dirname = Path(os.path.dirname(os.path.abspath(path)))
    # Check for environment variable to override the root directory
    root_dir_override = os.environ.get("REBUILDR_OVERRIDE_ROOT_DIR")
    if root_dir_override:
        logging.info(f"Overriding root directory with {root_dir_override}")
        root_absolute_dirname = Path(root_dir_override).resolve()
    image = StableDescriptor.from_descriptor(module.image, root_absolute_dirname)

    return image


def load_and_parse(path: str, build_args: dict[str, str]) -> dict[str, str]:
    desc = load_py_desc(path)
    env = StableEnvironment.from_os_env(build_args)

    if desc.targets is None or len(desc.targets) != 1:
        raise ValueError(
            "WIP - for now - Only one target is supported for docker build"
        )
    target = desc.targets[0]

    return (desc.stable_inputs_dict(env), target.content_id_tag(desc.inputs, env))


def parse_and_print_py(path: str, build_args: dict[str, str]):
    data, _ = load_and_parse(path, build_args)

    print(json.dumps(data, indent=4, sort_keys=True))


def parse_and_write_bazel_stable_metadata(
    path: str,
    build_args: dict[str, str],
    stable_metadata_file: str,
    stable_image_tag_file: str,
):
    data, content_id_tag = load_and_parse(path, build_args)

    try:
        with open(stable_metadata_file, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)
            f.write("\n")
    except (OSError, IOError) as e:
        raise RuntimeError(
            f"Failed to write stable metadata file {stable_metadata_file}: {e}"
        )

    try:
        with open(stable_image_tag_file, "w") as f:
            f.write(content_id_tag)
            f.write("\n")
    except (OSError, IOError) as e:
        raise RuntimeError(
            f"Failed to write stable image tag file {stable_image_tag_file}: {e}"
        )


def parse_build_args(args: list[str]) -> dict[str, str]:
    build_args = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            build_args[key] = value
    return build_args


class BuildDockerResult:
    tags: list[str]
    content_id_tag: str | None

    def __init__(self, tags: list[str], content_id_tag: str):
        self.tags = tags
        self.content_id_tag = content_id_tag

    def most_specific_tag(self) -> str:
        if self.content_id_tag is not None:
            return self.content_id_tag
        else:
            return self.tags[0]


# builds docker returns a list of tags associated with the build
def build_docker(
    path: str, build_args: dict[str, str], fetch_if_not_local: bool = True
) -> BuildDockerResult:
    desc = load_py_desc(path)
    env = StableEnvironment.from_os_env(build_args)

    if desc.targets is None or len(desc.targets) != 1:
        raise ValueError(
            "WIP - for now - Only one target is supported for docker build"
        )

    target = desc.targets[0]

    if not isinstance(target, StableImageTarget):
        raise ValueError("WIP - for now - Image target is supported for docker build")

    content_id_tag = (
        target.content_id_tag(desc.inputs, env)
        if target.also_tag_with_content_id
        else None
    )

    if content_id_tag and image_exists_locally(content_id_tag):
        logging.info(f"Tag {content_id_tag} already exists")
        return BuildDockerResult(tags=[content_id_tag], content_id_tag=content_id_tag)
    elif content_id_tag and image_exists_in_registry(content_id_tag):
        logging.info(f"Tag {content_id_tag} already exists in registry")
        if fetch_if_not_local:
            logging.info(f"Fetching tag {content_id_tag} from registry")
            pull_image(content_id_tag)
        else:
            logging.info(f"Skipping fetch of tag {content_id_tag} from registry")
        return BuildDockerResult(tags=[content_id_tag], content_id_tag=content_id_tag)

    tags = target.image_tags(desc.inputs, env)

    if len(tags) == 0:
        raise ValueError("No tags specified")

    ctx = LocalContext.temp()
    ctx.prepare_from_descriptor(desc)

    builder = DockerCLIBuilder()

    dockerfile_path = ctx.root_dir / target.dockerfile
    target_platforms = None
    do_load = False
    if target.platform is not None:
        target_platforms = target.platform.value
        do_load = True
    else:
        target_platforms = "linux/amd64,linux/arm64"

    builder.build(
        root_dir=ctx.src_path(),
        dockerfile=dockerfile_path,
        buildargs=build_args,
        tags=tags,
        platform=target_platforms,
        do_load=do_load,
    )

    return BuildDockerResult(tags=tags, content_id_tag=content_id_tag)


def build_tar(path: str, output: str):
    desc = load_py_desc(path)

    ctx = TarContext()
    ctx.prepare_from_descriptor(desc)

    ctx.copy_to_file(Path(output))


def print_usage():
    print("Usage: rebuildr <command> <args>")
    print("Commands:")
    print("  load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...]")
    print(
        "  load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...] bazel-stable-metadata <stable-metadata-file> <stable-image-tag-file>"
    )
    print(
        "  load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...] materialize-image"
    )
    print(
        "  load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...] push-image [--only-content-id-tag] [<override-tag>] ",
    )
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

    build_args = {}
    # parse build args until first subcommand
    while len(args) > 0 and "=" in args[0]:
        key, value = args[0].split("=", 1)
        build_args[key] = value
        args = args[1:]

    # ignore empty args before first subcommand
    while len(args) > 0 and args[0] == "":
        args = args[1:]

    if len(args) == 0:
        parse_and_print_py(file_path, build_args)
        return
    if any(arg in ("-h", "--help") for arg in args):
        print_usage()
        return

    if "bazel-stable-metadata" == args[0]:
        if len(args) < 2:
            logging.error("Stable metadata files must be specified")
            return
        else:
            parse_and_write_bazel_stable_metadata(
                file_path, build_args, args[1], args[2]
            )
        return

    if "materialize-image" == args[0]:
        tags = build_docker(file_path, build_args)
        print(tags.most_specific_tag())
        return

    if "push-image" == args[0]:
        if len(args) > 1 and args[1] == "--only-content-id-tag":
            only_content_id_tag = True
            args = args[1:]
        else:
            only_content_id_tag = False

        override_tag = None
        if len(args) > 1 and args[1] != "":
            override_tag = args[1]

        tags = build_docker(file_path, build_args, fetch_if_not_local=False)

        tags_to_push = tags.tags

        if only_content_id_tag:
            tags_to_push = [tags.content_id_tag]

        specific_tag = tags.most_specific_tag()

        if override_tag is not None:
            from rebuildr.containers.util import tag_image

            tag_image(specific_tag, override_tag)
            tags_to_push = [override_tag]
            specific_tag = override_tag

        for tag in tags_to_push:
            push_image(tag, overwrite_in_registry=False)
        print(specific_tag)

        return

    if "build-tar" == args[0]:
        if len(args) < 2:
            logging.error("Tar path is required")
            return
        else:
            build_tar(file_path, args[1])
        return

    logging.error(f"Unknown command: {args[0]}")
    print_usage()


def main():
    logging.basicConfig(level=logging.DEBUG)
    parse_cli()


if __name__ == "__main__":
    main()
