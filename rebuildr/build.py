import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile


class DockerCLIBuilder(object):
    def __init__(self):
        self._progress = "auto"
        # TODO: this setting should not rely on global env
        self.quiet = False if os.getenv("DOCKER_QUIET") is None else True

    def build(
        self,
        root_dir: Path,
        dockerfile,
        tags=[],
        nocache=False,
        pull=False,
        forcerm=False,
        container_limits=None,
        buildargs=None,
        cache_from=None,
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
        fd, iidfile = tempfile.mkstemp()
        try:
            # sort and uniq tags
            tags = list(set(tags))

            command_builder = _CommandBuilder()
            command_builder.add_params("--build-arg", buildargs)
            command_builder.add_list("--cache-from", cache_from)
            command_builder.add_arg("--file", dockerfile)
            command_builder.add_flag("--force-rm", forcerm)
            command_builder.add_flag("--no-cache", nocache)
            command_builder.add_arg("--progress", self._progress)
            command_builder.add_flag("--pull", pull)
            # if load is true we can only build current single platform image
            if do_load:
                command_builder.add_flag("--load", True)
            else:
                command_builder.add_arg("--platform", platform)
            for tag in tags:
                command_builder.add_arg("--tag", tag)
            command_builder.add_arg("--target", target)
            for context in build_context or []:
                command_builder.add_arg("--build-context", context)
            command_builder.add_arg("--iidfile", str(iidfile))
            if build_and_push:
                command_builder.add_flag("--push", True)
            args = command_builder.build([root_dir])
            if self.quiet:
                with subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                ) as p:
                    stdout, stderr = p.communicate()
                    if p.wait() != 0:
                        # TODO: add better error handling
                        print(f"error building image: {dockerfile}")
                        print("------- STDOUT ---------")
                        print(stdout, end="")
                        print("----------------")
                        print()
                        print("------- STDERR ---------")
                        print(stderr, end="")
                        print("----------------")
            else:
                with subprocess.Popen(
                    args, stdout=sys.stderr.buffer, universal_newlines=True
                ) as p:
                    exit_code = p.wait()
                    if exit_code != 0:
                        raise RuntimeError(f"Builder exited with code {exit_code}")

            # try:
            #     with open(str(iidfile)) as f:
            #         line = f.readline()
            #         if not line.startswith("sha256:"):
            #             raise RuntimeError("Invalid image ID format in iidfile")
            #         image_id = line.split(":")[1].strip()
            # except (OSError, IOError) as e:
            #     raise RuntimeError(f"Failed to read iidfile {iidfile}: {e}")
            # TODO: return image_id even in remote build
            return None
        finally:
            os.close(fd)
            if os.path.exists(iidfile):
                os.unlink(iidfile)


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
