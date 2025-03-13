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
        target=None,
    ):
        if dockerfile:
            if not dockerfile.is_absolute():
                dockerfile = root_dir / dockerfile
        else:
            dockerfile = root_dir / "Dockerfile"
        fd, iidfile = tempfile.mkstemp()

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
        for tag in tags:
            command_builder.add_arg("--tag", tag)
        command_builder.add_arg("--target", target)
        command_builder.add_arg("--iidfile", str(iidfile))
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
                if p.wait() != 0:
                    print("TODO: error building image")

        with open(str(iidfile)) as f:
            line = f.readline()
            image_id = line.split(":")[1].strip()

        return image_id


class _CommandBuilder(object):
    def __init__(self):
        self._args = ["docker", "build"]

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
