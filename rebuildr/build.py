import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from rebuildr.containers.docker import docker_bin


class DockerCLIBuilder(object):
    def __init__(self, quiet: bool = False, quiet_errors: bool = False):
        self._progress = "plain"
        # TODO: this setting should not rely on global env
        self.quiet = quiet if os.getenv("DOCKER_QUIET") is None else True
        self.quiet_errors = quiet_errors

    def maybe_run_postprocess_cmd(
        self, metadata_file: str, tags: list[str], pushed, loaded
    ):
        if os.getenv("REBUILDR_POSTPROCESS_CMD") is not None:
            cmd = os.getenv("REBUILDR_POSTPROCESS_CMD")
            logging.info(f"Running postprocess command: {cmd}")
            env = os.environ.copy()
            env["REBUILDR_BUILDX_METADATA_FILE"] = metadata_file
            tags_str = " ".join(tags)
            env["REBUILDR_BUILDX_TAGS"] = tags_str
            env["REBUILDR_BUILDX_TAGS_PUSHED"] = tags_str if pushed else ""
            env["REBUILDR_BUILDX_TAGS_LOADED"] = tags_str if loaded else ""

            p = subprocess.Popen(cmd, env=env, shell=True)
            if p.wait() != 0:
                raise RuntimeError(
                    f"Postprocess command failed: {cmd} with exit code {p.wait()}"
                )

    def build(
        self,
        root_dir: Path,
        dockerfile,
        tags=[],
        nocache=False,
        pull=False,
        forcerm=False,
        buildargs=None,
        cache_from=None,
        output=None,
        platform=None,
        target=None,
        build_context=None,
        do_load=False,
        build_and_push=False,
    ):
        if dockerfile:
            if not dockerfile.is_absolute():
                dockerfile = root_dir / dockerfile
        else:
            dockerfile = root_dir / "Dockerfile"
        # sort and uniq tags
        tags = list(set(tags))
        metadata_file = tempfile.NamedTemporaryFile()

        command_builder = _CommandBuilder()
        command_builder.add_params("--build-arg", buildargs)
        command_builder.add_list("--cache-from", cache_from)
        command_builder.add_arg("--file", dockerfile)
        command_builder.add_flag("--force-rm", forcerm)
        command_builder.add_flag("--no-cache", nocache)
        command_builder.add_arg("--progress", self._progress)
        command_builder.add_flag("--pull", pull)
        # if load is true we can only build current single platform image
        if do_load and not build_and_push:
            command_builder.add_flag("--load", True)
        else:
            command_builder.add_arg("--platform", platform)
        for tag in tags:
            command_builder.add_arg("--tag", tag)
        command_builder.add_arg("--target", target)
        command_builder.add_arg("--output", output)
        command_builder.add_arg("--metadata-file", metadata_file.name)

        for context in build_context or []:
            command_builder.add_arg("--build-context", context)
        if build_and_push:
            command_builder.add_flag("--push", True)
        args = command_builder.build([root_dir])

        subprocess.run([docker_bin(), "buildx", "ls"], check=True)
        subprocess.run("export", check=True, shell=True)

        if self.quiet:
            with subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            ) as p:
                stdout, stderr = p.communicate()
                exit_code = p.wait()
                if exit_code != 0:
                    if self.quiet_errors:
                        raise RuntimeError("Builder exited with code %s", exit_code)
                    # TODO: add better error handling
                    print(f"error building image: {dockerfile}")
                    print("------- STDOUT ---------")
                    print(stdout, end="")
                    print("----------------")
                    print()
                    print("------- STDERR ---------")
                    print(stderr, end="")
                    print("----------------")
                    raise RuntimeError("Builder exited with code %s", exit_code)

        else:
            with subprocess.Popen(
                args, stdout=sys.stderr.buffer, universal_newlines=True
            ) as p:
                exit_code = p.wait()
                if exit_code != 0:
                    raise RuntimeError(f"Builder exited with code {exit_code}")
        self.maybe_run_postprocess_cmd(
            metadata_file.name, tags, build_and_push, do_load
        )

        return None


class _CommandBuilder(object):
    def __init__(self):
        self._args = ["docker", "buildx", "build"]

    def add_arg(self, name, value):
        if value:
            self._args.extend([name, str(value)])

    def add_flag(self, name, flag):
        if flag:
            self._args.extend([name])

    def add_params(self, name, params):
        if params:
            for key, val in params.items():
                self._args.extend([name, "{}={}".format(key, val)])

    def add_list(self, name, values):
        if values:
            for val in values:
                self._args.extend([name, val])

    def build(self, args):
        all_args = self._args + args
        all_args = [str(x) for x in all_args]
        logging.info("Running command: %s", " ".join(all_args))
        return all_args
